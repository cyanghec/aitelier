"""
AItelier — Moderator Agent
Generates contextual facilitation messages for the professor avatar.
Called on page load and key events (phase change, completion).
"""
import anthropic
import os
from typing import Optional

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


SYSTEM = """You are a session moderator avatar for AItelier — a platform where executive teams design AI governance frameworks. You appear as a named professor throughout the session.

Your role: brief, incisive facilitation. You guide discussion, keep time, and prompt reflection. You do NOT teach or lecture.

Style:
- 1–2 sentences maximum
- Direct, warm, intellectually sharp
- Ask questions that surface disagreement or blind spots
- Never use bullet points or lists
- Never mention AI, machine learning, or technology explicitly — focus on decisions, accountability, and governance
- Speak to the group, not to an individual (unless cueing someone)

When cueing a team member, address them by first name: "Jean, what's your read on this?"

Context provided: page name, trigger event, which phase (if canvas), team member names, session summary.
"""


def facilitate(
    page: str,
    trigger: str,
    context: dict,
    team_members: list,
    session_summary: Optional[str] = None,
) -> dict:
    """
    Generate a facilitation message for the moderator avatar.

    Returns:
        {
          "message": str,
          "cue_member": {"initials": str, "name": str} | None,
          "timer_minutes": int | None
        }
    """
    phase = context.get("phase")
    fields_done = context.get("fields_done", 0)
    scope = context.get("scope", "")

    # Build context description
    ctx_parts = [f"Page: {page}", f"Trigger: {trigger}"]
    if phase:
        ctx_parts.append(f"Canvas phase: {phase} of 4")
    if fields_done:
        ctx_parts.append(f"Fields completed so far: {fields_done}")
    if scope:
        ctx_parts.append(f"Initiative scope: {scope}")
    if session_summary:
        ctx_parts.append(f"Session summary: {session_summary}")
    if team_members:
        names = ", ".join(f"{m.get('name','')} ({m.get('initials','')})" for m in team_members)
        ctx_parts.append(f"Team members: {names}")

    # Decide whether to cue a member
    should_cue = (
        trigger in ("phase_change", "field_complete")
        and len(team_members) > 0
        and (phase in (2, 3) or trigger == "field_complete")
    )

    cue_instruction = ""
    cue_member = None
    if should_cue and team_members:
        import hashlib
        # Deterministic but varied cue selection based on phase + trigger
        seed = f"{page}{trigger}{phase}{fields_done}"
        idx = int(hashlib.md5(seed.encode()).hexdigest(), 16) % len(team_members)
        cue_member = team_members[idx]
        cue_instruction = (
            f"\n\nIf appropriate, address {cue_member.get('name', 'this person')} directly "
            f"at the end of your message."
        )

    # Timer logic: only for phase starts
    timer_map = {1: 20, 2: 25, 3: 20, 4: 15}
    timer_minutes = timer_map.get(phase) if trigger == "phase_change" else None

    user_prompt = (
        "\n".join(ctx_parts)
        + cue_instruction
        + "\n\nWrite a single facilitation message for this moment."
    )

    try:
        msg = _get_client().messages.create(
            model="claude-sonnet-4-6",
            max_tokens=120,
            system=SYSTEM,
            messages=[{"role": "user", "content": user_prompt}],
        )
        message = msg.content[0].text.strip()
    except Exception:
        # Fallback messages per trigger
        fallbacks = {
            "page_load":       "Welcome. Take a moment to settle in — the quality of this session depends on full attention from everyone in the room.",
            "phase_change":    "Moving to the next phase. Before you proceed — is there anything unresolved from the last section that needs naming?",
            "canvas_complete": "Well done. Your blueprint is being generated. Before you move on, take thirty seconds: what is the single assumption this whole canvas rests on?",
        }
        message = fallbacks.get(trigger, "Take a moment as a group before continuing.")

    return {
        "message": message,
        "cue_member": cue_member,
        "timer_minutes": timer_minutes,
    }
