
CREATE TABLE IF NOT EXISTS olist.benchmark_results (
    query_name TEXT NOT NULL,
    variant TEXT NOT NULL,
    median_ms NUMERIC(10, 2) NOT NULL,
    PRIMARY KEY (query_name, variant)
);
