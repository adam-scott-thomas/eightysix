from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class HealthResponse(BaseModel):
    status: str
    db: str
    version: str


class IngestionSummary(BaseModel):
    created: int = 0
    updated: int = 0
    skipped: int = 0
