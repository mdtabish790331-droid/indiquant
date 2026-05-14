from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum, Boolean
from sqlalchemy.sql import func
from database import Base
import enum


class TournamentStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    completed = "completed"


class Tournament(Base):
    __tablename__ = "tournaments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    max_submissions = Column(Integer, default=5)
    status = Column(Enum(TournamentStatus), default=TournamentStatus.draft)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # FIX: store username from token (no FK to auth DB since services are separate)
    created_by = Column(String, nullable=False)


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False)
    # FIX: store actual user_id from token, not hardcoded 1
    user_id = Column(Integer, nullable=False)
    username = Column(String, nullable=False)
    score = Column(Float, default=0.0)
    rank = Column(Integer, nullable=True)
    file_path = Column(String)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    # FIX: was Integer before — should be Boolean
    is_valid = Column(Boolean, default=True)
    validation_error = Column(String, nullable=True)