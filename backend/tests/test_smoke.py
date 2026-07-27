"""End-to-end smoke test covering auth, the four ledgers, import/export,
change history, batch stats, dashboard and role-based permission denial."""
import io

import openpyxl
import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User


def _seed_admin():
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "admin").first():
            db.add(User(username="admin", password_hash=hash_password("admin123"),
                       real_name="管理员", role="admin", is_active=True))
            db.commit()
    finally:
        db.close()


def _login(client, username, password):
    r = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["data"]["access_token"]


def _build_items_xlsx():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["姓名", "工号或学号", "部门", "账号名称", "账号类型", "权限类型",
               "有效期", "开通结果", "失败原因"])
    ws.append(["张三", "20210001", "信息科", "zhangsan", "校园网", "普通",
               "2026-12-31", "success", ""])
    ws.append(["李四", "20210002", "信息科", "lisi", "VPN", "普通",
               "2026-12-31", "failed", "账号已存在"])
    ws.append(["王五", "20210003", "信息科", "wangwu", "邮箱", "普通",
               "", "pending", ""])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()


@pytest.fixture
def client():
    from app.main import app
    with TestClient(app) as c:
        _seed_admin()
        yield c


def test_full_flow(client):
    token = _login(client, "admin", "admin123")
    h = {"Authorization": f"Bearer {token}"}

    # /auth/me
    me = client.get("/api/v1/auth/me", headers=h).json()["data"]
    assert me["role"] == "admin"
    assert "system:user_manage" in me["permissions"]

    # department
    dep = client.post("/api/v1/departments", json={"name": "信息科"}, headers=h).json()["data"]
    assert dep["name"] == "信息科"

    # meeting CRUD + export
    m = client.post("/api/v1/meetings", json={"meeting_name": "月度调试会",
                     "status": "pending"}, headers=h).json()["data"]
    assert m["record_no"].startswith("MTG-")
    lst = client.get("/api/v1/meetings", headers=h).json()["data"]
    assert lst["total"] >= 1
    exp = client.get("/api/v1/meetings/export", headers=h)
    assert exp.status_code == 200 and exp.content[:2] == b"PK"

    # network asset + history
    a = client.post("/api/v1/network-assets",
                    json={"ip_address": "10.0.0.5", "mac_address": "aA:bB:CC:dd:ee:ff",
                          "user_name": "张三", "status": "active"}, headers=h).json()["data"]
    assert a["mac_address"] == "AA:BB:CC:DD:EE:FF"  # normalized
    upd = client.patch(f"/api/v1/network-assets/{a['id']}",
                       json={"user_name": "李四", "change_reason": "人员变更"}, headers=h)
    assert upd.status_code == 200
    hist = client.get(f"/api/v1/network-assets/{a['id']}/histories", headers=h).json()["data"]
    assert len(hist) >= 1 and hist[0]["field_name"] == "user_name"

    # MAC conflict should be rejected
    dup = client.post("/api/v1/network-assets",
                      json={"mac_address": "AA:BB:CC:DD:EE:FF", "status": "active",
                            "change_reason": "x"}, headers=h)
    assert dup.status_code == 409

    # account batch + item import + stats + export
    b = client.post("/api/v1/account-batches",
                    json={"batch_name": "2026级新生账号", "account_type": "校园网"},
                    headers=h).json()["data"]
    assert b["batch_no"].startswith("ACC-")
    xlsx = _build_items_xlsx()
    prev = client.post(f"/api/v1/account-batches/{b['id']}/items/import/preview",
                       files={"file": ("list.xlsx", xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                       headers=h).json()["data"]
    assert prev["valid_rows"] == 3 and prev["invalid_rows"] == 0
    commit = client.post(f"/api/v1/account-batches/{b['id']}/items/import/commit",
                         json={"import_token": prev["import_token"], "strategy": "skip"},
                         headers=h).json()["data"]
    assert commit["inserted"] == 3
    items = client.get(f"/api/v1/account-batches/{b['id']}/items", headers=h).json()["data"]
    assert items["total"] == 3
    detail = client.get(f"/api/v1/account-batches/{b['id']}", headers=h).json()["data"]
    assert detail["total_count"] == 3
    # batch update results
    first_id = items["items"][0]["id"]
    updr = client.patch(f"/api/v1/account-batches/{b['id']}/items/batch",
                        json={"items": [{"id": first_id, "result": "success"}]}, headers=h)
    assert updr.status_code == 200
    bexp = client.get(f"/api/v1/account-batches/{b['id']}/export?which=all", headers=h)
    assert bexp.status_code == 200 and bexp.content[:2] == b"PK"

    # maintenance
    mt = client.post("/api/v1/maintenance-records",
                     json={"category": "网络", "requester": "王五",
                           "problem_description": "无法上网", "status": "pending"},
                     headers=h).json()["data"]
    assert mt["record_no"].startswith("OPS-")

    # dashboard
    dash = client.get("/api/v1/dashboard/summary", headers=h).json()["data"]
    assert dash["meeting_total"] >= 1
    assert dash["account_batch_total"] >= 1

    # operation logs visible to admin
    logs = client.get("/api/v1/operation-logs", headers=h).json()["data"]
    assert logs["total"] >= 1


def test_operator_permission_denied(client):
    token = _login(client, "admin", "admin123")
    h = {"Authorization": f"Bearer {token}"}
    # create an operator
    op = client.post("/api/v1/users",
                     json={"username": "op1", "password": "op123456",
                           "real_name": "运维员", "role": "operator"},
                     headers=h).json()["data"]
    assert op["role"] == "operator"
    op_token = _login(client, "op1", "op123456")
    oh = {"Authorization": f"Bearer {op_token}"}
    # operator cannot access user management
    r = client.get("/api/v1/users", headers=oh)
    assert r.status_code == 403
    # operator can still view meetings
    r2 = client.get("/api/v1/meetings", headers=oh)
    assert r2.status_code == 200
