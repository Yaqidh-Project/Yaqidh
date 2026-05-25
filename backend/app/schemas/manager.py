import uuid
from pydantic import BaseModel
from typing import Optional

class ZonePerformanceMetric(BaseModel):
    zone_id: uuid.UUID
    zone_name: str
    assigned_teachers: list[str]  
    total_incidents: int
    resolved_incidents: int
    average_response_time_seconds: Optional[float] = None

class PerformanceDashboardOut(BaseModel):
    summary: dict
    zones_performance: list[ZonePerformanceMetric]