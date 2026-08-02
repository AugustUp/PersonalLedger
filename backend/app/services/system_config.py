"""台账定制服务：模块名称 / 维护分类 / 字段标签。

存储于 system_configs 表（key="ledger_customization"，JSON）。
缺省时返回内置默认值，保证未配置/未拉取时系统行为不变（向后兼容）。
"""
import json

from sqlalchemy.orm import Session

from app.core.exceptions import bad_request
from app.models.system_config import SystemConfig

CONFIG_KEY = "ledger_customization"

# 内置默认配置（与 types.ts / 前端默认保持一致）
DEFAULT_CONFIG: dict = {
    "ledger_names": {
        "meetings": "会议调试台账",
        "network_assets": "IP/MAC 台账",
        "account_batches": "批量账号台账",
        "maintenance": "通用维护台账",
    },
    "maintenance_categories": [
        {"label": "账号类", "options": ["OA", "邮箱"]},
        {"label": "终端类", "options": ["终端正版化", "终端安全软件"]},
        {"label": "网络类", "options": ["网络维护", "WIFI", "告警维护", "封禁IP"]},
        {"label": "无线类", "options": ["ncecampus无线", "深澜无线", "AC维护AP"]},
    ],
    "field_meta": {
        "meetings": {
            "meeting_name": {"label": "会议名称"}, "meeting_time": {"label": "会议时间"},
            "location": {"label": "地点"}, "contact_name": {"label": "联系人"},
            "contact_phone": {"label": "联系电话"}, "technicians": {"label": "调试人员"},
            "equipment": {"label": "设备"}, "debug_content": {"label": "调试内容"},
            "problem_description": {"label": "问题"}, "handling_process": {"label": "处理过程"},
            "result": {"label": "结果"}, "onsite_support": {"label": "现场保障"},
            "status": {"label": "状态"}, "remark": {"label": "备注"},
        },
        "network_assets": {
            "ip_address": {"label": "IP 地址"}, "mac_address": {"label": "MAC 地址"},
            "user_name": {"label": "使用人"}, "department": {"label": "部门"},
            "device_name": {"label": "设备名称"}, "device_type": {"label": "设备类型"},
            "building": {"label": "楼宇"}, "room": {"label": "房间"},
            "vlan": {"label": "VLAN"}, "switch_name": {"label": "交换机"},
            "switch_port": {"label": "端口"}, "account_name": {"label": "账号名称"},
            "registered_at": {"label": "登记日期"}, "status": {"label": "状态"},
            "remark": {"label": "备注"},
        },
        "account_batches": {
            "batch_name": {"label": "批次名称"}, "account_type": {"label": "账号类型"},
            "applicant_department": {"label": "申请部门"}, "applicant": {"label": "申请人"},
            "application_date": {"label": "申请日期"}, "handler": {"label": "经办人"},
            "status": {"label": "状态"}, "remark": {"label": "备注"},
        },
        "maintenance": {
            "category": {"label": "分类"}, "related_system": {"label": "关联系统/设备"},
            "requester": {"label": "报修人"}, "department": {"label": "部门"},
            "contact_phone": {"label": "联系电话"}, "location": {"label": "地点"},
            "problem_description": {"label": "问题描述"}, "handling_process": {"label": "处理过程"},
            "fault_cause": {"label": "故障原因"}, "result": {"label": "处理结果"},
            "status": {"label": "状态"}, "handler": {"label": "经办人"},
            "started_at": {"label": "开始时间"}, "finished_at": {"label": "结束时间"},
            "remark": {"label": "备注"},
        },
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    """浅层配置合并：只取定制者提供的键，缺省回退 base。"""
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def get_full_config(db: Session) -> dict:
    row = db.query(SystemConfig).filter(SystemConfig.key == CONFIG_KEY).first()
    if row is None:
        return json.loads(json.dumps(DEFAULT_CONFIG))  # deep copy
    try:
        stored = json.loads(row.value_json)
    except (json.JSONDecodeError, TypeError):
        stored = {}
    return _deep_merge(json.loads(json.dumps(DEFAULT_CONFIG)), stored)


def _validate(payload: dict) -> None:
    names = payload.get("ledger_names")
    if names is not None:
        if not isinstance(names, dict):
            raise bad_request("ledger_names 格式错误")
        for k, v in names.items():
            if not isinstance(v, str) or not v.strip():
                raise bad_request("台账名称不能为空")

    cats = payload.get("maintenance_categories")
    if cats is not None:
        if not isinstance(cats, list) or len(cats) > 12:
            raise bad_request("分类分组数量不合法（1-12 组）")
        seen = set()
        for g in cats:
            if not isinstance(g, dict) or not str(g.get("label", "")).strip():
                raise bad_request("分组名称不能为空")
            opts = g.get("options", [])
            if not isinstance(opts, list) or not opts:
                raise bad_request(f"分组「{g.get('label')}」至少要有一个分类")
            for c in opts:
                if not isinstance(c, str) or not c.strip():
                    raise bad_request("分类名称不能为空")
                if c in seen:
                    raise bad_request(f"分类「{c}」重复")
                seen.add(c)

    meta = payload.get("field_meta")
    if meta is not None:
        if not isinstance(meta, dict):
            raise bad_request("field_meta 格式错误")
        for module, fields in meta.items():
            if not isinstance(fields, dict):
                raise bad_request("字段配置格式错误")
            for key, item in fields.items():
                if not isinstance(item, dict) or "label" not in item or not str(item.get("label", "")).strip():
                    raise bad_request(f"字段 {module}.{key} 缺少有效 label")


def update_config(db: Session, payload: dict, operator_id: int, ip: str | None) -> dict:
    _validate(payload)
    merged = _deep_merge(get_full_config(db), payload)
    row = db.query(SystemConfig).filter(SystemConfig.key == CONFIG_KEY).first()
    if row is None:
        row = SystemConfig(key=CONFIG_KEY, value_json=json.dumps(merged, ensure_ascii=False))
        db.add(row)
    else:
        row.value_json = json.dumps(merged, ensure_ascii=False)
    db.commit()
    from app.services.operation_log import log_operation

    log_operation(db, user_id=operator_id, module="system", action="update_config",
                  description="更新台账定制配置", request_ip=ip)
    db.commit()
    return merged
