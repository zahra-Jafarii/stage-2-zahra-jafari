import os
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
SQL_DIR = PACKAGE_DIR / "sql"

# defaults for running this project on its own; callers can pass their own folders
PROJECT_ROOT = PACKAGE_DIR.parents[1]
RAW_DIR = PROJECT_ROOT / "raw"
WORK_DIR = PROJECT_ROOT / "curated"

RANDOM_SEED = 42
CHUNK_SIZE = 20_000
QUARANTINE_THRESHOLD = 0.05
SCHEMA = "olist"

DEFAULT_DATABASE_URL = "postgresql+psycopg2://olist_user:olist_pass@localhost:5432/olist"


def get_database_url():
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
