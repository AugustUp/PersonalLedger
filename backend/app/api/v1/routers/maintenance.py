from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import RequirePermission, get_current_user
from app.core.exceptions import ok
from app.models.user import User
from app.schemas.maintenance import (
    MaintenanceCreate, MaintenanceDetail, MaintenanceListItem, MaintenanceQuery,
    MaintenanceUpdate,
)
from app.services.maintenance import (
    EXPORT_HEADERS, create_maintenance, delete_maintenance, export_rows,
    get_maintenance_or_404, query_maintenance, restore_maintenance, update_maintenance,
)
from app.utils.export_response import build_export_response

router = APIRouter(prefix="/maintenance-records", tags=["maintenance"])


def _ip(r: Request):
    return r.client.host if r.client else None


@router.get("", response_model=dict, dependencies=[Depends(RequirePermission("maintenance:view"))])
def list_endpoint(
    q: MaintenanceQuery = Depends(),
    categories: list[str] | None = Query(None, description="按分类筛选(可多选)，用于分组导航整组筛选"),
    db: Session = Depends(get_db),
):
    if categories is not None:
        q.categories = categories
    items, total, pages = query_maintenance(db, q)
    return ok({
        "items": [MaintenanceListItem.model_validate(i).model_dump() for i in items],
        "page": q.page, "page_size": q.page_size, "total": total, "pages": pages,
    })


@router.post("", response_model=dict, dependencies=[Depends(RequirePermission("maintenance:create"))])
def create_endpoint(payload: MaintenanceCreate, request: Request,
                    db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    m = create_maintenance(db, payload, user.id, _ip(request))
    return ok(MaintenanceDetail.model_validate(m).model_dump(), message="创建成功")


@router.get("/export", response_model=dict,
            dependencies=[Depends(RequirePermission("maintenance:export"))])
def export_endpoint(q: MaintenanceQuery = Depends(), bg: BackgroundTasks = BackgroundTasks(),
                    db: Session = Depends(get_db)):
    rows = export_rows(db, q)
    return build_export_response(EXPORT_HEADERS, rows, "通用维护台账.xlsx", bg)


@router.get("/{rec_id}", response_model=dict,
            dependencies=[Depends(RequirePermission("maintenance:view"))])
def detail_endpoint(rec_id: int, db: Session = Depends(get_db)):
    m = get_maintenance_or_404(db, rec_id)
    return ok(MaintenanceDetail.model_validate(m).model_dump())


@router.patch("/{rec_id}", response_model=dict,
              dependencies=[Depends(RequirePermission("maintenance:update"))])
def update_endpoint(rec_id: int, payload: MaintenanceUpdate, request: Request,
                    db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    m = update_maintenance(db, rec_id, payload, user.id, _ip(request))
    return ok(MaintenanceDetail.model_validate(m).model_dump(), message="更新成功")


@router.delete("/{rec_id}", response_model=dict,
               dependencies=[Depends(RequirePermission("maintenance:delete"))])
def delete_endpoint(rec_id: int, request: Request, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    delete_maintenance(db, rec_id, user.id, _ip(request))
    return ok(message="已删除")


@router.post("/{rec_id}/restore", response_model=dict,
             dependencies=[Depends(RequirePermission("maintenance:delete"))])
def restore_endpoint(rec_id: int, request: Request, db: Session = Depends(get_db),
                     user: User = Depends(get_current_user)):
    m = restore_maintenance(db, rec_id, user.id, _ip(request))
    return ok(MaintenanceDetail.model_validate(m).model_dump(), message="已恢复")
