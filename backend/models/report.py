from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel

from backend.config import AnalysisStatus


class ReportStatus(str, Enum):
    SUBMITTED = "submitted"
    REVIEWED = "reviewed"
    RESOLVED = "resolved"


class ReportCreate(BaseModel):
    image_path: str
    description: str
    category: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class Report(BaseModel):
    id: int
    image_path: str
    description: str
    category: str = ""
    issue_type: Optional[str] = None
    severity: Optional[str] = None
    confidence: Optional[float] = None
    explanation: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: ReportStatus = ReportStatus.SUBMITTED
    analysis_status: AnalysisStatus = AnalysisStatus.PENDING
    created_at: datetime

    # Civic Intelligence routing fields (nullable — legacy reports stay valid)
    authority_name: Optional[str] = None
    department: Optional[str] = None
    routing_reason: Optional[str] = None
    assembly_constituency_id: Optional[str] = None
    assembly_constituency_name: Optional[str] = None
    lok_sabha_constituency_id: Optional[str] = None
    mla_name: Optional[str] = None
    mla_party: Optional[str] = None
    mp_name: Optional[str] = None
    mp_party: Optional[str] = None
    jurisdiction_status: Optional[str] = None
    resolution_method: Optional[str] = None
    notification_status: Optional[str] = None
    notification_channel: Optional[str] = None
    notification_sent_at: Optional[str] = None