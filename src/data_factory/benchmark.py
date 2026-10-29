import re
import statistics
import time

import pandas as pd
from sqlalchemy import text

from data_factory.config import SQL_DIR

BUDGET_MS = 200
EXECUTION_PATTERN = re.compile(r"Execution Time: ([\d.]+) ms")
SEQ_SCAN_PATTERN = re.compile(r"Seq Scan on (\w+)")
INDEX_SCAN_PATTERN = re.compile(r"Index (?:Only )?Scan(?: Backward)? using (\w+)")


def load_query(file_name):
    return (SQL_DIR / "queries" / file_name).read_text(encoding="utf-8")


def time_query(engine, sql, params=None, warmup_runs=2, timed_runs=9):
    durations_ms = []
    with engine.connect() as connection:
        for run_index in range(warmup_runs + timed_runs):
            started = time.perf_counter()
            connection.execute(text(sql), params or {}).fetchall()
            elapsed_ms = (time.perf_counter() - started) * 1000
            if run_index >= warmup_runs:
                durations_ms.append(elapsed_ms)
    median_ms = statistics.median(durations_ms)
    return {
        "median_ms": round(median_ms, 2),
        "min_ms": round(min(durations_ms), 2),
        "max_ms": round(max(durations_ms), 2),
        "spread_percent": round((max(durations_ms) - min(durations_ms)) / median_ms * 100, 1),
    }


def explain_analyze(engine, sql, params=None):
    explain_sql = f"EXPLAIN (ANALYZE, BUFFERS) {sql}"
    with engine.connect() as connection:
        rows = connection.execute(text(explain_sql), params or {})
        return "\n".join(row[0] for row in rows)


def plan_execution_ms(plan_text):
    match = EXECUTION_PATTERN.search(plan_text)
    return float(match.group(1)) if match else None


def plan_uses_index(plan_text, index_name):
    return index_name in INDEX_SCAN_PATTERN.findall(plan_text)


def run_step(engine, query_name, step_label, sql_text, params=None, index_name=None):
    timing = time_query(engine, sql_text, params)
    plan_text = explain_analyze(engine, sql_text, params)
    return {
        "query": query_name,
        "step": step_label,
        "index_name": index_name,
        **timing,
        "execution_ms": plan_execution_ms(plan_text),
        "within_budget": timing["median_ms"] < BUDGET_MS,
        "seq_scans": ", ".join(sorted(set(SEQ_SCAN_PATTERN.findall(plan_text)))),
        "index_used": plan_uses_index(plan_text, index_name) if index_name else None,
        "plan": plan_text,
    }


SUMMARY_COLUMNS = [
    "query", "step", "index_name", "median_ms", "min_ms", "max_ms", "spread_percent",
    "execution_ms", "within_budget", "seq_scans", "index_used",
]


def summarize_steps(results):
    return pd.DataFrame(results)[SUMMARY_COLUMNS]
