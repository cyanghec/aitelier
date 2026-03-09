import json
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from database import get_session
from models import SessionDB, CanvasStateDB, BlueprintDB
from agents import report_generator

router = APIRouter(prefix="/api/blueprint", tags=["blueprint"])


@router.get("/{session_id}")
def get_blueprint(
    session_id: str,
    db: Session = Depends(get_session),
):
    session = db.get(SessionDB, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Return cached blueprint if it exists
    existing = db.exec(
        select(BlueprintDB).where(BlueprintDB.session_id == session_id)
    ).first()
    if existing:
        return json.loads(existing.blueprint_json)

    # Generate blueprint from canvas state + intake
    canvas_row = db.exec(
        select(CanvasStateDB).where(CanvasStateDB.session_id == session_id)
    ).first()
    if not canvas_row:
        raise HTTPException(status_code=400, detail="No canvas state found for this session")

    canvas_state = json.loads(canvas_row.state_json)
    intake_summary = json.loads(session.intake_summary or "{}")

    blueprint = report_generator.generate(canvas_state, intake_summary)

    # Persist
    record = BlueprintDB(
        session_id=session_id,
        blueprint_json=json.dumps(blueprint),
        readiness_score=float(blueprint.get("readiness_score", 0)),
    )
    db.add(record)
    db.commit()

    return blueprint
