from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from database import get_session
from models import SessionDB, SurveyResponseDB, SurveyRequest

router = APIRouter(prefix="/api/survey", tags=["survey"])


@router.post("/{session_id}")
def submit_survey(
    session_id: str,
    body: SurveyRequest,
    db: Session = Depends(get_session),
):
    session = db.get(SessionDB, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    existing = db.exec(
        select(SurveyResponseDB).where(SurveyResponseDB.session_id == session_id)
    ).first()

    if existing:
        for k, v in body.model_dump(exclude_none=True).items():
            setattr(existing, k, v)
        db.add(existing)
    else:
        record = SurveyResponseDB(session_id=session_id, **body.model_dump())
        db.add(record)

    db.commit()
    return {"status": "survey_saved", "session_id": session_id}
