# AItelier

A research platform for a randomised controlled field experiment (RQ3) testing three AI governance approaches in executive AI decision-making.

## Live Deployments

| Environment | URL | Purpose |
|---|---|---|
| **Production** | https://aitelier-demo.netlify.app | Participant-facing |
| **Test / Dev** | https://aitelier-test.netlify.app | Development & testing |
| **Backend API** | https://aitelier-tljf.onrender.com | FastAPI (Render, Starter plan) |

## RCT Design — Three Arms

| Arm | Label | Description |
|---|---|---|
| T1 | Reactive | AI available on demand, never proactively intervenes |
| T2 | Oversight Advisor | AI suggests oversight level before F6 capability chains |
| T3 | Decision Challenger | AI challenges final decisions after F6 capability chains |

Arm assignment is deterministic: `MD5(session_id) % 3`

### Test Links (one per arm)

| Arm | Session | Direct link |
|---|---|---|
| T1 | S-TU1203-BFA2 | https://aitelier-demo.netlify.app/canvas.html?session=S-TU1203-BFA2 |
| T2 | S-TU1203-78F9 | https://aitelier-demo.netlify.app/canvas.html?session=S-TU1203-78F9 |
| T3 | S-TU1203-4C48 | https://aitelier-demo.netlify.app/canvas.html?session=S-TU1203-4C48 |

New test sessions can be generated via:
```bash
curl -s -X POST https://aitelier-tljf.onrender.com/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"participant_first":"Test","participant_last":"User","rq":"RQ3"}'
```

## Participant Flow

```
index.html  →  canvas.html  →  blueprint.html  →  survey.html
  (intake)      (4 phases)      (AI blueprint)     (survey)
```

Session state is passed via URL `?session=` parameter and `sessionStorage`.

## Tech Stack

### Backend (FastAPI · Python 3.11)
- **Framework**: FastAPI 0.115.0
- **ORM**: SQLModel 0.0.21 + SQLite (persisted on Render disk at `/data`)
- **AI**: Anthropic Claude Sonnet 4.6 (`claude-sonnet-4-6`)
- **Server**: Uvicorn 0.30.6

### Frontend (Vanilla JS · Netlify)
- `index.html` — session intake & participant registration
- `canvas.html` — 4-phase AI governance canvas (F0–F9)
- `blueprint.html` — AI-generated governance blueprint
- `survey.html` — post-session survey
- `config.js` — sets `window.AITELIER_API`

## Project Structure

```
.
├── backend/
│   ├── agents/
│   │   ├── intake.py
│   │   ├── reactive.py                  # T1 arm
│   │   ├── rq3_oversight_advisor.py     # T2 arm
│   │   ├── rq3_decision_challenger.py   # T3 arm
│   │   └── report_generator.py
│   ├── routers/
│   │   ├── sessions.py
│   │   ├── events.py
│   │   ├── canvas.py
│   │   ├── guidance.py
│   │   ├── blueprint.py
│   │   └── survey.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── requirements.txt
│   └── .python-version        # pins Python 3.11.9 for Render
├── frontend/
│   ├── index.html
│   ├── canvas.html
│   ├── blueprint.html
│   ├── survey.html
│   └── config.js
├── netlify.toml               # publish = "frontend"
└── render.yaml                # rootDir: backend, disk: /data
```

## Local Development

### Backend
```bash
cd backend
pip install -r requirements.txt
echo "ANTHROPIC_API_KEY=sk-..." > .env
python -m uvicorn main:app --reload --port 8000
```

### Frontend
Open `frontend/index.html` via any HTTP server or directly in browser. `config.js` falls back to `http://localhost:8000` when `AITELIER_API` is empty.

## Git Branches

| Branch | Purpose |
|---|---|
| `main` | Production — auto-deploys to Render; deploy frontend with `netlify deploy --prod` |
| `staging` | Development — deploy frontend to `aitelier-test.netlify.app` |

## Key API Endpoints

```
POST /api/sessions                          Create session (assigns arm)
GET  /api/sessions/{id}                     Get session
POST /api/canvas/{id}                       Save canvas state
POST /api/guidance/reactive-query           T1: on-demand AI query
POST /api/guidance/oversight-advisor        T2: pre-F6 AI suggestion
POST /api/guidance/decision-challenger      T3: post-F6 AI challenge
POST /api/guidance/oversight-advisor-outcome   T2: log DV (accepted_suggestion)
POST /api/guidance/decision-challenger-outcome T3: log DV (revised_after_challenge)
POST /api/events                            Log any event
POST /api/survey/{id}                       Submit survey
GET  /health                                Health check
```

## Environment Variables

| Variable | Where | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Render → Environment | Required — Claude API key |

## Deployment

```bash
# Deploy to production (aitelier-demo.netlify.app)
netlify deploy --dir=frontend --site=fa7c3182-cfaa-44cb-820f-94e484c7b180 --prod

# Deploy to test (aitelier-test.netlify.app)
netlify deploy --dir=frontend --site=f2c1dc10-7ca4-4a25-9f63-9e236d4b7c2b --prod
```

Backend deploys automatically on push to `main` via Render's GitHub integration.
