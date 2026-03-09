import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from database import get_session
from models import SessionDB, CanvasStateDB

router = APIRouter(prefix="/api/canvas", tags=["canvas"])


@router.put("/{session_id}")
def save_canvas(
    session_id: str,
    body: dict,
    db: Session = Depends(get_session),
):
    session = db.get(SessionDB, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    existing = db.exec(
        select(CanvasStateDB).where(CanvasStateDB.session_id == session_id)
    ).first()

    if existing:
        existing.state_json = json.dumps(body)
        existing.updated_at = datetime.utcnow()
        db.add(existing)
    else:
        record = CanvasStateDB(
            session_id=session_id,
            state_json=json.dumps(body),
        )
        db.add(record)

    db.commit()
    return {"status": "saved"}


@router.get("/{session_id}")
def get_canvas(
    session_id: str,
    db: Session = Depends(get_session),
):
    record = db.exec(
        select(CanvasStateDB).where(CanvasStateDB.session_id == session_id)
    ).first()
    if not record:
        return {}
    return json.loads(record.state_json)


@router.post("/{session_id}/complete")
def complete_canvas(
    session_id: str,
    db: Session = Depends(get_session),
):
    session = db.get(SessionDB, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.canvas_complete = True
    session.updated_at = datetime.utcnow()
    db.add(session)
    db.commit()
    return {"status": "canvas_complete"}
