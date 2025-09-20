from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional
from datetime import datetime

class AnomalyHistoryCreate(BaseModel):
    organization_id: UUID
    run_timestamp: Optional[datetime] = None
    start_date: datetime
    end_date: datetime
    results: str 