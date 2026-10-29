SELECT
    date_trunc('month', order_purchase_timestamp)::date AS month_start,
    category,
    SUM(price) AS total_sales,
    COUNT(DISTINCT order_id) AS order_count,
    ROUND(SUM(price) / COUNT(DISTINCT order_id), 2) AS avg_order_value
FROM olist.v_order_items_enriched
WHERE order_status <> 'canceled'
GROUP BY 1, 2
ORDER BY 1, 2;
