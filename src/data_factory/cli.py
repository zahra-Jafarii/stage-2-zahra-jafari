import argparse
from pathlib import Path

from data_factory.config import RAW_DIR, SCHEMA, SQL_DIR, WORK_DIR
from data_factory.contracts import ALL_TABLES
from data_factory.db import make_engine, run_sql_file, truncate_tables
from data_factory.keys import database_key_provider
from data_factory.olist_load import load_all, write_summary
from data_factory.prepare import prepare_inputs

STRUCTURE_FILES = ["001_schemas.sql", "002_tables.sql", "002_quarantine_tables.sql",
                   "002_benchmark_tables.sql"]
LOGIC_FILES = ["003_views.sql", "004_functions.sql", "005_procedures.sql"]
INDEX_FILE = "006_indexes.sql"


def run_sql_files(engine, file_names, sql_dir=SQL_DIR):
    for file_name in file_names:
        run_sql_file(engine, Path(sql_dir) / file_name)


def reset_database(engine):
    with engine.begin() as connection:
        connection.exec_driver_sql(f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE")


def vacuum_analyze(engine):
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        connection.exec_driver_sql("VACUUM ANALYZE")


def empty_data_tables(engine):
    """Full refresh: a repeated run ends in the same state and never duplicates rows."""
    names = ALL_TABLES + [f"{name}_quarantine" for name in ALL_TABLES]
    truncate_tables(engine, SCHEMA, names)


def build_database(engine=None, with_indexes=True, raw_dir=None, work_dir=None):
    """Empty PostgreSQL -> tables, data (through the stage 1 factory), views, indexes."""
    own_engine = engine is None
    engine = engine or make_engine()
    raw_dir = Path(raw_dir or RAW_DIR)
    work_dir = Path(work_dir or WORK_DIR)
    try:
        run_sql_files(engine, STRUCTURE_FILES)
        prepared = prepare_inputs(raw_dir, work_dir / "prepared")
        empty_data_tables(engine)
        summary = load_all(prepared, database_key_provider(engine, SCHEMA),
                           work_dir / "olist", engine=engine)
        write_summary(summary, work_dir / "olist" / "load_summary.json")
        run_sql_files(engine, LOGIC_FILES)
        if with_indexes:
            run_sql_files(engine, [INDEX_FILE])
        vacuum_analyze(engine)
        return summary
    finally:
        if own_engine:
            engine.dispose()


def load_stage1_output(config_path, engine=None, **overrides):
    """Send the stage 1 (NYC 311) result to the database through the stage 1 package."""
    from nyc311_factory.config import load_config, with_overrides
    from nyc311_factory.pipeline import run_pipeline

    config = with_overrides(load_config(str(config_path)), **overrides)
    return run_pipeline(config, engine=engine)


def build_parser():
    parser = argparse.ArgumentParser(prog="data_factory")
    parser.add_argument("--raw-dir", help="folder with the Olist csv files")
    parser.add_argument("--work-dir", help="folder for prepared files and manifests")
    parser.add_argument("--stage1-config", help="stage 1 config; its output goes to the database")
    return parser


def main():
    args = build_parser().parse_args()
    summary = build_database(raw_dir=args.raw_dir, work_dir=args.work_dir)
    print(summary.drop(columns=["reasons"]).to_string(index=False))
    print("missing categories added:", summary.attrs["missing_categories_added"])
    if args.stage1_config:
        manifest = load_stage1_output(args.stage1_config)
        print("stage 1 records:", manifest["records"])


if __name__ == "__main__":
    main()
