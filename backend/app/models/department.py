from sqlalchemy import Column, ForeignKey, Integer, String, Text

from app.core.database import Base
from app.models.base import TimestampMixin


class Department(Base, TimestampMixin):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=True)
    parent_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    remark = Column(Text, nullable=True)
