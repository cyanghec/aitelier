from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from database import get_session
from models import (
    SessionDB, CreateSessionRequest, SessionResponse,
    assign_arm, generate_session_id,
)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse)
def create_session(
    body: CreateSessionRequest,
    db: Session = Depends(get_session),
):
    session_id = generate_session_id(body.participant_first, body.participant_last)
    arm = assign_arm(session_id)

    record = SessionDB(
        session_id=session_id,
        arm=arm,
        participant_first=body.participant_first,
        participant_last=body.participant_last,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/{session_id}", response_model=SessionResponse)
def get_session_by_id(
    session_id: str,
    db: Session = Depends(get_session),
):
    record = db.get(SessionDB, session_id)
    if not record:
        raise HTTPException(status_code=404, detail="Session not found")
    return record
