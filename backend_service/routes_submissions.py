from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from database import get_db
from models import Submission, Tournament, TournamentStatus
from schemas import SubmissionResponse, LeaderboardEntry
from auth_client import get_current_user, require_participant
from typing import List
import pandas as pd
import io
import os
from datetime import datetime, timezone

router = APIRouter(prefix="/api/submissions", tags=["Submissions"])
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ── PARTICIPANT ONLY ──────────────────────────────────────

@router.post("/{tournament_id}", response_model=SubmissionResponse, status_code=201)
async def submit_predictions(
    tournament_id: int,
    file: UploadFile = File(...),
    current_user: dict = Depends(require_participant),
    db: Session = Depends(get_db),
):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    if tournament.status != TournamentStatus.active:
        raise HTTPException(status_code=400, detail="Tournament is not active")
    if datetime.now(timezone.utc) > tournament.end_date:
        raise HTTPException(status_code=400, detail="Submission deadline has passed")

    user_id = current_user["user_id"]
    count = db.query(Submission).filter(
        Submission.tournament_id == tournament_id,
        Submission.user_id == user_id,
        Submission.is_valid == True,
    ).count()
    if count >= tournament.max_submissions:
        raise HTTPException(status_code=400, detail=f"Limit reached: max {tournament.max_submissions} submissions.")

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Sirf .csv file allowed hai.")

    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSV parse error: {str(e)}")

    if "prediction" not in df.columns:
        raise HTTPException(status_code=400, detail="CSV mein 'prediction' column hona chahiye.")
    if df.empty:
        raise HTTPException(status_code=400, detail="CSV empty hai.")

    timestamp = int(datetime.now(timezone.utc).timestamp())
    file_path = os.path.join(UPLOAD_DIR, f"t{tournament_id}_u{user_id}_{timestamp}.csv")
    with open(file_path, "wb") as f:
        f.write(content)

    submission = Submission(
        tournament_id=tournament_id,
        user_id=user_id,
        username=current_user["username"],
        score=0.0,
        file_path=file_path,
        is_valid=True,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


# ── DONO (admin + participant) ────────────────────────────

@router.get("/{tournament_id}", response_model=List[SubmissionResponse])
def get_submissions(
    tournament_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    query = db.query(Submission).filter(Submission.tournament_id == tournament_id)
    if current_user["role"] == "participant":
        query = query.filter(Submission.user_id == current_user["user_id"])
    return query.order_by(Submission.submitted_at.desc()).all()


@router.get("/{tournament_id}/leaderboard", response_model=List[LeaderboardEntry])
def get_leaderboard(
    tournament_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    submissions = db.query(Submission).filter(
        Submission.tournament_id == tournament_id,
        Submission.is_valid == True,
    ).order_by(Submission.score.desc(), Submission.submitted_at.asc()).all()

    seen, leaderboard, rank = set(), [], 1
    for sub in submissions:
        if sub.user_id not in seen:
            seen.add(sub.user_id)
            leaderboard.append(LeaderboardEntry(
                rank=rank, user_id=sub.user_id, username=sub.username,
                score=sub.score, submitted_at=sub.submitted_at,
            ))
            rank += 1
    return leaderboard