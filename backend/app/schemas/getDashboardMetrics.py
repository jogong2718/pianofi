from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from typing import Optional

class DashboardMetrics(BaseModel):
    total_transcriptions: int
    processing_count: int
    this_month_count: int
    transcriptions_left: Optional[int]