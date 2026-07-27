from sqlalchemy import Boolean, Column, ForeignKey, Integer, String

from app.core.database import Base
from app.models.base import TimestampMixin


class Attachment(Base, TimestampMixin):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_type = Column(String(50), nullable=False, index=True)
    business_id = Column(Integer, nullable=False, index=True)
    original_name = Column(String(255), nullable=False)
    stored_name = Column(String(100), nullable=False)
    file_path = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=True)
    size = Column(Integer, nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
