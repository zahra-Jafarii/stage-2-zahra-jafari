from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, func, select, table, text

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


def count_rows(engine, schema, table_name):
    statement = select(func.count()).select_from(table(table_name, schema=schema))
    with engine.connect() as connection:
        return connection.execute(statement).scalar_one()


def truncate_tables(engine, schema, table_names):
    """Empty several tables in one statement (tables that point at each other are fine)."""
    quote = engine.dialect.identifier_preparer.quote
    names = ", ".join(f"{quote(schema)}.{quote(name)}" for name in table_names)
    with engine.begin() as connection:
        connection.exec_driver_sql(f"TRUNCATE TABLE {names}")


def replace_frame(engine, frame, schema, table_name, dtype_map):
    """Replace the rows of a table with a DataFrame, using the column types you give."""
    quote = engine.dialect.identifier_preparer.quote
    with engine.begin() as connection:
        connection.exec_driver_sql(f"DELETE FROM {quote(schema)}.{quote(table_name)}")
        frame.to_sql(
            table_name, connection, schema=schema, if_exists="append",
            index=False, dtype=dtype_map, chunksize=5_000, method="multi",
        )
