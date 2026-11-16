WITH monthly AS (
    SELECT
        date_trunc('month', order_purchase_timestamp)::date AS month_start,
        category,
        customer_state,
        SUM(price) AS total_sales,
        COUNT(DISTINCT order_id) AS order_count
    FROM olist.v_order_items_enriched
    WHERE order_status <> 'canceled'
    GROUP BY 1, 2, 3
)
SELECT
    month_start,
    category,
    customer_state,
    total_sales,
    order_count,
    SUM(total_sales) OVER (
        PARTITION BY category, customer_state
        ORDER BY month_start
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS rolling_3_month_sales
FROM monthly
ORDER BY category, customer_state, month_start;
