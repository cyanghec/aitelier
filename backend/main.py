import os
from pathlib import Path
from dotenv import load_dotenv, dotenv_values

# Load from the .env next to this file, overriding any stale shell env vars
_env_path = Path(__file__).parent / ".env"
load_dotenv(_env_path, override=True)

# Verify the key loaded correctly at startup
_key = os.environ.get("ANTHROPIC_API_KEY", "")
if not _key:
    raise RuntimeError(f"ANTHROPIC_API_KEY not found. Checked: {_env_path}")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import create_db_and_tables
from routers import sessions, events, canvas, guidance, blueprint, survey

app = FastAPI(title="AItelier API", version="0.1.0")

# Allow the HTML files served from disk (or localhost:3000/5500) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten to specific origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(sessions.router)
app.include_router(events.router)
app.include_router(canvas.router)
app.include_router(guidance.router)
app.include_router(blueprint.router)
app.include_router(survey.router)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.get("/health")
def health():
    return {"status": "ok"}
