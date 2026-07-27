from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.exceptions import ok
from app.models.user import User
from app.schemas.dashboard import DashboardSummary
from app.services.dashboard import get_summary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=dict)
def summary(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    s = get_summary(db)
    return ok(DashboardSummary.model_validate(s).model_dump())
