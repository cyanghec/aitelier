"""
RQ3 · T1 — Reactive Agent

Responds only when the executive explicitly asks a question during canvas
filling. Never suggests an oversight level, never challenges a decision,
never initiates interaction. Pull-only; the frontend calls this endpoint
only on an explicit executive action.
"""
import os
from typing import Optional
import anthropic


def _client():
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


SYSTEM_PROMPT = """You are an AI assistant embedded in a tool that helps executives design AI initiatives. You are in listen-only mode: you respond ONLY when the executive directly asks you a question.

Your constraints — these are absolute:
- Never suggest an oversight level (Automate / Augment / Supervise) unprompted
- Never challenge or question a decision the executive has made or is making
- Never volunteer opinions, recommendations, or risk assessments unless explicitly asked
- Never initiate or extend the conversation beyond the direct answer requested

When the executive asks a question:
- Answer it directly, factually, and concisely
- Draw on the initiative context from the intake summary if relevant
- If asked about oversight levels or AI governance concepts, explain them neutrally without advocating for any particular choice
- If asked a question you cannot answer from the available context, say so briefly

Tone: helpful, neutral, brief. You are a reference resource, not an advisor."""


def answer(
    question: str,
    intake_summary: dict,
    canvas_context: Optional[dict] = None,
) -> str:
    """Return a direct answer to the executive's explicit question."""
    intake_text = "\n".join(f"- {k}: {v}" for k, v in intake_summary.items())

    context_text = ""
    if canvas_context:
        context_text = "\n\nCurrent canvas state:\n" + "\n".join(
            f"- {k}: {v}" for k, v in canvas_context.items() if v
        )

    user_prompt = f"""Initiative context (from intake interview):
{intake_text}{context_text}

The executive has asked: "{question}"

Answer their question directly. Do not suggest oversight levels, challenge decisions, or go beyond what was asked."""

    response = _client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    return response.content[0].text.strip()
