# AItelier · Agentic System — RQ3

> **6 agents · 3 experimental arms · claude-sonnet-4-6**
> A controlled field experiment on AI governance decision-making among executive teams.

---

## Agent Flow Map

```mermaid
flowchart TD
    P("👤 **Participant**\nOpens canvas via session link\nArm assigned: MD5·session_id· % 3")

    P --> I

    subgraph PRE["⬜ PRE-TREATMENT · All arms"]
        I("💬 **Intake Agent**\nMulti-turn scoping interview\n3–8 turns · max 1024 tokens\nOutputs: intake_summary JSON")
    end

    I -->|intake_summary| O

    O("⚙️ **Orchestrator**\nDeterministic router — no LLM\nReads session.arm from DB\nImmutable after first assignment")

    O --> G{{"Arm?"}}

    G -->|T1 · Reactive| ARM1
    G -->|T2 · AI Suggests| ARM2
    G -->|T3 · AI Challenges| ARM3
    G -->|All arms · all pages| MOD

    subgraph MOD_LANE["🟤 MODERATOR · Ambient · All arms"]
        MOD("🎓 **Moderator Agent**\nProfessor avatar on all 4 pages\nFires on: page_load · phase_change\nfield_complete · canvas_complete\nmax 120 tokens\nSets timers · cues team members")
    end

    subgraph T1_LANE["🟢 T1 · Reactive only"]
        ARM1("🔇 **No AI Active**\nExecutive sets oversight\nwithout proactive AI input")
        ARM1 --> AG1
        AG1("💬 **Reactive Agent**\nAnswers only if asked directly\nNever suggests · never challenges\nmax 400 tokens\n\nDV: agent.queried rate")
        AG1 --> CV1("📋 **Canvas — T1**\nAll 10 fields\nF6 oversight set unaided")
    end

    subgraph T2_LANE["🔵 T2 · AI Suggests"]
        ARM2("💡 **Oversight Advisor active**\nFires after F5 capability selection\nbefore F6 is set")
        ARM2 --> AG2
        AG2("🧭 **Oversight Advisor**\nSuggests Automate / Augment / Supervise\nbased on capability tier + context\nmax 512 tokens\n\nTier logic:\nsense→Automate · interpret→Augment\nact→Supervise · learn→Augment")
        AG2 -->|suggest before F6| CV2("📋 **Canvas — T2**\nF5→Advisor fires→Accept/Override→F6\n\nDV: accepted_suggestion")
    end

    subgraph T3_LANE["🔴 T3 · AI Challenges"]
        ARM3("⚡ **Decision Challenger active**\nFires after F6 oversight is set\nbefore confirmation")
        ARM3 --> AG3
        AG3("🔍 **Decision Challenger**\nSurfaces failure scenario\nAsks: who is accountable?\nmax 300 tokens · 1 paragraph\n\n'If this fails for 3 months\nundetected — who owns it?'")
        AG3 -->|challenge after F6| CV3("📋 **Canvas — T3**\nF6 set→Challenger fires→Reconsider/Confirm\n\nDV: revised_after_challenge")
    end

    MOD -->|phase cues · timers| CV1
    MOD -->|phase cues · timers| CV2
    MOD -->|phase cues · timers| CV3

    CV1 --> DONE
    CV2 --> DONE
    CV3 --> DONE

    DONE("✓ **Canvas Complete**\n10/10 fields submitted\nOutcome events logged")

    DONE -->|canvas_state + intake_summary| RPT

    subgraph SYNTH["⬜ SYNTHESIS · All arms"]
        RPT("📄 **Report Generator**\nSynthesises canvas + intake → Blueprint\nStrips agent suggestions + arm label\nmax 2048 tokens\n\nOutputs: readiness_score 0–5\nred/amber/green recommendations")
    end

    RPT --> BP("📑 **AI Decision Blueprint**\nblueprint.html\nInitiative overview · Capability stack\nOversight design · Governance\nReadiness score")

    RPT --> SV("📊 **Post-Session Survey**\nsurvey.html\nQ1 Confidence · Q2 Advice-seeking\nQ3 Delegation · Q4 Implementation\nQ5 Open reflection")

    MOD -->|page cues| BP
    MOD -->|page cues| SV

    style PRE fill:#f0f0f8,stroke:#9896b8,stroke-width:1.5px
    style MOD_LANE fill:#fdf5e6,stroke:#7a4a00,stroke-width:1.5px
    style T1_LANE fill:#f0faf0,stroke:#276b2a,stroke-width:1.5px
    style T2_LANE fill:#f0f4ff,stroke:#14569e,stroke-width:1.5px
    style T3_LANE fill:#fff5f5,stroke:#b52222,stroke-width:1.5px
    style SYNTH fill:#f5f0ff,stroke:#5a3d9e,stroke-width:1.5px
```

---

## Agent Specifications

| # | Agent | File | Arm | Trigger | Max Tokens | Primary Output |
|---|-------|------|-----|---------|-----------|----------------|
| 1 | **Intake** | `agents/intake.py` | All | Pre-canvas · conversation start | 1 024 | `intake_summary` JSON |
| 2 | **Reactive** | `agents/reactive.py` | T1 only | Executive asks a question | 400 | Direct answer |
| 3 | **Oversight Advisor** | `agents/rq3_oversight_advisor.py` | T2 only | F5 capability selected | 512 | `{suggested_level, rationale, display_message}` |
| 4 | **Decision Challenger** | `agents/rq3_decision_challenger.py` | T3 only | F6 oversight level set | 300 | Challenge paragraph |
| 5 | **Moderator** | `agents/moderator.py` | All | page_load · phase_change · field_complete · canvas_complete | 120 | `{message, cue_member?, timer_minutes?}` |
| 6 | **Report Generator** | `agents/report_generator.py` | All | Canvas complete · first blueprint load | 2 048 | Blueprint JSON |

---

## RCT Design

| Arm | Treatment | Agent fires when | Primary DV |
|-----|-----------|-----------------|------------|
| **T1** | Reactive AI only | Executive explicitly asks | `agent.queried` rate |
| **T2** | AI suggests oversight level | After F5 capability selected, before F6 set | `accepted_suggestion` (boolean) |
| **T3** | AI challenges oversight choice | After F6 level set, before confirmation | `revised_after_challenge` (boolean) |

**Arm assignment** — deterministic: `MD5(session_id) % 3 → T1 | T2 | T3`
**Arm isolation** — guidance endpoints return `403` if the session's arm doesn't match.

---

## Key System Prompts

### Intake Agent
> *"Before we open your canvas — tell me about the AI initiative you're here to design. What business problem are you solving, and which team or data would be involved?"*
> Gathers: `problem · domain · data_type · team_size · industry · implementer_roles`
> Never mentions: canvas fields · oversight levels · experimental arms

### Reactive Agent (T1)
> **Absolute constraints:** never suggest an oversight level · never challenge a decision · never volunteer opinions · respond only when explicitly asked · one paragraph maximum

### Oversight Advisor (T2)
> Tier defaults: `sense → Automate` · `interpret → Augment` · `act → Supervise` · `learn → Augment`
> Output format: `SUGGESTED_LEVEL: / RATIONALE: / DISPLAY:`

### Decision Challenger (T3)
> *"You've chosen [level] for [capability]. Before confirming — if this produces a systematic error for 3 months before anyone notices, who is responsible and what's the remediation path? Does that change your choice?"*
> Format: exactly one paragraph · 3–5 sentences · second person · no headers

### Moderator Agent
> *"1–2 sentences maximum. Direct, warm, intellectually sharp. Never lecture — facilitate. Never mention technology explicitly — focus on decisions and accountability."*
> Cue logic: `MD5(page + trigger + phase + fields_done) % len(team_members)` — deterministic

### Report Generator
> **Critical:** Blueprint reflects only participant's own field values — no agent suggestions, no treatment arm label. Outputs `readiness_score 0–5` + `red/amber/green` recommendations.

---

## Canvas Fields

| Phase | Field | Description |
|-------|-------|-------------|
| 1 — Inputs & Context | F0 | Initiative Scope |
| | F1 | Data Inputs |
| | F2 | Human Inputs |
| | F3 | Systems & Infrastructure |
| | F4 | Tacit Constraints |
| 2 — AI Capabilities | F5 | Capability Type ← **T2/T3 intervention point** |
| | F6 | Per-capability Oversight Chains ← **T2/T3 intervention point** |
| 3 — Decision & Oversight | F7 | Feedback Loops |
| | F8 | Business Outcomes & KPIs |
| 4 — Governance | F9 | Governance & Accountability |

---

## Files

```
backend/
  agents/
    intake.py                    # Agent 1 — pre-treatment scoping
    reactive.py                  # Agent 2 — T1 reactive Q&A
    rq3_oversight_advisor.py     # Agent 3 — T2 oversight suggestion
    rq3_decision_challenger.py   # Agent 4 — T3 adversarial challenge
    moderator.py                 # Agent 5 — ambient professor facilitator
    report_generator.py          # Agent 6 — blueprint synthesis
  routers/
    guidance.py                  # Agent hub — intake + arm-specific endpoints
    moderator.py                 # POST /api/moderator/message
    blueprint.py                 # GET /api/blueprint/{session_id}
    sessions.py / canvas.py / events.py / survey.py

frontend/
  moderator.js                   # Moderator IIFE — injected on all 4 pages
  index.html / canvas.html / blueprint.html / survey.html
  config.js                      # window.AITELIER_API

docs/
  README.md                      # This file
  agent-map.html                 # Interactive zoomable map (open locally)
  agents.html                    # Full API + prompt reference
```
