from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List

from agents import moderator

router = APIRouter(prefix="/api/moderator", tags=["moderator"])


class TeamMember(BaseModel):
    initials: str
    name: str


class ModeratorMessageRequest(BaseModel):
    session_id: Optional[str] = None
    page: str                        # index | canvas | blueprint | survey
    trigger: str                     # page_load | phase_change | canvas_complete | field_complete
    context: dict = {}               # phase, fields_done, scope, ...
    team_members: List[TeamMember] = []


class ModeratorMessageResponse(BaseModel):
    message: str
    cue_member: Optional[dict] = None   # {initials, name}
    timer_minutes: Optional[int] = None


@router.post("/message", response_model=ModeratorMessageResponse)
def get_moderator_message(req: ModeratorMessageRequest):
    result = moderator.facilitate(
        page=req.page,
        trigger=req.trigger,
        context=req.context,
        team_members=[m.dict() for m in req.team_members],
    )
    return result
