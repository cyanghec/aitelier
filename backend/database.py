import os
from sqlmodel import SQLModel, create_engine, Session, text

# DATA_DIR can be set to a persistent disk mount (e.g. /data on Render).
# Falls back to the backend directory for local development.
_data_dir = os.environ.get("DATA_DIR", os.path.dirname(__file__))
os.makedirs(_data_dir, exist_ok=True)
DB_PATH = os.path.join(_data_dir, "aitelier.db")
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    # Enable WAL mode for concurrent reads during writes
    with engine.connect() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL"))
        conn.commit()


def get_session():
    with Session(engine) as session:
        yield session
