from fastapi import APIRouter, BackgroundTasks, Depends, Request, UploadFile, File
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import RequirePermission, get_current_user
from app.core.exceptions import ok
from app.models.user import User
from app.schemas.meeting import MeetingCreate, MeetingDetail, MeetingListItem, MeetingQuery, MeetingUpdate
from app.services.meeting import (
    EXPORT_HEADERS, create_meeting, delete_meeting, export_rows,
    get_meeting_or_404, query_meetings, restore_meeting, update_meeting,
)
from app.utils.export_response import build_export_response

router = APIRouter(prefix="/meetings", tags=["meetings"])


def _ip(r: Request):
    return r.client.host if r.client else None


@router.get("", response_model=dict, dependencies=[Depends(RequirePermission("meeting:view"))])
def list_endpoint(q: MeetingQuery = Depends(), db: Session = Depends(get_db)):
    items, total, pages = query_meetings(db, q)
    return ok({
        "items": [MeetingListItem.model_validate(m).model_dump() for m in items],
        "page": q.page, "page_size": q.page_size, "total": total, "pages": pages,
    })


@router.post("", response_model=dict, dependencies=[Depends(RequirePermission("meeting:create"))])
def create_endpoint(payload: MeetingCreate, request: Request,
                    db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    m = create_meeting(db, payload, user.id, _ip(request))
    return ok(MeetingDetail.model_validate(m).model_dump(), message="创建成功")


@router.get("/export", response_model=dict,
            dependencies=[Depends(RequirePermission("meeting:export"))])
def export_endpoint(q: MeetingQuery = Depends(), bg: BackgroundTasks = BackgroundTasks(),
                    db: Session = Depends(get_db)):
    rows = export_rows(db, q)
    return build_export_response(
        EXPORT_HEADERS, rows, f"会议调试台账_{q.start_date or ''}.xlsx", bg,
    )


@router.get("/{meeting_id}", response_model=dict,
            dependencies=[Depends(RequirePermission("meeting:view"))])
def detail_endpoint(meeting_id: int, db: Session = Depends(get_db)):
    m = get_meeting_or_404(db, meeting_id)
    return ok(MeetingDetail.model_validate(m).model_dump())


@router.patch("/{meeting_id}", response_model=dict,
              dependencies=[Depends(RequirePermission("meeting:update"))])
def update_endpoint(meeting_id: int, payload: MeetingUpdate, request: Request,
                    db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    m = update_meeting(db, meeting_id, payload, user.id, _ip(request))
    return ok(MeetingDetail.model_validate(m).model_dump(), message="更新成功")


@router.delete("/{meeting_id}", response_model=dict,
               dependencies=[Depends(RequirePermission("meeting:delete"))])
def delete_endpoint(meeting_id: int, request: Request, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    delete_meeting(db, meeting_id, user.id, _ip(request))
    return ok(message="已删除")


@router.post("/{meeting_id}/restore", response_model=dict,
             dependencies=[Depends(RequirePermission("meeting:delete"))])
def restore_endpoint(meeting_id: int, request: Request, db: Session = Depends(get_db),
                     user: User = Depends(get_current_user)):
    m = restore_meeting(db, meeting_id, user.id, _ip(request))
    return ok(MeetingDetail.model_validate(m).model_dump(), message="已恢复")
