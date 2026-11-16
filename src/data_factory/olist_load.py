"""Load the Olist tables one by one through the stage 1 factory."""
import json
from pathlib import Path

import pandas as pd
from nyc311_factory.config import Config
from nyc311_factory.pipeline import run_pipeline

from data_factory.config import CHUNK_SIZE, QUARANTINE_THRESHOLD, SCHEMA
from data_factory.contracts import ALL_TABLES
from data_factory.olist_datasets import build_dataset

SUMMARY_COLUMNS = ["table", "read", "inserted", "quarantined", "quarantine_ratio", "reasons"]


def table_config(table, input_path, curated_root, schema=SCHEMA, destinations=("database",),
                 mode="existing", threshold=QUARANTINE_THRESHOLD):
    """One factory config per table; each table keeps its own manifest folder."""
    return Config(
        quarantine_threshold=threshold,
        curated_dir=str(Path(curated_root) / table),
        dataset=table,
        source_type="csv",
        input_path=str(input_path),
        destinations=tuple(destinations),
        page_size=CHUNK_SIZE,
        database_schema=schema,
        database_load_mode=mode,
    )


def summary_row(table, manifest):
    records = manifest["records"]
    raw = records["raw"]
    return {
        "table": table,
        "read": raw,
        "inserted": records["passed"],
        "quarantined": records["quarantined_rows"],
        "quarantine_ratio": round(records["quarantined_rows"] / raw, 5) if raw else 0.0,
        "reasons": records["quarantine_by_reason"],
    }


def load_table(table, input_path, key_provider, curated_root, engine=None, **settings):
    """Run the factory for one table and return its manifest."""
    config = table_config(table, input_path, curated_root, **settings)
    return run_pipeline(config, dataset=build_dataset(table, key_provider), engine=engine)


def load_all(prepared, key_provider, curated_root, engine=None, **settings):
    """Load every table in dependency order; parents are published before children."""
    rows = []
    for table in ALL_TABLES:
        manifest = load_table(table, prepared.paths[table], key_provider, curated_root,
                              engine=engine, **settings)
        rows.append(summary_row(table, manifest))
    summary = pd.DataFrame(rows, columns=SUMMARY_COLUMNS)
    summary.attrs["missing_categories_added"] = prepared.missing_categories_added
    summary.attrs["geolocation_raw_points"] = prepared.geolocation_raw_points
    return summary


def write_summary(summary, path):
    """Keep the load summary next to the per-table manifests."""
    content = {
        "tables": json.loads(summary.to_json(orient="records")),
        "missing_categories_added": summary.attrs.get("missing_categories_added"),
        "geolocation_raw_points": summary.attrs.get("geolocation_raw_points"),
    }
    Path(path).write_text(json.dumps(content, indent=2, ensure_ascii=False), encoding="utf-8")
