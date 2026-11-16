SELECT
    date_trunc('month', o.order_purchase_timestamp)::date AS month_start,
    COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') AS category,
    SUM(i.price) AS total_sales,
    COUNT(DISTINCT o.order_id) AS order_count,
    ROUND(SUM(i.price) / COUNT(DISTINCT o.order_id), 2) AS avg_order_value
FROM olist.orders o
JOIN olist.order_items i ON i.order_id = o.order_id
JOIN olist.products p ON p.product_id = i.product_id
LEFT JOIN olist.category_translation t ON t.product_category_name = p.product_category_name
WHERE o.order_status <> 'canceled'
GROUP BY 1, 2
ORDER BY 1, 2;
