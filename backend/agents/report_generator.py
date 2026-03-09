"""
Report Generator — synthesises canvas state + intake + events → AI Decision Blueprint.
Strips all agent prompt text; returns only the executive's final field values + analysis.
"""
import json
import os
import anthropic

def _client():
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM_PROMPT = """You are a senior AI governance analyst. You will receive a completed AI initiative canvas (the executive's own answers) and a session intake summary, and you must generate a structured AI Decision Blueprint.

IMPORTANT: The blueprint must reflect ONLY the participant's own field values. Do not include or reference any AI agent suggestions, prompts, or messages. Experts reading this blueprint are blind to the experimental treatment.

Generate a JSON object with exactly these keys:
{
  "initiative_title": "A concise title derived from the problem and domain",
  "executive_summary": "2–3 sentence summary of the initiative",
  "initiative_overview": {
    "scope": "single-function | multi-function | enterprise",
    "problem_statement": "from F0/intake",
    "data_sources": ["list from F1"],
    "human_roles": ["list from F2"],
    "systems_infrastructure": "from F3",
    "tacit_constraints": "from F4"
  },
  "capability_stack": [
    {
      "name": "capability name",
      "tier": "sense|interpret|act|learn",
      "input_sources": "...",
      "human_judgment": "...",
      "oversight_level": "Automate|Augment|Supervise"
    }
  ],
  "oversight_design": {
    "automate_count": 0,
    "augment_count": 0,
    "supervise_count": 0,
    "oversight_notes": "brief observation about the overall oversight pattern"
  },
  "feedback_loops": {
    "capture_method": "...",
    "review_cadence": "...",
    "notes": "..."
  },
  "business_outcomes": "from F8",
  "governance": {
    "model_owner": "...",
    "retraining_authority": "...",
    "shutdown_authority": "...",
    "governance_narrative": "from F9"
  },
  "readiness_score": 0.0,
  "readiness_rationale": "1–2 sentences explaining the score",
  "recommendations": [
    {"severity": "red|amber|green", "message": "..."}
  ]
}

Readiness score (0–5): assess holistically — 5 means governance-ready, well-specified, operationally grounded; 1–2 means significant gaps in oversight or tacit knowledge. Apply the same rigour as an expert panel reviewer.

Recommendations: flag missing governance (red), oversight mismatches (amber), or strengths (green). Limit to 3–5 items."""


def generate(
    canvas_state: dict,
    intake_summary: dict,
) -> dict:
    """Generate blueprint JSON from canvas state and intake summary."""
    canvas_text = json.dumps(canvas_state, indent=2)
    intake_text = json.dumps(intake_summary, indent=2)

    user_prompt = f"""Intake summary:
{intake_text}

Canvas state (participant's own answers):
{canvas_text}

Generate the AI Decision Blueprint JSON."""

    response = _client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    text = response.content[0].text.strip()

    # Extract JSON if wrapped in markdown code block
    if "```json" in text:
        text = text.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in text:
        text = text.split("```", 1)[1].split("```", 1)[0].strip()

    return json.loads(text)
