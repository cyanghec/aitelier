"""
Intake agent — conversational scoping of the AI initiative.
Multi-turn dialogue until scope confirmed → emits intake_summary JSON.
"""
import json
import os
from typing import Optional, Tuple, List
import anthropic

def _client():
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM_PROMPT = """You are conducting a structured intake interview to scope an executive's AI initiative before they begin designing it. Your goal is to gather enough information to populate an intake summary with these fields:

- problem: the core business problem being solved
- domain: the business domain or function (e.g. finance, supply chain, HR, customer service)
- data_type: the primary type of data involved (e.g. structured transactions, unstructured documents, sensor data)
- team_size: approximate number of people involved in the affected process
- industry: the participant's industry
- implementer_roles: a list of specific lower-level roles who do the operational work (e.g. "credit analysts", "warehouse supervisors", "customer service agents")

Rules:
- Never mention the canvas, fields, or any experimental structure
- Ask open, conversational questions — not a checklist
- Continue for 3–8 turns until you have enough to populate all fields
- When you have gathered sufficient information, end your reply with a JSON block wrapped in <intake_summary>...</intake_summary> tags containing the structured data
- The JSON must have exactly these keys: problem, domain, data_type, team_size, industry, implementer_roles (as a list of strings)
- Be warm and professionally curious, not clinical"""

OPENING_MESSAGE = (
    "Before we open your canvas — tell me about the AI initiative you're here to design. "
    "What business problem are you solving, and which team or data would be involved?"
)


def chat(history: List[dict]) -> Tuple[str, Optional[dict]]:
    """
    Send history to Claude and return (reply_text, intake_summary_or_None).
    history is a list of {role, content} dicts (user + assistant turns).
    """
    messages = history if history else []

    response = _client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=messages,
    )

    reply = response.content[0].text

    # Check if the agent has signalled scope completion
    intake_summary = None
    if "<intake_summary>" in reply and "</intake_summary>" in reply:
        start = reply.index("<intake_summary>") + len("<intake_summary>")
        end = reply.index("</intake_summary>")
        try:
            intake_summary = json.loads(reply[start:end].strip())
        except json.JSONDecodeError:
            intake_summary = None
        # Strip the JSON tag from the displayed reply
        reply = reply[:reply.index("<intake_summary>")].strip()

    return reply, intake_summary


def get_opening() -> str:
    return OPENING_MESSAGE
