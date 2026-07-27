"""Shared request/response schemas (manual 7.3, 8.2, 8.3)."""
from datetime import date, datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageQuery(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    sort_by: str | None = None
    sort_order: str = Field("desc", pattern="^(asc|desc)$")


class PageResult(BaseModel, Generic[T]):
    items: list[T]
    page: int
    page_size: int
    total: int
    pages: int


class IDResponse(BaseModel):
    id: int


# ---- Excel import preview / commit (manual 11.4) ----
class ImportErrorItem(BaseModel):
    row: int
    field: str | None = None
    message: str


class ImportPreview(BaseModel):
    import_token: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    errors: list[ImportErrorItem] = []
    sample: list[dict] = []


class ImportCommit(BaseModel):
    import_token: str
    strategy: str = Field("skip", pattern="^(skip|update)$")
