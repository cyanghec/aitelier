import hashlib
import uuid
from datetime import datetime
from typing import Optional, Any
from sqlmodel import SQLModel, Field, Column, JSON


# ── DB Tables ──────────────────────────────────────────────────────────────

class SessionDB(SQLModel, table=True):
    __tablename__ = "sessions"
    session_id: str = Field(primary_key=True)
    rq: str = Field(default="RQ3")
    arm: str  # T1 | T2 | T3
    participant_first: Optional[str] = None
    participant_last: Optional[str] = None
    intake_summary: Optional[str] = None  # JSON string
    intake_complete: bool = Field(default=False)
    canvas_complete: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CanvasStateDB(SQLModel, table=True):
    __tablename__ = "canvas_states"
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True)
    state_json: str  # Full canvas state serialised as JSON string
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class EventDB(SQLModel, table=True):
    __tablename__ = "events"
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True)
    treatment: Optional[str] = None
    event_type: str
    timestamp: str
    data_json: str = Field(default="{}")  # extra fields as JSON


class IntakeMessageDB(SQLModel, table=True):
    __tablename__ = "intake_messages"
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True)
    role: str  # "user" | "assistant"
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SurveyResponseDB(SQLModel, table=True):
    __tablename__ = "survey_responses"
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True, unique=True)
    q1_confidence: Optional[int] = None
    q2_advice_seeking: Optional[int] = None
    q3_delegation: Optional[int] = None
    q4_implementation: Optional[int] = None
    open_reflection: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BlueprintDB(SQLModel, table=True):
    __tablename__ = "blueprints"
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True, unique=True)
    blueprint_json: str  # Full blueprint as JSON
    readiness_score: float
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ── Pydantic Request / Response schemas ────────────────────────────────────

class CreateSessionRequest(SQLModel):
    participant_first: Optional[str] = None
    participant_last: Optional[str] = None


class SessionResponse(SQLModel):
    session_id: str
    rq: str
    arm: str
    participant_first: Optional[str]
    participant_last: Optional[str]
    intake_complete: bool
    canvas_complete: bool
    created_at: datetime


class EventRequest(SQLModel):
    session_id: str
    treatment: Optional[str] = None
    event_type: str
    timestamp: str
    # Any extra fields are accepted via model_extra


class IntakeMessageRequest(SQLModel):
    session_id: str
    message: str


class IntakeMessageResponse(SQLModel):
    reply: str
    intake_complete: bool
    intake_summary: Optional[dict] = None


class OversightAdvisorRequest(SQLModel):
    session_id: str
    capability_name: str
    capability_tier: str  # sense | interpret | act | learn


class OversightAdvisorResponse(SQLModel):
    suggested_level: str  # Automate | Augment | Supervise
    rationale: str
    display_message: str


class DecisionChallengerRequest(SQLModel):
    session_id: str
    capability_name: str
    oversight_chosen: str  # Automate | Augment | Supervise
    canvas_context: Optional[dict] = None  # optional F3/F4/F8 context


class DecisionChallengerResponse(SQLModel):
    challenge: str


class SurveyRequest(SQLModel):
    q1_confidence: Optional[int] = None
    q2_advice_seeking: Optional[int] = None
    q3_delegation: Optional[int] = None
    q4_implementation: Optional[int] = None
    open_reflection: Optional[str] = None


# ── Helpers ────────────────────────────────────────────────────────────────

ARMS = ["T1", "T2", "T3"]


def assign_arm(session_id: str) -> str:
    """Deterministic arm assignment: same session_id always → same arm."""
    h = int(hashlib.md5(session_id.encode()).hexdigest(), 16)
    return ARMS[h % 3]


def generate_session_id(first: Optional[str], last: Optional[str]) -> str:
    initials = ""
    if first:
        initials += first[0].upper()
    if last:
        initials += last[0].upper()
    if not initials:
        initials = uuid.uuid4().hex[:4].upper()
    date_part = datetime.utcnow().strftime("%d%m")
    unique = uuid.uuid4().hex[:4].upper()
    return f"S-{initials}{date_part}-{unique}"
