"""汇报中心：按时间范围汇总四台账明细（个人工作留底 / 写周月季年报）。"""
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.exceptions import ok
from app.models.user import User
from app.services.report import summarize

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/summary", response_model=dict)
def report_summary(
    start: date | None = None,
    end: date | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """返回 [start, end] 内四台账明细。start/end 缺省分别取 1970 / 今天。"""
    return ok(summarize(db, start, end))
