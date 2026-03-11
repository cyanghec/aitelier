"""
RQ3 · T2 — Oversight Advisor

Fires after the executive selects an AI capability (F5), before they set
the oversight level (F6). Suggests a default oversight level with rationale
grounded in the capability tier and initiative context from intake.
"""
import os
import anthropic

def _client():
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# Tier defaults used as a prior, but Claude reasons from context
TIER_DEFAULTS = {
    "sense": "Automate",
    "interpret": "Augment",
    "act": "Supervise",
    "learn": "Augment",
}

SYSTEM_PROMPT = """You are an AI governance advisor embedded in a tool that helps executives design AI initiatives. Your role is to recommend an appropriate oversight level for a specific AI capability before the executive sets it.

Oversight levels (choose exactly one):
- Automate: AI acts without human review. Appropriate for low-stakes, high-reversibility, well-understood decisions.
- Augment: AI provides a recommendation; a human approves or rejects before action. Appropriate for moderate stakes or when human context is important.
- Supervise: Human makes the decision with AI providing supporting information only. Appropriate for high-stakes, hard-to-reverse, or accountability-sensitive decisions.

Tier heuristics (starting point, not a rule):
- Sense (perception/monitoring): often Automate if stakes are low
- Interpret (analysis/prediction): usually Augment
- Act (automation of decisions or actions): default to Supervise unless the action is trivially reversible
- Learn (model retraining/adaptation): usually Augment — humans should validate drift before deployment

Your output must be structured as three lines:
SUGGESTED_LEVEL: <Automate|Augment|Supervise>
RATIONALE: <2–3 sentence explanation grounded in the capability and initiative context>
DISPLAY: <The full message to show the executive, in second person, referencing the capability by name and explaining the rationale concisely. End with: "You can choose a different level if your context calls for it.">

Never invent facts not in the intake summary. If the intake summary is incomplete, reason from the capability tier and general principles."""


def advise(
    capability_name: str,
    capability_tier: str,
    intake_summary: dict,
    capability_input: str = "",
    capability_output: str = "",
) -> dict:
    """Return {suggested_level, rationale, display_message}."""
    tier_lower = capability_tier.lower()
    tier_default = TIER_DEFAULTS.get(tier_lower, "Augment")

    intake_text = "\n".join(
        f"- {k}: {v}" for k, v in intake_summary.items()
    )

    io_section = ""
    if capability_input or capability_output:
        io_section = "\nCapability I/O (as described by the executive):"
        if capability_input:
            io_section += f"\n- Input: {capability_input}"
        if capability_output:
            io_section += f"\n- Expected output: {capability_output}"
        io_section += "\n"

    user_prompt = f"""Initiative context (from intake interview):
{intake_text}
{io_section}
The executive is designing an AI capability called "{capability_name}" (tier: {capability_tier}).
The baseline heuristic for this tier is {tier_default}.

Recommend the most appropriate oversight level for this specific capability in this specific context. Consider:
1. The stakes of an incorrect decision — especially given the expected output
2. How easily errors in the output can be detected and reversed
3. Who bears accountability if the AI produces a wrong output
4. Whether the expected output implies autonomous action, human review, or advisory use

Provide your structured output."""

    response = _client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    text = response.content[0].text
    result = {"suggested_level": tier_default, "rationale": "", "display_message": ""}

    for line in text.strip().splitlines():
        if line.startswith("SUGGESTED_LEVEL:"):
            val = line.split(":", 1)[1].strip()
            if val in ("Automate", "Augment", "Supervise"):
                result["suggested_level"] = val
        elif line.startswith("RATIONALE:"):
            result["rationale"] = line.split(":", 1)[1].strip()
        elif line.startswith("DISPLAY:"):
            result["display_message"] = line.split(":", 1)[1].strip()

    # Fallback if DISPLAY not parsed cleanly (multi-line)
    if not result["display_message"] and "DISPLAY:" in text:
        result["display_message"] = text.split("DISPLAY:", 1)[1].strip()

    return result
