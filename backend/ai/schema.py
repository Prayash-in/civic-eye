from enum import Enum

from pydantic import BaseModel, Field


class IssueType(str, Enum):
    POTHOLE = "pothole"
    DAMAGED_ROAD = "damaged_road"
    GARBAGE_OVERFLOW = "garbage_overflow"
    ILLEGAL_DUMPING = "illegal_dumping"
    BROKEN_STREETLIGHT = "broken_streetlight"
    WATER_LEAKAGE = "water_leakage"
    BLOCKED_DRAIN = "blocked_drain"
    OPEN_DRAIN = "open_drain"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CivicIssueAnalysis(BaseModel):
    issue_type: IssueType
    severity: Severity
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str