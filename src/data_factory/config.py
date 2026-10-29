import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "raw"
SQL_DIR = PROJECT_ROOT / "sql"

RANDOM_SEED = 42
CHUNK_SIZE = 20_000
QUARANTINE_THRESHOLD = 0.05

DEFAULT_DATABASE_URL = "postgresql+psycopg2://olist_user:olist_pass@localhost:5432/olist"


def get_database_url():
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)