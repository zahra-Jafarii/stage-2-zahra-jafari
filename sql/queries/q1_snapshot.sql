SELECT
    month_start,
    category_name AS category,
    SUM(total_sales) AS total_sales,
    SUM(order_count) AS order_count,
    ROUND(SUM(total_sales) / SUM(order_count), 2) AS avg_order_value
FROM olist.monthly_category_snapshot
GROUP BY 1, 2
ORDER BY 1, 2;
