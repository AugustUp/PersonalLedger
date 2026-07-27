from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    business_type: str
    business_id: int
    original_name: str
    mime_type: str | None = None
    size: int
    uploaded_by: int | None = None
    created_at: datetime | None = None
