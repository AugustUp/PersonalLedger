import os
import tempfile
from fastapi import APIRouter, BackgroundTasks, Depends, Request, UploadFile, File
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import RequirePermission, get_current_user
from app.core.exceptions import ok
from app.core.exceptions import bad_request
from app.models.department import Department
from app.models.user import User
from app.schemas.network_asset import (
    ImportCommit, ImportPreview, NetworkAssetCreate, NetworkAssetDetail,
    NetworkAssetListItem, NetworkAssetQuery, NetworkAssetUpdate,
    NetworkAssetHistoryOut,
)
from app.services.network_asset import (
    EXPORT_HEADERS, create_asset, export_rows, get_asset_or_404, import_commit,
    import_preview, list_histories, query_assets, update_asset,
)
from app.utils.export_response import build_export_response

router = APIRouter(prefix="/network-assets", tags=["network-assets"])


def _ip(r: Request):
    return r.client.host if r.client else None


def _detail(db: Session, a) -> dict:
    """构造详情/创建/更新响应，补充部门名称（model 无该属性）。"""
    d = NetworkAssetDetail.model_validate(a).model_dump()
    d["department_name"] = db.get(Department, a.department_id).name if a.department_id else None
    return d


async def _save_temp(file: UploadFile) -> str:
    fd, path = tempfile.mkstemp(suffix=".xlsx")
    with os.fdopen(fd, "wb") as f:
        f.write(await file.read())
    return path


@router.get("", response_model=dict, dependencies=[Depends(RequirePermission("network_asset:view"))])
def list_endpoint(q: NetworkAssetQuery = Depends(), db: Session = Depends(get_db)):
    items, total, pages = query_assets(db, q)
    return ok({
        "items": [NetworkAssetListItem.model_validate(i).model_dump() for i in items],
        "page": q.page, "page_size": q.page_size, "total": total, "pages": pages,
    })


@router.post("", response_model=dict, dependencies=[Depends(RequirePermission("network_asset:create"))])
def create_endpoint(payload: NetworkAssetCreate, request: Request,
                    db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    a = create_asset(db, payload, user.id, _ip(request))
    return ok(_detail(db, a), message="创建成功")


@router.get("/export", response_model=dict,
            dependencies=[Depends(RequirePermission("network_asset:export"))])
def export_endpoint(q: NetworkAssetQuery = Depends(), bg: BackgroundTasks = BackgroundTasks(),
                    db: Session = Depends(get_db)):
    rows = export_rows(db, q)
    return build_export_response(EXPORT_HEADERS, rows, "IP_MAC台账.xlsx", bg)


@router.get("/{asset_id}", response_model=dict,
            dependencies=[Depends(RequirePermission("network_asset:view"))])
def detail_endpoint(asset_id: int, db: Session = Depends(get_db)):
    a = get_asset_or_404(db, asset_id)
    return ok(_detail(db, a))


@router.get("/{asset_id}/histories", response_model=dict,
            dependencies=[Depends(RequirePermission("network_asset:history"))])
def histories_endpoint(asset_id: int, db: Session = Depends(get_db)):
    get_asset_or_404(db, asset_id)
    hs = list_histories(db, asset_id)
    return ok([NetworkAssetHistoryOut.model_validate(h).model_dump() for h in hs])


@router.patch("/{asset_id}", response_model=dict,
              dependencies=[Depends(RequirePermission("network_asset:update"))])
def update_endpoint(asset_id: int, payload: NetworkAssetUpdate, request: Request,
                    db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    a = update_asset(db, asset_id, payload, user.id, _ip(request))
    return ok(_detail(db, a), message="更新成功")


@router.post("/import/preview", response_model=dict,
             dependencies=[Depends(RequirePermission("network_asset:import"))])
async def import_preview_endpoint(file: UploadFile = File(...),
                                  db: Session = Depends(get_db)):
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise bad_request("请上传 Excel 文件")
    path = await _save_temp(file)
    try:
        result = import_preview(db, path)
    finally:
        os.unlink(path)
    return ok(ImportPreview.model_validate(result).model_dump())


@router.post("/import/commit", response_model=dict,
             dependencies=[Depends(RequirePermission("network_asset:import"))])
def import_commit_endpoint(payload: ImportCommit, request: Request,
                           db: Session = Depends(get_db),
                           user: User = Depends(get_current_user)):
    return ok(import_commit(db, payload.import_token, payload.strategy, user.id, _ip(request)))
