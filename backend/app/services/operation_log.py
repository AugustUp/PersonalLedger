"""Audit logging (manual 14)."""
from sqlalchemy.orm import Session

from app.models.operation_log import OperationLog


def log_operation(
    db: Session,
    *,
    user_id: int | None,
    module: str,
    action: str,
    business_id: int | None = None,
    description: str | None = None,
    request_ip: str | None = None,
) -> None:
    """Write an audit entry. Called inside the request transaction so it rolls
    back together with the business change when something fails."""
    db.add(
        OperationLog(
            user_id=user_id,
            module=module,
            action=action,
            business_id=business_id,
            description=description,
            request_ip=request_ip,
        )
    )
