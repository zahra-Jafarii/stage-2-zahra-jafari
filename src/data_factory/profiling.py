import pandas as pd

from data_factory.contracts import TABLE_SPECS
from data_factory.loader import read_raw_chunks

PRIMARY_KEYS = {
    "category_translation": ["product_category_name"],
    "customers": ["customer_id"],
    "sellers": ["seller_id"],
    "products": ["product_id"],
    "orders": ["order_id"],
    "order_items": ["order_id", "order_item_id"],
    "order_payments": ["order_id", "payment_sequential"],
    "order_reviews": ["review_id", "order_id"],
}


def iter_renamed_chunks(raw_dir, table_name):
    spec = TABLE_SPECS[table_name]
    for chunk in read_raw_chunks(raw_dir, spec["file"]):
        yield chunk.rename(columns=spec["rename"])


def collect_values(raw_dir, table_name, column):
    values = set()
    for chunk in iter_renamed_chunks(raw_dir, table_name):
        values |= set(chunk[column].dropna())
    return values


def count_orphans(raw_dir, table_name, column, parent_table, parent_column):
    parent_values = collect_values(raw_dir, parent_table, parent_column)
    orphan_count = 0
    for chunk in iter_renamed_chunks(raw_dir, table_name):
        child_values = chunk[column].dropna()
        orphan_count += int((~child_values.isin(parent_values)).sum())
    return orphan_count


def count_duplicate_keys(raw_dir, table_name, key_columns):
    keys = pd.concat(
        [chunk[key_columns] for chunk in iter_renamed_chunks(raw_dir, table_name)]
    )
    return int(keys.duplicated().sum())


def count_nulls(raw_dir, table_name):
    totals = None
    for chunk in iter_renamed_chunks(raw_dir, table_name):
        counts = chunk.isna().sum()
        totals = counts if totals is None else totals + counts
    return totals
