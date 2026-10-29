from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

from data_factory.config import get_database_url

APPLICATION_NAME = "data_factory"


def make_engine(database_url=None):
    return create_engine(
        database_url or get_database_url(),
        pool_pre_ping=True,
        connect_args={"application_name": APPLICATION_NAME},
    )


def has_statements(sql_text):
    lines = [line.strip() for line in sql_text.splitlines()]
    return any(line and not line.startswith("--") for line in lines)


def run_sql_file(engine, sql_path):
    sql_text = Path(sql_path).read_text(encoding="utf-8")
    if not has_statements(sql_text):
        return
    with engine.begin() as connection:
        connection.exec_driver_sql(sql_text)


def read_in_batches(engine, sql, params=None, batch_size=10_000):
    with engine.connect().execution_options(stream_results=True) as connection:
        yield from pd.read_sql_query(
            text(sql), connection, params=params, chunksize=batch_size
        )
