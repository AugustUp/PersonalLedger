from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import RequirePermission, get_current_user
from app.core.exceptions import ok
from app.models.user import User
from app.schemas.department import DepartmentCreate, DepartmentOut, DepartmentUpdate
from app.services.department import (
    create_department,
    delete_department,
    list_departments,
    update_department,
)

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("", response_model=dict)
def list_endpoint(page: int = 1, page_size: int = 100, keyword: str | None = None,
                  db: Session = Depends(get_db),
                  _: User = Depends(get_current_user)):
    items, total, pages = list_departments(db, page, page_size, keyword)
    return ok({
        "items": [d.model_dump() for d in items],
        "page": page, "page_size": page_size, "total": total, "pages": pages,
    })


@router.post("", response_model=dict,
             dependencies=[Depends(RequirePermission("system:department_manage"))])
def create_endpoint(payload: DepartmentCreate, db: Session = Depends(get_db)):
    d = create_department(db, payload)
    db.commit()
    return ok(DepartmentOut.model_validate(d).model_dump(), message="创建成功")


@router.patch("/{dept_id}", response_model=dict,
              dependencies=[Depends(RequirePermission("system:department_manage"))])
def update_endpoint(dept_id: int, payload: DepartmentUpdate, db: Session = Depends(get_db)):
    d = update_department(db, dept_id, payload)
    db.commit()
    return ok(DepartmentOut.model_validate(d).model_dump(), message="更新成功")


@router.delete("/{dept_id}", response_model=dict,
               dependencies=[Depends(RequirePermission("system:department_manage"))])
def delete_endpoint(dept_id: int, db: Session = Depends(get_db)):
    delete_department(db, dept_id)
    db.commit()
    return ok(message="删除成功")
