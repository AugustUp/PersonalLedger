from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, func

from app.core.database import Base


class OperationLog(Base):
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True, index=True)
    module = Column(String(50), nullable=False, index=True)
    action = Column(String(50), nullable=False)
    business_id = Column(Integer, nullable=True, index=True)
    description = Column(String(500), nullable=True)
    request_ip = Column(String(64), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
