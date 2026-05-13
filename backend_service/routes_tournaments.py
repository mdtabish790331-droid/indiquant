from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Tournament, TournamentStatus
from schemas import TournamentCreate, TournamentResponse

router = APIRouter(prefix="/api/tournaments", tags=["Tournaments"])

@router.post("/", response_model=TournamentResponse)
def create_tournament(tournament: TournamentCreate, db: Session = Depends(get_db)):
    db_tournament = Tournament(
        name=tournament.name,
        description=tournament.description,
        start_date=tournament.start_date,
        end_date=tournament.end_date,
        max_submissions=tournament.max_submissions,
        created_by=1
    )
    db.add(db_tournament)
    db.commit()
    db.refresh(db_tournament)
    return db_tournament

@router.get("/", response_model=List[TournamentResponse])
def list_tournaments(status: TournamentStatus = None, db: Session = Depends(get_db)):
    query = db.query(Tournament)
    if status:
        query = query.filter(Tournament.status == status)
    return query.all()

@router.get("/{tournament_id}", response_model=TournamentResponse)
def get_tournament(tournament_id: int, db: Session = Depends(get_db)):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return tournament

@router.post("/{tournament_id}/activate")
def activate_tournament(tournament_id: int, db: Session = Depends(get_db)):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    tournament.status = TournamentStatus.active
    db.commit()
    return {"message": f"Tournament '{tournament.name}' activated"}