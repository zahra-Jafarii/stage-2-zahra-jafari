import pandas as pd


def parse_dates(chunk, date_columns):
    for column in date_columns:
        chunk[column] = pd.to_datetime(chunk[column], errors="coerce")
    return chunk


def parse_numbers(chunk, number_columns):
    for column in number_columns:
        chunk[column] = pd.to_numeric(chunk[column], errors="coerce")
    return chunk


def parse_integers(chunk, integer_columns):
    for column in integer_columns:
        chunk[column] = pd.to_numeric(chunk[column], errors="coerce").astype("Int64")
    return chunk


def prepare_chunk(chunk, spec):
    chunk = chunk.rename(columns=spec["rename"])
    chunk = parse_dates(chunk, spec["dates"])
    chunk = parse_numbers(chunk, spec["numbers"])
    return parse_integers(chunk, spec["integers"])


def to_python_nulls(frame):
    return frame.astype(object).where(frame.notna(), None)


def rule_not_null(column):
    return f"NULL_{column}", lambda chunk: chunk[column].notna()


def rule_in_set(column, allowed_values):
    return f"DOMAIN_{column}", lambda chunk: chunk[column].isin(allowed_values)


def rule_min_value(column, minimum):
    return f"MIN_{column}", lambda chunk: chunk[column] >= minimum


def rule_in_keys(column, valid_keys, parent_table):
    return f"FK_{column}_{parent_table}", lambda chunk: chunk[column].isin(valid_keys)


def apply_rules(chunk, rules):
    quarantined_parts = []
    for reason_code, is_valid in rules:
        valid_mask = is_valid(chunk).fillna(False)
        if not valid_mask.all():
            quarantined_parts.append(chunk[~valid_mask].assign(reason_code=reason_code))
            chunk = chunk[valid_mask]
    if quarantined_parts:
        return chunk, pd.concat(quarantined_parts)
    return chunk, chunk.iloc[0:0].assign(reason_code=pd.Series(dtype=str))


def aggregate_geolocation(chunks):
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