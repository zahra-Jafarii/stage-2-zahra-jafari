CREATE TABLE IF NOT EXISTS olist.monthly_category_snapshot (
    month_start DATE NOT NULL,
    category_name TEXT NOT NULL,
    customer_state CHAR(2) NOT NULL,
    total_sales NUMERIC(14, 2) NOT NULL,
    order_count INTEGER NOT NULL,
    avg_order_value NUMERIC(12, 2) NOT NULL,
    PRIMARY KEY (month_start, category_name, customer_state)
);

-- Rebuilds one month: delete and insert run inside the single CALL transaction,
-- so any error rolls both back and the previous snapshot of that month stays intact.
CREATE OR REPLACE PROCEDURE olist.rebuild_monthly_snapshot(target_month DATE)
LANGUAGE plpgsql
AS $$
DECLARE
    month_begin DATE;
BEGIN
    IF target_month IS NULL THEN
        RAISE EXCEPTION 'target_month must not be null';
    END IF;
    month_begin := date_trunc('month', target_month)::date;

    DELETE FROM olist.monthly_category_snapshot WHERE month_start = month_begin;

    INSERT INTO olist.monthly_category_snapshot
        (month_start, category_name, customer_state, total_sales, order_count, avg_order_value)
    SELECT
        month_begin,
        category,
        customer_state,
        SUM(price),
        COUNT(DISTINCT order_id),
        ROUND(SUM(price) / COUNT(DISTINCT order_id), 2)
    FROM olist.v_order_items_enriched
    WHERE order_status <> 'canceled'
      AND order_purchase_timestamp >= month_begin
      AND order_purchase_timestamp < month_begin + INTERVAL '1 month'
    GROUP BY category, customer_state;
END;
$$;
