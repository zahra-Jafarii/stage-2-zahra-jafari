SELECT
    month_start,
    category_name AS category,
    customer_state,
    total_sales,
    order_count,
    SUM(total_sales) OVER (
        PARTITION BY category_name, customer_state
        ORDER BY month_start
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS rolling_3_month_sales
FROM olist.monthly_category_snapshot
ORDER BY category_name, customer_state, month_start;
