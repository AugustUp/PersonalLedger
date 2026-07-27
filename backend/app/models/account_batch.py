from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class AccountBatch(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "account_batches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_no = Column(String(30), unique=True, index=True, nullable=False)
    batch_name = Column(String(200), nullable=False)
    account_type = Column(String(50), nullable=True)
    applicant_department = Column(String(100), nullable=True)
    applicant = Column(String(100), nullable=True)
    application_date = Column(Date, nullable=True)
    total_count = Column(Integer, default=0, nullable=False)
    success_count = Column(Integer, default=0, nullable=False)
    failed_count = Column(Integer, default=0, nullable=False)
    pending_count = Column(Integer, default=0, nullable=False)
    handler = Column(String(100), nullable=True)
    status = Column(String(30), nullable=False, default="draft")
    source_file_id = Column(Integer, nullable=True)
    result_file_id = Column(Integer, nullable=True)
    remark = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)


class AccountBatchItem(Base, TimestampMixin):
    __tablename__ = "account_batch_items"
    __table_args__ = (
        UniqueConstraint("batch_id", "account_name", name="uq_batch_account"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(
        Integer, ForeignKey("account_batches.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    real_name = Column(String(100), nullable=True)
    identity_no = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    account_name = Column(String(100), nullable=True)
    account_type = Column(String(50), nullable=True)
    permission_type = Column(String(50), nullable=True)
    valid_until = Column(Date, nullable=True)
    result = Column(String(30), default="pending", nullable=False)
    failure_reason = Column(String(500), nullable=True)
    processed_at = Column(DateTime, nullable=True)
    remark = Column(Text, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
