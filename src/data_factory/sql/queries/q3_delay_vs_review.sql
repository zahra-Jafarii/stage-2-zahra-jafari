WITH order_review AS (
    SELECT order_id, AVG(review_score) AS review_score
    FROM olist.order_reviews
    GROUP BY order_id
),
delayed AS (
    SELECT
        o.order_id,
        olist.delivery_delay_days(
            o.order_delivered_customer_date, o.order_estimated_delivery_date
        ) AS delay_days
    FROM olist.orders o
    WHERE o.order_delivered_customer_date IS NOT NULL
)
SELECT
    CASE
        WHEN d.delay_days <= 0 THEN '1_on_time_or_early'
        WHEN d.delay_days <= 3 THEN '2_late_up_to_3_days'
        WHEN d.delay_days <= 7 THEN '3_late_3_to_7_days'
        WHEN d.delay_days <= 14 THEN '4_late_7_to_14_days'
        ELSE '5_late_over_14_days'
    END AS delay_bucket,
    COUNT(*) AS orders,
    ROUND(AVG(r.review_score), 3) AS avg_review_score
FROM delayed d
JOIN order_review r ON r.order_id = d.order_id
GROUP BY 1
ORDER BY 1;
