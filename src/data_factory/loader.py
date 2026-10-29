from collections import Counter

import pandas as pd

from data_factory.config import CHUNK_SIZE, QUARANTINE_THRESHOLD
from data_factory.contracts import (
    ALLOWED_VALUES, FOREIGN_KEYS, LOAD_ORDER, MIN_VALUES,
    NOT_NULL_COLUMNS, TABLE_SPECS,
)
from data_factory.transform import (
    aggregate_geolocation, apply_rules, prepare_chunk, rule_in_keys,
    rule_in_set, rule_min_value, rule_not_null,
)


class QuarantineThresholdExceeded(RuntimeError):
    pass


def read_raw_chunks(raw_dir, file_name, chunk_size=CHUNK_SIZE):
    return pd.read_csv(raw_dir / file_name, dtype=str, chunksize=chunk_size)


def build_rules(table_name, destination):
    rules = [rule_not_null(column) for column in NOT_NULL_COLUMNS.get(table_name, [])]
    for column, allowed in ALLOWED_VALUES.get(table_name, {}).items():
        rules.append(rule_in_set(column, allowed))
    for column, minimum in MIN_VALUES.get(table_name, {}).items():
        rules.append(rule_min_value(column, minimum))
    for column, parent_table, parent_column in FOREIGN_KEYS.get(table_name, []):
        parent_keys = destination.read_keys(parent_table, parent_column)
        rules.append(rule_in_keys(column, parent_keys, parent_table))
    return rules


def register_missing_categories(destination, raw_dir):
    known = destination.read_keys("category_translation", "product_category_name")
    used = set()
    for chunk in read_raw_chunks(raw_dir, TABLE_SPECS["products"]["file"]):
        used |= set(chunk["product_category_name"].dropna().unique())
    missing = sorted(used - known)
    if missing:
        frame = pd.DataFrame({
            "product_category_name": missing,
            "product_category_name_english": [None] * len(missing),
        })
        destination.write_clean("category_translation", frame)
    return len(missing)


def check_threshold(table_name, rows_read, rows_quarantined, threshold):
    ratio = rows_quarantined / rows_read if rows_read else 0.0
    if ratio > threshold:
        raise QuarantineThresholdExceeded(
            f"{table_name}: quarantine ratio {ratio:.4f} exceeds {threshold}"
        )
    return ratio


def load_table(destination, table_name, raw_dir, threshold=QUARANTINE_THRESHOLD):
    spec = TABLE_SPECS[table_name]
    rules = build_rules(table_name, destination)
    rows_before = destination.count_rows(table_name)
    rows_read = 0
    rows_quarantined = 0
    reason_counts = Counter()

    for raw_chunk in read_raw_chunks(raw_dir, spec["file"]):
        chunk = prepare_chunk(raw_chunk, spec)
        clean, quarantined = apply_rules(chunk, rules)
        destination.write_clean(table_name, clean)
        destination.write_quarantine(table_name, quarantined)
        rows_read += len(chunk)
        rows_quarantined += len(quarantined)
        reason_counts.update(quarantined["reason_code"].value_counts().to_dict())

    ratio = check_threshold(table_name, rows_read, rows_quarantined, threshold)
    rows_inserted = destination.count_rows(table_name) - rows_before
    return {
        "table": table_name,
        "read": rows_read,
        "inserted": rows_inserted,
        "skipped": rows_read - rows_quarantined - rows_inserted,
        "quarantined": rows_quarantined,
        "quarantine_ratio": round(ratio, 5),
        "reasons": dict(reason_counts),
    }


def load_geolocation(destination, raw_dir):
    chunks = read_raw_chunks(raw_dir, "olist_geolocation_dataset.csv")
    aggregated = aggregate_geolocation(chunks)
    rows_before = destination.count_rows("geolocation")
    destination.write_clean("geolocation", aggregated)
    return {
        "table": "geolocation",
        "read": int(aggregated["point_count"].sum()),
        "inserted": destination.count_rows("geolocation") - rows_before,
        "skipped": 0,
        "quarantined": 0,
        "quarantine_ratio": 0.0,
        "reasons": {},
    }


def load_all(destination, raw_dir):
    summaries = []
    missing_categories_added = 0
    for table_name in LOAD_ORDER:
        if table_name == "products":
            missing_categories_added = register_missing_categories(destination, raw_dir)
        summaries.append(load_table(destination, table_name, raw_dir))
    summaries.append(load_geolocation(destination, raw_dir))
    summary = pd.DataFrame(summaries)
    summary.attrs["missing_categories_added"] = missing_categories_added
    return summary
