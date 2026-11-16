"""Where the parent keys of a foreign key check come from."""
from pathlib import Path

import pandas as pd


def database_key_provider(engine, schema):
    """Read the keys of a table that an earlier run has already loaded."""
    cache = {}

    def provide(table_name, column_name):
        if (table_name, column_name) not in cache:
            cache[(table_name, column_name)] = read_keys(engine, schema, table_name, column_name)
        return cache[(table_name, column_name)]

    return provide


def read_keys(engine, schema, table_name, column_name):
    from sqlalchemy import column, select, table

    statement = select(column(column_name)).select_from(table(table_name, schema=schema))
    with engine.connect() as connection:
        return {str(row[0]).strip() for row in connection.execute(statement)}


def folder_key_provider(curated_root):
    """Read the keys from the cases.csv of an earlier run (csv destination)."""
    cache = {}

    def provide(table_name, column_name):
        if (table_name, column_name) not in cache:
            path = Path(curated_root) / table_name / "cases.csv"
            frame = pd.read_csv(path, usecols=[column_name], dtype=str, na_filter=False)
            cache[(table_name, column_name)] = set(frame[column_name].str.strip())
        return cache[(table_name, column_name)]

    return provide
