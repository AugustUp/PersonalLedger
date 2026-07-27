from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class MaintenanceRecord(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "maintenance_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_no = Column(String(30), unique=True, index=True, nullable=False)
    category = Column(String(50), index=True, nullable=True)
    requester = Column(String(100), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    location = Column(String(200), nullable=True)
    problem_description = Column(Text, nullable=True)
    handling_process = Column(Text, nullable=True)
    fault_cause = Column(Text, nullable=True)
    result = Column(Text, nullable=True)
    status = Column(String(30), nullable=False, default="pending")
    handler = Column(String(100), nullable=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    remark = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
