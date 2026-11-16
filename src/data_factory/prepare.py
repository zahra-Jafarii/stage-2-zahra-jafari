"""Small preparation steps that run before the stage 1 factory reads a file."""
import csv
import shutil
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from data_factory.config import CHUNK_SIZE
from data_factory.contracts import GEOLOCATION_FILE, TABLE_SPECS


@dataclass
class PreparedInputs:
    """Input file of every table, plus two facts the load summary reports."""
    paths: dict = field(default_factory=dict)
    missing_categories_added: int = 0
    geolocation_raw_points: int = 0


def read_raw_chunks(raw_dir, file_name, chunk_size=CHUNK_SIZE):
    return pd.read_csv(Path(raw_dir) / file_name, dtype=str, chunksize=chunk_size)


def copy_with_new_header(source, target, rename):
    """Copy a csv file; only the header line changes (values stay untouched)."""
    with open(source, newline="", encoding="utf-8-sig") as handle:
        header = next(csv.reader(handle))
    new_header = [rename.get(name, name) for name in header]
    with open(source, "rb") as src, open(target, "wb") as dst:
        src.readline()
        dst.write((",".join(new_header) + "\n").encode("utf-8"))
        shutil.copyfileobj(src, dst)


def find_missing_categories(raw_dir):
    """Categories used by products that the translation file does not list."""
    products = pd.read_csv(Path(raw_dir) / TABLE_SPECS["products"]["file"], dtype=str,
                           usecols=["product_category_name"])
    translation = pd.read_csv(Path(raw_dir) / TABLE_SPECS["category_translation"]["file"],
                              dtype=str, usecols=["product_category_name"])
    used = set(products["product_category_name"].dropna())
    return sorted(used - set(translation["product_category_name"].dropna()))


def prepare_translation(raw_dir, target, missing_categories):
    """Translation file plus the missing categories (English name left empty)."""
    source = Path(raw_dir) / TABLE_SPECS["category_translation"]["file"]
    frame = pd.read_csv(source, dtype=str, keep_default_na=False)
    extra = pd.DataFrame({
        "product_category_name": missing_categories,
        "product_category_name_english": [""] * len(missing_categories),
    })
    pd.concat([frame, extra], ignore_index=True).to_csv(target, index=False, encoding="utf-8")


def aggregate_geolocation(chunks):
    """Average latitude and longitude of all points of one zip prefix."""
    partial_sums = []
    for chunk in chunks:
        chunk["geolocation_lat"] = pd.to_numeric(chunk["geolocation_lat"], errors="coerce")
        chunk["geolocation_lng"] = pd.to_numeric(chunk["geolocation_lng"], errors="coerce")
        grouped = chunk.groupby("geolocation_zip_code_prefix").agg(
            lat_sum=("geolocation_lat", "sum"),
            lng_sum=("geolocation_lng", "sum"),
            point_count=("geolocation_lat", "size"),
        )
        partial_sums.append(grouped)
    total = pd.concat(partial_sums).groupby(level=0).sum()
    result = pd.DataFrame({
        "avg_lat": total["lat_sum"] / total["point_count"],
        "avg_lng": total["lng_sum"] / total["point_count"],
        "point_count": total["point_count"],
    })
    return result.reset_index()


def prepare_geolocation(raw_dir, target):
    """Write one row per zip prefix; returns the number of raw points."""
    aggregated = aggregate_geolocation(read_raw_chunks(raw_dir, GEOLOCATION_FILE))
    aggregated.to_csv(target, index=False, encoding="utf-8")
    return int(aggregated["point_count"].sum())


def prepare_inputs(raw_dir, work_dir):
    """Return the file the factory reads for each table."""
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    prepared = PreparedInputs()
    for table, spec in TABLE_SPECS.items():
        source = Path(raw_dir) / spec["file"]
        if spec["rename"]:
            target = work_dir / spec["file"]
            copy_with_new_header(source, target, spec["rename"])
            prepared.paths[table] = target
        else:
            prepared.paths[table] = source

    missing = find_missing_categories(raw_dir)
    translation_path = work_dir / TABLE_SPECS["category_translation"]["file"]
    prepare_translation(raw_dir, translation_path, missing)
    prepared.paths["category_translation"] = translation_path
    prepared.missing_categories_added = len(missing)

    geolocation_path = work_dir / "geolocation_by_zip.csv"
    prepared.geolocation_raw_points = prepare_geolocation(raw_dir, geolocation_path)
    prepared.paths["geolocation"] = geolocation_path
    return prepared
