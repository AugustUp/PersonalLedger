import os
import tempfile
from fastapi import APIRouter, BackgroundTasks, Depends, Request, UploadFile, File
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import RequirePermission, get_current_user
from app.core.exceptions import ok
from app.core.exceptions import bad_request
from app.models.user import User
from app.schemas.account_batch import (
    AccountBatchCreate, AccountBatchDetail, AccountBatchItemOut,
    AccountBatchItemQuery, AccountBatchListItem, AccountBatchQuery,
    AccountBatchUpdate, BatchItemResultBatchUpdate, ImportCommit,
)
from app.services.account_batch import (
    EXPORT_HEADERS, batch_update_results, create_batch, delete_batch,
    export_rows, get_batch_or_404, import_commit, import_preview,
    query_batches, query_items, update_batch,
)
from app.utils.export_response import build_export_response

router = APIRouter(prefix="/account-batches", tags=["account-batches"])


def _ip(r: Request):
    return r.client.host if r.client else None


async def _save_temp(file: UploadFile) -> str:
    fd, path = tempfile.mkstemp(suffix=".xlsx")
    with os.fdopen(fd, "wb") as f:
        f.write(await file.read())
    return path


@router.get("", response_model=dict, dependencies=[Depends(RequirePermission("account_batch:view"))])
def list_endpoint(q: AccountBatchQuery = Depends(), db: Session = Depends(get_db)):
    items, total, pages = query_batches(db, q)
    return ok({
        "items": [AccountBatchListItem.model_validate(b).model_dump() for b in items],
        "page": q.page, "page_size": q.page_size, "total": total, "pages": pages,
    })


@router.post("", response_model=dict, dependencies=[Depends(RequirePermission("account_batch:create"))])
def create_endpoint(payload: AccountBatchCreate, request: Request,
                    db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    b = create_batch(db, payload, user.id, _ip(request))
    return ok(AccountBatchDetail.model_validate(b).model_dump(), message="创建成功")


@router.get("/export-template", response_model=dict,
            dependencies=[Depends(RequirePermission("account_batch:import"))])
def template_endpoint(bg: BackgroundTasks = BackgroundTasks(), db: Session = Depends(get_db)):
    # empty export with headers only serves as a downloadable template
    return build_export_response(EXPORT_HEADERS, [], "账号导入模板.xlsx", bg)


@router.get("/{batch_id}", response_model=dict,
            dependencies=[Depends(RequirePermission("account_batch:view"))])
def detail_endpoint(batch_id: int, db: Session = Depends(get_db)):
    b = get_batch_or_404(db, batch_id)
    return ok(AccountBatchDetail.model_validate(b).model_dump())


@router.patch("/{batch_id}", response_model=dict,
              dependencies=[Depends(RequirePermission("account_batch:update"))])
def update_endpoint(batch_id: int, payload: AccountBatchUpdate, request: Request,
                    db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    b = update_batch(db, batch_id, payload, user.id, _ip(request))
    return ok(AccountBatchDetail.model_validate(b).model_dump(), message="更新成功")


@router.delete("/{batch_id}", response_model=dict,
               dependencies=[Depends(RequirePermission("account_batch:delete"))])
def delete_endpoint(batch_id: int, request: Request, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    delete_batch(db, batch_id, user.id, _ip(request))
    return ok(message="已作废")


@router.get("/{batch_id}/items", response_model=dict,
            dependencies=[Depends(RequirePermission("account_batch:view"))])
def items_endpoint(batch_id: int, q: AccountBatchItemQuery = Depends(),
                   db: Session = Depends(get_db)):
    items, total, pages = query_items(db, batch_id, q)
    return ok({
        "items": [AccountBatchItemOut.model_validate(i).model_dump() for i in items],
        "page": q.page, "page_size": q.page_size, "total": total, "pages": pages,
    })


@router.post("/{batch_id}/items/import/preview", response_model=dict,
             dependencies=[Depends(RequirePermission("account_batch:import"))])
async def import_preview_endpoint(batch_id: int, file: UploadFile = File(...),
                                  db: Session = Depends(get_db)):
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise bad_request("请上传 Excel 文件")
    path = await _save_temp(file)
    try:
        result = import_preview(db, batch_id, path)
    finally:
        os.unlink(path)
    return ok(result)


@router.post("/{batch_id}/items/import/commit", response_model=dict,
             dependencies=[Depends(RequirePermission("account_batch:import"))])
def import_commit_endpoint(batch_id: int, payload: ImportCommit, request: Request,
                           db: Session = Depends(get_db),
                           user: User = Depends(get_current_user)):
    return ok(import_commit(db, batch_id, payload.import_token, user.id, _ip(request)))


@router.patch("/{batch_id}/items/batch", response_model=dict,
              dependencies=[Depends(RequirePermission("account_batch:update"))])
def batch_result_endpoint(batch_id: int, payload: BatchItemResultBatchUpdate,
                          request: Request, db: Session = Depends(get_db),
                          user: User = Depends(get_current_user)):
    return ok(batch_update_results(db, batch_id, payload.items, user.id, _ip(request)))


@router.get("/{batch_id}/export", response_model=dict,
            dependencies=[Depends(RequirePermission("account_batch:export"))])
def export_endpoint(batch_id: int, which: str = "all",
                    bg: BackgroundTasks = BackgroundTasks(), db: Session = Depends(get_db)):
    if which not in ("all", "success", "failed", "pending"):
        which = "all"
    rows = export_rows(db, batch_id, which)
    return build_export_response(EXPORT_HEADERS, rows, f"账号名单_{which}.xlsx", bg)
