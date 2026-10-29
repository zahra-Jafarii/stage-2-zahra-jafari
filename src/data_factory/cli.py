from data_factory.config import RAW_DIR, SQL_DIR
from data_factory.db import make_engine, run_sql_file
from data_factory.destinations.postgres import PostgresDestination
from data_factory.loader import load_all

STRUCTURE_FILES = ["001_schemas.sql", "002_tables.sql", "002_benchmark_tables.sql"]
LOGIC_FILES = ["003_views.sql", "004_functions.sql", "005_procedures.sql"]
INDEX_FILE = "006_indexes.sql"


def run_sql_files(engine, file_names):
    for file_name in file_names:
        run_sql_file(engine, SQL_DIR / file_name)


def reset_database(engine):
    with engine.begin() as connection:
        connection.exec_driver_sql("DROP SCHEMA IF EXISTS olist CASCADE")


def vacuum_analyze(engine):
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        connection.exec_driver_sql("VACUUM ANALYZE")


def build_database(engine=None, with_indexes=True):
    own_engine = engine is None
    engine = engine or make_engine()
    try:
        run_sql_files(engine, STRUCTURE_FILES)
        destination = PostgresDestination(engine)
        summary = load_all(destination, RAW_DIR)
        run_sql_files(engine, LOGIC_FILES)
        if with_indexes:
            run_sql_files(engine, [INDEX_FILE])
        vacuum_analyze(engine)
        return summary
    finally:
        if own_engine:
            engine.dispose()


def main():
    summary = build_database()
    print(summary.to_string(index=False))
    print("missing categories added:", summary.attrs["missing_categories_added"])


if __name__ == "__main__":
    main()
