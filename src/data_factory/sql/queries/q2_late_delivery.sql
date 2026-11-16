SELECT
    c.customer_state,
    date_trunc('month', o.order_purchase_timestamp)::date AS month_start,
    COUNT(*) AS delivered_orders,
    COUNT(*) FILTER (
        WHERE o.order_delivered_customer_date > o.order_estimated_delivery_date
    ) AS late_orders,
    ROUND(100.0 * COUNT(*) FILTER (
        WHERE o.order_delivered_customer_date > o.order_estimated_delivery_date
    ) / COUNT(*), 2) AS late_percent
FROM olist.orders o
JOIN olist.customers c ON c.customer_id = o.customer_id
WHERE o.order_delivered_customer_date IS NOT NULL
GROUP BY 1, 2
ORDER BY 1, 2;
