from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import ImportCommit, ImportPreview, PageQuery


class AccountBatchBase(BaseModel):
    batch_name: str = Field(..., min_length=1, max_length=200)
    account_type: str | None = Field(None, max_length=50)
    applicant_department: str | None = Field(None, max_length=100)
    applicant: str | None = Field(None, max_length=100)
    application_date: date | None = None
    handler: str | None = Field(None, max_length=100)
    remark: str | None = None


class AccountBatchCreate(AccountBatchBase):
    pass


class AccountBatchUpdate(BaseModel):
    batch_name: str | None = Field(None, max_length=200)
    account_type: str | None = Field(None, max_length=50)
    applicant_department: str | None = Field(None, max_length=100)
    applicant: str | None = Field(None, max_length=100)
    application_date: date | None = None
    handler: str | None = Field(None, max_length=100)
    status: str | None = Field(
        None, pattern="^(draft|pending|processing|partial|completed|cancelled)$"
    )
    remark: str | None = None


class AccountBatchQuery(PageQuery):
    batch_name: str | None = None
    account_type: str | None = None
    status: str | None = None
    applicant: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class AccountBatchListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_no: str
    batch_name: str
    account_type: str | None = None
    applicant: str | None = None
    applicant_department: str | None = None
    application_date: date | None = None
    total_count: int
    success_count: int
    failed_count: int
    pending_count: int
    status: str
    handler: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AccountBatchDetail(AccountBatchListItem):
    remark: str | None = None
    source_file_id: int | None = None
    result_file_id: int | None = None


class AccountBatchItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_id: int
    real_name: str | None = None
    identity_no: str | None = None
    department: str | None = None
    account_name: str | None = None
    account_type: str | None = None
    permission_type: str | None = None
    valid_until: date | None = None
    result: str
    failure_reason: str | None = None
    processed_at: datetime | None = None
    remark: str | None = None


class BatchItemResultUpdate(BaseModel):
    id: int
    result: str = Field(..., pattern="^(pending|success|failed|skipped)$")
    failure_reason: str | None = Field(None, max_length=500)


class BatchItemResultBatchUpdate(BaseModel):
    items: list[BatchItemResultUpdate]


class AccountBatchItemQuery(PageQuery):
    result: str | None = None
    keyword: str | None = None


class BatchImportPreview(ImportPreview):
    pass


class BatchImportCommit(ImportCommit):
    batch_id: int | None = None
