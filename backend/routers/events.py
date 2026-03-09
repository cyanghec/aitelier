import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Response
from sqlmodel import Session

from database import get_session
from models import EventDB

router = APIRouter(prefix="/api/events", tags=["events"])


@router.post("")
def log_event(
    body: dict,
    db: Session = Depends(get_session),
):
    # Accept any shape matching the frontend logEvent() schema
    session_id = body.pop("session_id", "unknown")
    treatment = body.pop("treatment", None)
    event_type = body.pop("event_type", "unknown")
    timestamp = body.pop("timestamp", datetime.now(timezone.utc).isoformat())

    record = EventDB(
        session_id=session_id,
        treatment=treatment,
        event_type=event_type,
        timestamp=timestamp,
        data_json=json.dumps(body),
    )
    db.add(record)
    db.commit()
    return Response(status_code=204)
