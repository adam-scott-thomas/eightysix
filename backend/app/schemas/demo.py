from pydantic import BaseModel, Field


class LoadScenarioRequest(BaseModel):
    scenario: str
    location_id: str | None = None


class QuickAssessRequest(BaseModel):
    staff_count: int = Field(ge=1, le=100)
    orders_today: int = Field(ge=1, le=5000)
    avg_ticket: float = Field(gt=0, le=1000)
    restaurant_name: str = "Your Restaurant"


class SyncRequest(BaseModel):
    location_id: str
    providers: list[str] = ["pos", "labor"]


class RecomputeRequest(BaseModel):
    location_id: str
