from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Tournament, TournamentStatus
from schemas import TournamentCreate, TournamentResponse, TournamentStatusUpdate
from auth_client import get_current_user, require_admin
from typing import List

router = APIRouter(prefix="/api/tournaments", tags=["Tournaments"])

VALID_TRANSITIONS = {
    TournamentStatus.draft:     [TournamentStatus.active],
    TournamentStatus.active:    [TournamentStatus.completed],
    TournamentStatus.completed: [],
}


# ── ADMIN ONLY ────────────────────────────────────────────

@router.post("/", response_model=TournamentResponse, status_code=201)
def create_tournament(
    data: TournamentCreate,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if data.end_date <= data.start_date:
        raise HTTPException(status_code=400, detail="end_date must be after start_date")
    tournament = Tournament(
        name=data.name,
        description=data.description,
        start_date=data.start_date,
        end_date=data.end_date,
        max_submissions=data.max_submissions,
        created_by=current_user["username"],
    )
    db.add(tournament)
    db.commit()
    db.refresh(tournament)
    return tournament


@router.patch("/{tournament_id}/status", response_model=TournamentResponse)
def update_tournament_status(
    tournament_id: int,
    body: TournamentStatusUpdate,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    allowed = VALID_TRANSITIONS.get(tournament.status, [])
    if body.status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from '{tournament.status.value}' to '{body.status.value}'. "
                   f"Allowed: {[s.value for s in allowed] or 'none — terminal state'}",
        )
    tournament.status = body.status
    db.commit()
    db.refresh(tournament)
    return tournament


@router.delete("/{tournament_id}", status_code=204)
def delete_tournament(
    tournament_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    if tournament.status != TournamentStatus.draft:
        raise HTTPException(status_code=400, detail="Sirf draft tournament delete ho sakta hai.")
    db.delete(tournament)
    db.commit()


# ── DONO (admin + participant) ────────────────────────────

@router.get("/", response_model=List[TournamentResponse])
def list_tournaments(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(Tournament).all()


@router.get("/{tournament_id}", response_model=TournamentResponse)
def get_tournament(
    tournament_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return tournament