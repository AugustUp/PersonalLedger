#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Live smoke test for ops-ledger.

Runs against a running backend (default http://127.0.0.1:8000) and verifies
auth, RBAC, the four ledgers (CRUD / filter / export), import pipelines,
attachments, dashboard and operation logs. Exits non-zero if anything fails.
"""
import io
import sys

import httpx
import openpyxl

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
PASSED, FAILED = 0, 0
FAILURES = []


def check(name: str, ok: bool, detail: str = ""):
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  [PASS] {name}")
    else:
        FAILED += 1
        FAILURES.append(f"{name}: {detail}")
        print(f"  [FAIL] {name} -- {detail}")


def main():
    c = httpx.Client(base_url=BASE, timeout=20)

    # ---- meta ----
    r = c.get("/health")
    check("GET /health", r.status_code == 200 and r.json().get("code") == 0, r.text)

    # ---- auth: unauthorized ----
    r = c.get("/api/v1/auth/me")
    check("未带 token 访问 /auth/me 返回 401", r.status_code in (401, 403), f"status={r.status_code}")

    # ---- auth: login ----
    r = c.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    check("admin 登录", r.status_code == 200 and "access_token" in r.json().get("data", {}), r.text)
    token = r.json()["data"]["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    r = c.get("/api/v1/auth/me", headers=h)
    me = r.json().get("data", {})
    check("GET /auth/me", r.status_code == 200 and me.get("role") == "admin", r.text)

    # ---- departments CRUD ----
    r = c.post("/api/v1/departments", json={"name": "冒烟测试科"}, headers=h)
    dep = r.json().get("data", {})
    check("POST /departments 创建", r.status_code == 200 and dep.get("id"), r.text)
    r = c.get("/api/v1/departments", headers=h)
    check("GET /departments 列表", r.status_code == 200 and r.json()["data"]["total"] >= 1, r.text)
    if dep.get("id"):
        r = c.patch(f"/api/v1/departments/{dep['id']}", json={"name": "冒烟测试科-改名"}, headers=h)
        check("PATCH /departments 改名", r.status_code == 200 and r.json()["data"]["name"] == "冒烟测试科-改名", r.text)
        r = c.delete(f"/api/v1/departments/{dep['id']}", headers=h)
        check("DELETE /departments 删除", r.status_code == 200, r.text)

    # ---- meetings CRUD + filter + export ----
    payload = {"meeting_name": "冒烟测试会议", "location": "主楼101", "contact_name": "张三",
               "technicians": "李四", "status": "pending", "onsite_support": True}
    r = c.post("/api/v1/meetings", json=payload, headers=h)
    mtg = r.json().get("data", {})
    check("POST /meetings 创建", r.status_code == 200 and str(mtg.get("record_no", "")).startswith("MTG-"), r.text)
    mid = mtg.get("id")
    r = c.get("/api/v1/meetings", params={"keyword": "冒烟测试"}, headers=h)
    check("GET /meetings 关键词过滤", r.status_code == 200 and r.json()["data"]["total"] >= 1, r.text)
    r = c.get("/api/v1/meetings", params={"status": "pending", "page_size": 5}, headers=h)
    check("GET /meetings 状态过滤+分页", r.status_code == 200 and r.json()["data"]["items"], r.text)
    if mid:
        r = c.patch(f"/api/v1/meetings/{mid}", json={"status": "completed"}, headers=h)
        check("PATCH /meetings 状态更新", r.status_code == 200 and r.json()["data"]["status"] == "completed", r.text)
        r = c.get(f"/api/v1/meetings/{mid}", headers=h)
        check("GET /meetings/:id 详情", r.status_code == 200 and r.json()["data"]["id"] == mid, r.text)
    r = c.get("/api/v1/meetings/export", headers=h)
    check("GET /meetings/export 导出 xlsx", r.status_code == 200 and r.content[:2] == b"PK", f"status={r.status_code}")

    # ---- network assets CRUD + conflict + history + import + export ----
    r = c.post("/api/v1/network-assets", json={
        "ip_address": "10.99.0.1", "mac_address": "aa:bb:cc:00:11:22", "user_name": "王五",
        "device_name": "测试终端", "status": "active"}, headers=h)
    ast = r.json().get("data", {})
    check("POST /network-assets 创建+MAC归一化",
          r.status_code == 200 and ast.get("mac_address") == "AA:BB:CC:00:11:22", r.text)
    aid = ast.get("id")
    if aid:
        r = c.patch(f"/api/v1/network-assets/{aid}", json={"user_name": "赵六", "change_reason": "冒烟测试变更"}, headers=h)
        check("PATCH /network-assets 更新(带原因)", r.status_code == 200, r.text)
        r = c.get(f"/api/v1/network-assets/{aid}/histories", headers=h)
        hs = r.json().get("data", [])
        check("GET /network-assets/:id/histories 变更历史", r.status_code == 200 and any(x.get("field_name") == "user_name" for x in hs), r.text)
    # MAC conflict
    r = c.post("/api/v1/network-assets", json={"ip_address": "10.99.0.2", "mac_address": "AA:BB:CC:00:11:22",
                                               "status": "active", "change_reason": "x"}, headers=h)
    check("MAC 冲突被拒绝(409)", r.status_code == 409, f"status={r.status_code}")
    r = c.get("/api/v1/network-assets", params={"keyword": "测试终端"}, headers=h)
    check("GET /network-assets 过滤", r.status_code == 200 and r.json()["data"]["total"] >= 1, r.text)
    r = c.get("/api/v1/network-assets/export", headers=h)
    check("GET /network-assets/export 导出 xlsx", r.status_code == 200 and r.content[:2] == b"PK", f"status={r.status_code}")
    # import preview + commit
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["IP地址", "MAC地址", "使用人", "设备名称", "设备类型", "楼宇", "房间", "状态"])
    ws.append(["10.99.0.10", "AA:BB:CC:00:00:10", "冒烟导入1", "PC-1", "台式机", "1号楼", "101", "active"])
    ws.append(["10.99.0.11", "AA:BB:CC:00:00:11", "冒烟导入2", "PC-2", "笔记本", "1号楼", "102", "active"])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    files = {"file": ("assets.xlsx", buf.getvalue(),
                      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    r = c.post("/api/v1/network-assets/import/preview", files=files, headers=h)
    prev = r.json().get("data", {})
    check("POST /network-assets/import/preview 预览", r.status_code == 200 and prev.get("valid_rows") == 2, r.text)
    if prev.get("import_token"):
        r = c.post("/api/v1/network-assets/import/commit",
                   json={"import_token": prev["import_token"], "strategy": "skip"}, headers=h)
        check("POST /network-assets/import/commit 提交", r.status_code == 200 and r.json()["data"].get("inserted") == 2, r.text)

    # ---- account batches CRUD + items import + stats + export ----
    r = c.post("/api/v1/account-batches", json={"batch_name": "冒烟测试批次", "account_type": "校园网",
                                                "applicant": "钱七", "applicant_department": "信息科"}, headers=h)
    bat = r.json().get("data", {})
    check("POST /account-batches 创建", r.status_code == 200 and str(bat.get("batch_no", "")).startswith("ACC-"), r.text)
    bid = bat.get("id")
    if bid:
        wb2 = openpyxl.Workbook()
        ws2 = wb2.active
        ws2.append(["姓名", "工号或学号", "部门", "账号名称", "账号类型", "权限类型", "有效期", "开通结果", "失败原因"])
        ws2.append(["孙八", "20260001", "信息科", "sunba", "校园网", "普通", "2026-12-31", "success", ""])
        ws2.append(["周九", "20260002", "信息科", "zhoujiu", "VPN", "普通", "2026-12-31", "pending", ""])
        buf2 = io.BytesIO()
        wb2.save(buf2)
        buf2.seek(0)
        files2 = {"file": ("items.xlsx", buf2.getvalue(),
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        r = c.post(f"/api/v1/account-batches/{bid}/items/import/preview", files=files2, headers=h)
        prev2 = r.json().get("data", {})
        check("POST account-batches/:id/items/import/preview", r.status_code == 200 and prev2.get("valid_rows") == 2, r.text)
        if prev2.get("import_token"):
            r = c.post(f"/api/v1/account-batches/{bid}/items/import/commit",
                       json={"import_token": prev2["import_token"], "strategy": "skip"}, headers=h)
            check("POST items/import/commit", r.status_code == 200 and r.json()["data"].get("inserted") == 2, r.text)
        r = c.get(f"/api/v1/account-batches/{bid}/items", headers=h)
        items = r.json().get("data", {})
        check("GET :id/items 明细列表", r.status_code == 200 and items.get("total") == 2, r.text)
        r = c.get(f"/api/v1/account-batches/{bid}", headers=h)
        check("GET :id 批次统计", r.status_code == 200 and r.json()["data"].get("total_count") == 2, r.text)
        if items.get("items"):
            iid = items["items"][0]["id"]
            r = c.patch(f"/api/v1/account-batches/{bid}/items/batch",
                        json={"items": [{"id": iid, "result": "success"}]}, headers=h)
            check("PATCH :id/items/batch 批量更新结果", r.status_code == 200, r.text)
        for which in ("all", "success", "pending"):
            r = c.get(f"/api/v1/account-batches/{bid}/export", params={"which": which}, headers=h)
            check(f"GET :id/export?which={which}", r.status_code == 200 and r.content[:2] == b"PK", f"status={r.status_code}")

    # ---- maintenance CRUD + category filter + quick status + export ----
    r = c.post("/api/v1/maintenance-records", json={
        "category": "网络维护", "related_system": "NCE-Campus", "requester": "吴十",
        "location": "3号楼", "problem_description": "无法上网（冒烟测试）", "status": "pending",
        "handler": "郑一"}, headers=h)
    mtn = r.json().get("data", {})
    check("POST /maintenance-records 创建", r.status_code == 200 and str(mtn.get("record_no", "")).startswith("OPS-"), r.text)
    mid2 = mtn.get("id")

    # 自由填写部门：自动创建 + 同名复用
    r = c.post("/api/v1/maintenance-records", json={
        "category": "OA", "requester": "自由部门测试", "department_name": "自由部门A",
        "problem_description": "部门自由填写测试", "status": "pending"}, headers=h)
    check("POST maintenance 自由填写部门(自动创建)",
          r.status_code == 200 and r.json()["data"].get("department_name") == "自由部门A", r.text)
    r = c.post("/api/v1/maintenance-records", json={
        "category": "邮箱", "requester": "自由部门测试2", "department_name": "自由部门A",
        "problem_description": "部门复用测试", "status": "pending"}, headers=h)
    check("POST maintenance 同名部门不重复创建",
          r.status_code == 200 and r.json()["data"].get("department_name") == "自由部门A", r.text)
    r = c.get("/api/v1/departments", params={"keyword": "自由部门A"}, headers=h)
    check("自由部门A 仅创建 1 个", r.status_code == 200 and r.json()["data"]["total"] == 1, r.text)

    r = c.get("/api/v1/maintenance-records", params={"categories": ["网络维护"]}, headers=h)
    check("GET maintenance 分类过滤(categories=网络维护)", r.status_code == 200 and r.json()["data"]["total"] >= 1, r.text)
    r = c.get("/api/v1/maintenance-records", params={"categories": ["OA", "邮箱"]}, headers=h)
    check("GET maintenance 多分类过滤(OA+邮箱)", r.status_code == 200, r.text)
    r = c.get("/api/v1/maintenance-records", params={"related_system": "NCE-Campus"}, headers=h)
    check("GET maintenance 关联系统过滤", r.status_code == 200 and r.json()["data"]["total"] >= 1, r.text)
    if mid2:
        # simulate quick status flow used by the list page
        r = c.patch(f"/api/v1/maintenance-records/{mid2}", json={"status": "processing"}, headers=h)
        check("PATCH maintenance 状态流转 pending->processing", r.status_code == 200 and r.json()["data"]["status"] == "processing", r.text)
        r = c.patch(f"/api/v1/maintenance-records/{mid2}", json={"status": "resolved"}, headers=h)
        check("PATCH maintenance 状态流转 processing->resolved", r.status_code == 200 and r.json()["data"]["status"] == "resolved", r.text)
        r = c.get(f"/api/v1/maintenance-records/{mid2}", headers=h)
        check("GET maintenance/:id 详情", r.status_code == 200 and r.json()["data"]["id"] == mid2, r.text)
    r = c.get("/api/v1/maintenance-records/export", headers=h)
    check("GET /maintenance-records/export 导出 xlsx", r.status_code == 200 and r.content[:2] == b"PK", f"status={r.status_code}")

    # ---- attachments (business_type/business_id are multipart FORM fields) ----
    files3 = {"file": ("note.txt", b"smoke attachment content", "text/plain")}
    r = c.post("/api/v1/attachments",
               data={"business_type": "meetings", "business_id": str(mid or 1)},
               files=files3, headers=h)
    att = r.json().get("data", {})
    check("POST /attachments 上传", r.status_code == 200 and att.get("id"), r.text)
    if att.get("id"):
        r = c.get("/api/v1/attachments", params={"business_type": "meetings", "business_id": mid or 1}, headers=h)
        check("GET /attachments 列表", r.status_code == 200 and any(x["id"] == att["id"] for x in r.json()["data"]), r.text)
        r = c.delete(f"/api/v1/attachments/{att['id']}", headers=h)
        check("DELETE /attachments 删除", r.status_code == 200, r.text)

    # ---- dashboard ----
    r = c.get("/api/v1/dashboard/summary", headers=h)
    dash = r.json().get("data", {})
    check("GET /dashboard/summary",
          r.status_code == 200 and dash.get("meeting_total", 0) >= 1 and "maintenance_by_category" in dash, r.text)

    # ---- operation logs ----
    r = c.get("/api/v1/operation-logs", headers=h)
    check("GET /operation-logs", r.status_code == 200 and r.json()["data"]["total"] >= 1, r.text)

    # ---- users + RBAC ----
    r = c.get("/api/v1/users", headers=h)
    check("GET /users (admin)", r.status_code == 200, r.text)
    r = c.post("/api/v1/users", json={"username": "smokeop", "password": "smoke123456",
                                      "real_name": "冒烟运维", "role": "operator"}, headers=h)
    op = r.json().get("data", {})
    check("POST /users 创建 operator", r.status_code == 200 and op.get("role") == "operator", r.text)
    uid = op.get("id")
    if uid:
        r = c.post(f"/api/v1/users/{uid}/reset-password", json={"new_password": "smoke654321"}, headers=h)
        check("POST /users/:id/reset-password", r.status_code == 200, r.text)

    # ---- 部门删除引用保护 ----
    r = c.post("/api/v1/departments", json={"name": "被引用部门"}, headers=h)
    dep2 = r.json().get("data", {})
    if dep2.get("id"):
        r = c.post("/api/v1/users", json={"username": "depuser", "password": "smoke123456",
                                          "real_name": "部门用户", "role": "operator",
                                          "department_id": dep2["id"]}, headers=h)
        check("POST /users 关联部门创建", r.status_code == 200, r.text)
        r = c.delete(f"/api/v1/departments/{dep2['id']}", headers=h)
        check("有用户引用的部门删除被拒(409)", r.status_code == 409, f"status={r.status_code}")

    # ---- 数据备份（system:backup_manage，仅 admin）----
    r = c.post("/api/v1/system/backup", headers=h)
    bk = r.json().get("data", {})
    check("POST /system/backup 创建备份", r.status_code == 200 and bk.get("filename"), r.text)
    r = c.get("/api/v1/system/backup", headers=h)
    check("GET /system/backup 列表", r.status_code == 200 and len(r.json().get("data", [])) >= 1, r.text)

    # ---- 台账定制（system:config_manage，仅 admin 可写）----
    r = c.get("/api/v1/customization/config", headers=h)
    cfg = r.json().get("data", {})
    check("GET /customization/config 默认配置",
          r.status_code == 200 and cfg.get("ledger_names", {}).get("meetings") == "会议调试台账"
          and len(cfg.get("maintenance_categories", [])) == 4 and "field_meta" in cfg, r.text)
    r = c.put("/api/v1/customization/config", headers=h, json={
        "ledger_names": {"meetings": "会务保障台账"},
        "maintenance_categories": [
            {"label": "账号类", "options": ["OA", "邮箱"]},
            {"label": "服务器类", "options": ["服务器维护", "数据库维护"]},
        ],
    })
    d = r.json().get("data", {})
    check("PUT /customization/config 修改名称+分类",
          r.status_code == 200 and d.get("ledger_names", {}).get("meetings") == "会务保障台账"
          and len(d.get("maintenance_categories", [])) == 2, r.text)
    r = c.get("/api/v1/customization/config", headers=h)
    d2 = r.json().get("data", {})
    check("未改部分保持默认（field_meta 仍在）", "field_meta" in d2 and "meetings" in d2.get("field_meta", {}), r.text)
    r = c.put("/api/v1/customization/config", headers=h,
              json={"maintenance_categories": [{"label": "A", "options": ["X", "X"]}]})
    check("分类重名被拒(400)", r.status_code == 400, f"status={r.status_code}")

    # ---- 登录失败锁定（连续 5 次失败后第 6 次应 429）----
    lock_codes = []
    for _ in range(6):
        rr = c.post("/api/v1/auth/login", json={"username": "locktest", "password": "wrong-pass"})
        lock_codes.append(rr.status_code)
    check("连续失败 5 次后第 6 次登录被锁定(429)", lock_codes[-1] == 429, f"codes={lock_codes}")
    r = c.post("/api/v1/auth/login", json={"username": "smokeop", "password": "smoke654321"})
    check("未锁定用户仍可正常登录", r.status_code == 200, f"status={r.status_code}")
    op_token = r.json()["data"]["access_token"]
    oh = {"Authorization": f"Bearer {op_token}"}
    r = c.get("/api/v1/users", headers=oh)
    check("operator 访问用户管理被拒(403)", r.status_code == 403, f"status={r.status_code}")
    r = c.get("/api/v1/meetings", headers=oh)
    check("operator 可访问会议列表(200)", r.status_code == 200, f"status={r.status_code}")
    r = c.get("/api/v1/meetings/export", headers=oh)
    check("operator 导出会议被拒(403)", r.status_code == 403, f"status={r.status_code}")
    r = c.post("/api/v1/users", json={"username": "smokeop2", "password": "smoke123456",
                                      "real_name": "越权用户", "role": "operator"}, headers=oh)
    check("operator 创建用户被拒(403)", r.status_code == 403, f"status={r.status_code}")
    r = c.get("/api/v1/operation-logs", headers=oh)
    check("operator 访问操作日志被拒(403)", r.status_code == 403, f"status={r.status_code}")
    r = c.post("/api/v1/system/backup", headers=oh)
    check("operator 创建备份被拒(403)", r.status_code == 403, f"status={r.status_code}")
    r = c.put("/api/v1/customization/config", headers=oh,
              json={"ledger_names": {"meetings": "越权改名"}})
    check("operator 修改定制被拒(403)", r.status_code == 403, f"status={r.status_code}")

    # ---- logout ----
    r = c.post("/api/v1/auth/logout", headers=h)
    check("POST /auth/logout", r.status_code == 200, r.text)

    # ---- summary ----
    print(f"\n==== 冒烟测试结果：{PASSED} 通过 / {FAILED} 失败 ====")
    if FAILURES:
        print("失败明细：")
        for f in FAILURES:
            print(f"  - {f}")
    sys.exit(1 if FAILED else 0)


if __name__ == "__main__":
    main()
