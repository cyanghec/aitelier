"""
RQ3 · T3 — Decision Challenger

Fires after the executive sets the oversight level for a capability (F6),
before they confirm. Challenges their choice by surfacing accountability
implications and failure-mode consequences.
"""
import os
from typing import Optional
import anthropic

def _client():
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM_PROMPT = """You are an AI governance advisor embedded in a tool that helps executives design AI initiatives. An executive has just set an oversight level for an AI capability and you must challenge their decision before they confirm it.

Your purpose is NOT to say they are wrong — it is to surface the accountability and failure-mode implications they may not have considered, so they make a more deliberate choice.

Your challenge must:
1. Name the specific capability and oversight level they chose
2. Present a concrete failure scenario (systematic error persisting undetected for months)
3. Ask who is responsible and what the remediation path is in that scenario
4. Ask whether this changes their oversight choice

Tone: direct, intellectually serious, not alarmist. You are a peer challenging them to think harder, not a compliance officer lecturing them.

Output exactly one paragraph (3–5 sentences). No headers, no bullet points. Address the executive directly in second person."""


def challenge(
    capability_name: str,
    oversight_chosen: str,
    intake_summary: dict,
    capability_input: str = "",
    capability_output: str = "",
    canvas_context: Optional[dict] = None,
) -> str:
    """Return the challenge message string."""
    intake_text = "\n".join(f"- {k}: {v}" for k, v in intake_summary.items())

    io_section = ""
    if capability_input or capability_output:
        io_section = "\n\nCapability I/O (as described by the executive):"
        if capability_input:
            io_section += f"\n- Input: {capability_input}"
        if capability_output:
            io_section += f"\n- Expected output: {capability_output}"

    context_text = ""
    if canvas_context:
        context_text = "\n\nAdditional canvas context:\n" + "\n".join(
            f"- {k}: {v}" for k, v in canvas_context.items() if v
        )

    user_prompt = f"""Initiative context (from intake interview):
{intake_text}{io_section}{context_text}

The executive has set the oversight level for "{capability_name}" to "{oversight_chosen}".

Generate a challenge question that:
- Grounds the failure scenario in the specific expected output (if provided) — what does it look like when THAT output is wrong?
- Asks concretely: if this system produced systematic errors for 3 months before anyone noticed, who would be responsible and what would the remediation path look like?
- Ends by asking whether knowing this changes their oversight choice

Do not repeat the prompt instructions. Write only the challenge message."""

    response = _client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    return response.content[0].text.strip()
