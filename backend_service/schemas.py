from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum


class TournamentStatus(str, Enum):
    draft = "draft"
    active = "active"
    completed = "completed"


class TournamentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    max_submissions: int = 5


class TournamentStatusUpdate(BaseModel):
    status: TournamentStatus


class TournamentResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    start_date: datetime
    end_date: datetime
    max_submissions: int
    status: TournamentStatus
    created_at: datetime
    created_by: str

    class Config:
        from_attributes = True


class SubmissionResponse(BaseModel):
    id: int
    tournament_id: int
    user_id: int
    username: str
    score: float
    rank: Optional[int]
    submitted_at: datetime
    is_valid: bool
    validation_error: Optional[str]

    class Config:
        from_attributes = True


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    username: str
    score: float
    submitted_at: datetime