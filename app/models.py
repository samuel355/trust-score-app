from pydantic import BaseModel
from datetime import datetime

class TelemetryData(BaseModel):
    id: int
    vm_id: str
    timestamp: datetime
    event_type: str | None = None
    stride_category: str | None = None
    risk_level: int | None = None

class TrustScore(BaseModel):
    id: int
    session_id: str
    vm_id: str
    timestamp: datetime
    trust_score: float
    mfa_required: bool
