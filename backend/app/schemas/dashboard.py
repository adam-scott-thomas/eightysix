from pydantic import BaseModel


class ReadinessResponse(BaseModel):
    status: str
    completeness_score: float
    missing_domains: list[str]
    available_quick_wins: list[str]
