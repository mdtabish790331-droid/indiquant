from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from database import get_db
from models import Submission, Tournament, TournamentStatus
import pandas as pd
import io
import os
from datetime import datetime

router = APIRouter(prefix="/api/submissions", tags=["Submissions"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/{tournament_id}")
async def submit_predictions(tournament_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    if tournament.status != TournamentStatus.active:
        raise HTTPException(status_code=400, detail="Tournament is not active")
    
    if datetime.now() > tournament.end_date:
        raise HTTPException(status_code=400, detail="Submission deadline passed")
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files allowed")
    
    content = await file.read()
    
    # Validate CSV
    try:
        df = pd.read_csv(io.BytesIO(content))
        if 'prediction' not in df.columns:
            raise HTTPException(status_code=400, detail="CSV must have 'prediction' column")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid CSV: {str(e)}")
    
    # Save file
    file_path = os.path.join(UPLOAD_DIR, f"tournament_{tournament_id}_user_1_{int(datetime.now().timestamp())}.csv")
    with open(file_path, "wb") as f:
        f.write(content)
    
    submission = Submission(
        tournament_id=tournament_id,
        user_id=1,
        score=0.0,
        file_path=file_path,
        is_valid=1
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    
    return {"message": "Submission successful", "submission_id": submission.id, "rows": len(df)}