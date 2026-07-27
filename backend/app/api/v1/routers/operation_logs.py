from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import RequirePermission
from app.core.exceptions import ok
from app.schemas.operation_log import OperationLogOut, OperationLogQuery
from app.utils.query import apply_sort, paginate

from app.models.operation_log import OperationLog

router = APIRouter(prefix="/operation-logs", tags=["operation-logs"])


@router.get("", response_model=dict,
           dependencies=[Depends(RequirePermission("system:log_view"))])
def list_endpoint(q: OperationLogQuery = Depends(), db: Session = Depends(get_db)):
    query = db.query(OperationLog)
    if q.module:
        query = query.filter(OperationLog.module == q.module)
    if q.action:
        query = query.filter(OperationLog.action == q.action)
    if q.user_id is not None:
        query = query.filter(OperationLog.user_id == q.user_id)
    if q.keyword:
        like = f"%{q.keyword}%"
        query = query.filter(OperationLog.description.like(like))
    if q.start_date:
        query = query.filter(OperationLog.created_at >= q.start_date)
    if q.end_date:
        query = query.filter(OperationLog.created_at <= q.end_date)
    query = apply_sort(query, OperationLog, q.sort_by, q.sort_order,
                       {"created_at": OperationLog.created_at})
    items, total, pages = paginate(query, q.page, q.page_size)
    return ok({
        "items": [OperationLogOut.model_validate(o).model_dump() for o in items],
        "page": q.page, "page_size": q.page_size, "total": total, "pages": pages,
    })
