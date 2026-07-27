"""Attachment service (manual 12)."""
from sqlalchemy.orm import Session

from app.core.exceptions import not_found
from app.models.attachment import Attachment
from app.services.operation_log import log_operation


def create_attachment(db: Session, meta: dict, user_id: int, ip: str | None) -> Attachment:
    att = Attachment(**meta)
    db.add(att)
    db.commit()
    db.refresh(att)
    log_operation(db, user_id=user_id, module="attachment", action="upload",
                  business_id=att.business_id,
                  description=f"上传附件 {att.original_name}", request_ip=ip)
    db.commit()
    return att


def list_by_business(db: Session, business_type: str, business_id: int) -> list[Attachment]:
    return (
        db.query(Attachment)
        .filter(Attachment.business_type == business_type,
                Attachment.business_id == business_id,
                Attachment.is_deleted.is_(False))
        .order_by(Attachment.id.desc())
        .all()
    )


def get_for_download(db: Session, attachment_id: int) -> Attachment:
    att = db.get(Attachment, attachment_id)
    if att is None or att.is_deleted:
        raise not_found("附件不存在")
    return att


def delete_attachment(db: Session, attachment_id: int, user_id: int, ip: str | None) -> None:
    att = db.get(Attachment, attachment_id)
    if att is None:
        raise not_found("附件不存在")
    att.is_deleted = True
    db.commit()
    log_operation(db, user_id=user_id, module="attachment", action="delete",
                  business_id=att.business_id,
                  description=f"删除附件 {att.original_name}", request_ip=ip)
    db.commit()
