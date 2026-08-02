import os

from fastapi import APIRouter, Depends, Form, Request, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.exceptions import forbidden, not_found, ok
from app.core.security import has_permission
from app.models.attachment import Attachment
from app.models.user import User
from app.schemas.attachment import AttachmentOut
from app.services.attachment import (
    create_attachment, delete_attachment, get_for_download, list_by_business,
)
from app.utils.file import save_upload

router = APIRouter(prefix="/attachments", tags=["attachments"])

# business_type -> required permission to upload/download
_BIZ_PERM = {
    "meetings": "meeting:view",
    "network-assets": "network_asset:view",
    "account-batches": "account_batch:view",
    "maintenance": "maintenance:view",
}


def _check_biz_perm(user: User, business_type: str):
    """business_type 必须在白名单内（防路径穿越/任意目录写入），再校验业务权限。"""
    perm = _BIZ_PERM.get(business_type)
    if perm is None:
        raise forbidden("不支持的附件业务类型")
    if not has_permission(user, perm):
        raise forbidden("无权限访问该业务的附件")


@router.get("", response_model=dict)
def list_endpoint(business_type: str, business_id: int,
                  db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _check_biz_perm(user, business_type)
    items = list_by_business(db, business_type, business_id)
    return ok([AttachmentOut.model_validate(a).model_dump() for a in items])


@router.post("", response_model=dict)
async def upload_endpoint(business_type: str = Form(...), business_id: int = Form(...),
                         file: UploadFile = File(...), request: Request = None,
                         db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _check_biz_perm(user, business_type)
    ip = request.client.host if request and request.client else None
    meta = await save_upload(file, business_type, business_id)
    meta["uploaded_by"] = user.id
    att = create_attachment(db, meta, user.id, ip)
    return ok(AttachmentOut.model_validate(att).model_dump(), message="上传成功")


@router.get("/{attachment_id}/download")
def download_endpoint(attachment_id: int, db: Session = Depends(get_db),
                     user: User = Depends(get_current_user)):
    att = get_for_download(db, attachment_id)
    _check_biz_perm(user, att.business_type)
    abs_path = os.path.join(settings.upload_dir, att.file_path)
    if not os.path.exists(abs_path):
        raise not_found("文件不存在")
    return FileResponse(abs_path, filename=att.original_name,
                        media_type=att.mime_type or "application/octet-stream")


@router.delete("/{attachment_id}", response_model=dict)
def delete_endpoint(attachment_id: int, request: Request = None,
                   db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    att = db.get(Attachment, attachment_id)
    if att is None:
        raise not_found("附件不存在")
    _check_biz_perm(user, att.business_type)
    ip = request.client.host if request and request.client else None
    delete_attachment(db, attachment_id, user.id, ip)
    return ok(message="已删除")
