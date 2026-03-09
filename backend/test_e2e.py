"""End-to-end test: intake → canvas save → T2 oversight advisor → blueprint"""
import os, json, sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env", override=True)

import urllib.request, urllib.error

BASE = "http://localhost:8000"

def api(method, path, body=None):
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        BASE + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req) as r:
            text = r.read().decode()
            return json.loads(text) if text else {}
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code}: {e.read().decode()[:300]}")
        sys.exit(1)

# ── 1. Create session ──────────────────────────────────────────────────────
print("1. Creating session...")
s = api("POST", "/api/sessions", {"participant_first": "Cathy", "participant_last": "Yang"})
SID, ARM = s["session_id"], s["arm"]
print(f"   ✓ {SID} | Arm: {ARM}")

# ── 2. Intake conversation ─────────────────────────────────────────────────
print("\n2. Intake agent...")
turns = [
    "We want to use AI to detect fraud in our payment processing system. We handle about 50k transactions per day across our e-commerce platform.",
    "Our industry is retail e-commerce. The reconciliation team is 12 people — fraud analysts and senior reviewers. We work with transaction logs, card metadata, and behavioural clickstream data.",
    "The main implementer roles would be fraud analysts, data engineers, and the compliance officer. The business problem is that manual review can't keep up — we miss about 3% of fraud cases and the false positive rate buries the team.",
]
for i, msg in enumerate(turns):
    r = api("POST", "/api/guidance/intake-message", {"session_id": SID, "message": msg})
    print(f"   Turn {i+1} — complete: {r['intake_complete']}")
    print(f"   Agent: {r['reply'][:120]}...")
    if r["intake_complete"]:
        print(f"   ✓ Intake summary: {json.dumps(r['intake_summary'], indent=4)}")
        break

# ── 3. Save canvas state ───────────────────────────────────────────────────
print("\n3. Saving canvas state...")
canvas = {
    "scope": "multi",
    "dataSources": [
        {"id": 1, "name": "Transaction logs", "owner": "Data Engineering", "format": "SQL · real-time"},
        {"id": 2, "name": "Card metadata feed", "owner": "Risk team", "format": "API · real-time"},
    ],
    "roles": ["Fraud Analyst", "Data Engineer", "Compliance Officer"],
    "fields": {
        "F3": "Existing fraud rules engine (cannot be replaced until Q4 2026). All AI flags must route through the ServiceNow review queue before action is taken.",
        "F4": "Senior analysts informally override the rules engine on weekend nights — the false positive rate spikes and they suppress alerts without logging it.",
        "F7-capture": "Weekly outcome tracking",
        "F7-cadence": "Monthly model review",
        "F8": "Reduce fraud losses by 40%. Reduce false positive review time by 60%. Compliance SLA: <2h response on flagged transactions.",
        "F9-owner": "Head of Fraud Operations",
        "F9-retrain": "Data Science Lead",
        "F9-shutdown": "Chief Risk Officer",
        "F9": "Model owner reviews performance weekly. Retrain authority held by Data Science Lead with compliance sign-off. Shutdown authority with CRO — triggered if precision drops below 85% for 3 consecutive days.",
    },
    "capabilities": ["Anomaly Detection", "Risk Scoring"],
    "chains": {
        "Anomaly Detection": {"tier": "sense", "input": "Transaction logs + behavioural data", "judgment": "Analyst reviews flagged transactions", "oversight": "Augment"},
        "Risk Scoring": {"tier": "interpret", "input": "Card metadata + transaction history", "judgment": "Senior analyst approves block decisions", "oversight": "Supervise"},
    },
    "sessionId": SID,
}
r = api("PUT", f"/api/canvas/{SID}", canvas)
print(f"   ✓ {r}")

# ── 4. Test T2 Oversight Advisor (only fires if arm=T2) ────────────────────
if ARM == "T2":
    print("\n4. Oversight Advisor (T2)...")
    r = api("POST", "/api/guidance/oversight-advisor", {
        "session_id": SID,
        "capability_name": "Anomaly Detection",
        "capability_tier": "sense",
    })
    print(f"   Suggested: {r['suggested_level']}")
    print(f"   Message: {r['display_message'][:200]}")
elif ARM == "T3":
    print("\n4. Decision Challenger (T3)...")
    r = api("POST", "/api/guidance/decision-challenger", {
        "session_id": SID,
        "capability_name": "Risk Scoring",
        "oversight_chosen": "Augment",
    })
    print(f"   Challenge: {r['challenge'][:200]}")
else:
    print(f"\n4. Arm is T1 — no agents fire (correct baseline behaviour)")

# ── 5. Complete canvas + generate blueprint ────────────────────────────────
print("\n5. Completing canvas...")
api("POST", f"/api/canvas/{SID}/complete")
print("   ✓ Canvas marked complete")

print("\n6. Generating blueprint (calls Claude)...")
bp = api("GET", f"/api/blueprint/{SID}")
print(f"   ✓ Title: {bp.get('initiative_title')}")
print(f"   ✓ Readiness score: {bp.get('readiness_score')}/5")
print(f"   ✓ Recommendations: {len(bp.get('recommendations', []))} items")
for rec in bp.get("recommendations", []):
    print(f"      [{rec['severity'].upper()}] {rec['message'][:80]}")

# ── 6. Submit survey ───────────────────────────────────────────────────────
print("\n7. Submitting survey...")
r = api("POST", f"/api/survey/{SID}", {"q1_confidence": 4, "q2_advice_seeking": 3, "q3_delegation": 4, "q4_implementation": 5, "open_reflection": "The tacit knowledge field was the hardest but most valuable."})
print(f"   ✓ {r}")

print("\n🎉 Full end-to-end test passed!")
