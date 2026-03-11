import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from database import get_session
from models import (
    SessionDB, IntakeMessageDB,
    IntakeMessageRequest, IntakeMessageResponse,
    OversightAdvisorRequest, OversightAdvisorResponse,
    OversightAdvisorOutcomeRequest,
    DecisionChallengerRequest, DecisionChallengerResponse,
    DecisionChallengerOutcomeRequest,
    ReactiveQueryRequest, ReactiveQueryResponse,
    EventDB,
)
from agents import intake, rq3_oversight_advisor, rq3_decision_challenger, reactive

router = APIRouter(prefix="/api/guidance", tags=["guidance"])


# ── Intake ──────────────────────────────────────────────────────────────────

@router.get("/intake-opening")
def get_intake_opening():
    return {"message": intake.get_opening()}


@router.post("/intake-message", response_model=IntakeMessageResponse)
def intake_message(
    body: IntakeMessageRequest,
    db: Session = Depends(get_session),
):
    session = db.get(SessionDB, body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.intake_complete:
        raise HTTPException(status_code=400, detail="Intake already complete")

    # Load full history for this session
    history_rows = db.exec(
        select(IntakeMessageDB)
        .where(IntakeMessageDB.session_id == body.session_id)
        .order_by(IntakeMessageDB.id)
    ).all()

    history = [{"role": r.role, "content": r.content} for r in history_rows]

    # Append the new user message
    history.append({"role": "user", "content": body.message})

    # Call the intake agent
    reply, intake_summary = intake.chat(history)

    # Persist user message
    db.add(IntakeMessageDB(
        session_id=body.session_id, role="user", content=body.message
    ))
    # Persist assistant reply
    db.add(IntakeMessageDB(
        session_id=body.session_id, role="assistant", content=reply
    ))

    if intake_summary:
        session.intake_summary = json.dumps(intake_summary)
        session.intake_complete = True
        db.add(session)

    db.commit()

    return IntakeMessageResponse(
        reply=reply,
        intake_complete=session.intake_complete,
        intake_summary=intake_summary,
    )


# ── Oversight Advisor (RQ3 · T2) ────────────────────────────────────────────

@router.post("/oversight-advisor", response_model=OversightAdvisorResponse)
def oversight_advisor(
    body: OversightAdvisorRequest,
    db: Session = Depends(get_session),
):
    session = db.get(SessionDB, body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.arm != "T2":
        raise HTTPException(status_code=403, detail="Oversight Advisor is only active for arm T2")

    intake_summary = json.loads(session.intake_summary or "{}")

    result = rq3_oversight_advisor.advise(
        capability_name=body.capability_name,
        capability_tier=body.capability_tier,
        intake_summary=intake_summary,
        capability_input=body.capability_input or "",
        capability_output=body.capability_output or "",
    )

    # Log the agent event
    db.add(EventDB(
        session_id=body.session_id,
        treatment="T2",
        event_type="oversight.suggested",
        timestamp=datetime.now(timezone.utc).isoformat(),
        data_json=json.dumps({
            "capability": body.capability_name,
            "tier": body.capability_tier,
            "suggested_level": result["suggested_level"],
        }),
    ))
    db.commit()

    return OversightAdvisorResponse(**result)


# ── Decision Challenger (RQ3 · T3) ──────────────────────────────────────────

@router.post("/decision-challenger", response_model=DecisionChallengerResponse)
def decision_challenger(
    body: DecisionChallengerRequest,
    db: Session = Depends(get_session),
):
    session = db.get(SessionDB, body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.arm != "T3":
        raise HTTPException(status_code=403, detail="Decision Challenger is only active for arm T3")

    intake_summary = json.loads(session.intake_summary or "{}")

    challenge = rq3_decision_challenger.challenge(
        capability_name=body.capability_name,
        oversight_chosen=body.oversight_chosen,
        intake_summary=intake_summary,
        capability_input=body.capability_input or "",
        capability_output=body.capability_output or "",
        canvas_context=body.canvas_context,
    )

    # Log the agent event
    db.add(EventDB(
        session_id=body.session_id,
        treatment="T3",
        event_type="challenge.prompted",
        timestamp=datetime.now(timezone.utc).isoformat(),
        data_json=json.dumps({
            "capability": body.capability_name,
            "F6.choice.before": body.oversight_chosen,
        }),
    ))
    db.commit()

    return DecisionChallengerResponse(challenge=challenge)


# ── Reactive Query (RQ3 · T1) ────────────────────────────────────────────────

@router.post("/reactive-query", response_model=ReactiveQueryResponse)
def reactive_query(
    body: ReactiveQueryRequest,
    db: Session = Depends(get_session),
):
    session = db.get(SessionDB, body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.arm != "T1":
        raise HTTPException(status_code=403, detail="Reactive Agent is only active for arm T1")

    intake_summary = json.loads(session.intake_summary or "{}")

    answer = reactive.answer(
        question=body.question,
        intake_summary=intake_summary,
        canvas_context=body.canvas_context,
    )

    # Log the agent event
    db.add(EventDB(
        session_id=body.session_id,
        treatment="T1",
        event_type="agent.queried",
        timestamp=datetime.now(timezone.utc).isoformat(),
        data_json=json.dumps({
            "query_content": body.question,
        }),
    ))
    db.commit()

    return ReactiveQueryResponse(answer=answer)


# ── Oversight Advisor Outcome (RQ3 · T2) — primary DV ───────────────────────

@router.post("/oversight-advisor-outcome")
def oversight_advisor_outcome(
    body: OversightAdvisorOutcomeRequest,
    db: Session = Depends(get_session),
):
    session = db.get(SessionDB, body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.arm != "T2":
        raise HTTPException(status_code=403, detail="Oversight Advisor outcome is only for arm T2")

    db.add(EventDB(
        session_id=body.session_id,
        treatment="T2",
        event_type="oversight.outcome",
        timestamp=datetime.now(timezone.utc).isoformat(),
        data_json=json.dumps({
            "capability": body.capability_name,
            "F6.suggestion": body.F6_suggestion,
            "F6.final": body.F6_final,
            "accepted_suggestion": body.accepted_suggestion,
        }),
    ))
    db.commit()
    return {"status": "logged"}


# ── Decision Challenger Outcome (RQ3 · T3) — primary DV ─────────────────────

@router.post("/decision-challenger-outcome")
def decision_challenger_outcome(
    body: DecisionChallengerOutcomeRequest,
    db: Session = Depends(get_session),
):
    session = db.get(SessionDB, body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.arm != "T3":
        raise HTTPException(status_code=403, detail="Decision Challenger outcome is only for arm T3")

    db.add(EventDB(
        session_id=body.session_id,
        treatment="T3",
        event_type="challenge.outcome",
        timestamp=datetime.now(timezone.utc).isoformat(),
        data_json=json.dumps({
            "capability": body.capability_name,
            "F6.choice.before": body.F6_choice_before,
            "F6.choice.after": body.F6_choice_after,
            "revised_after_challenge": body.revised_after_challenge,
        }),
    ))
    db.commit()
    return {"status": "logged"}
