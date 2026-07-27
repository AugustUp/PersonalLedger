from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class MeetingRecord(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "meeting_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_no = Column(String(30), unique=True, index=True, nullable=False)
    meeting_name = Column(String(200), nullable=False)
    meeting_time = Column(DateTime, nullable=True)
    location = Column(String(200), nullable=True)
    contact_name = Column(String(100), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    technicians = Column(String(300), nullable=True)
    equipment = Column(Text, nullable=True)
    debug_content = Column(Text, nullable=True)
    problem_description = Column(Text, nullable=True)
    handling_process = Column(Text, nullable=True)
    result = Column(Text, nullable=True)
    onsite_support = Column(Boolean, default=False, nullable=False)
    status = Column(String(30), nullable=False, default="pending")
    remark = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
