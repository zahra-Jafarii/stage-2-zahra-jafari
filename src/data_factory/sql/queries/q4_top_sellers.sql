WITH top_sellers AS (
    SELECT seller_id, SUM(price) AS revenue
    FROM olist.order_items
    GROUP BY seller_id
    ORDER BY revenue DESC
    LIMIT 20
),
seller_orders AS (
    SELECT DISTINCT i.seller_id, i.order_id
    FROM olist.order_items i
    JOIN top_sellers s ON s.seller_id = i.seller_id
)
SELECT
    s.seller_id,
    s.revenue,
    ROUND(AVG(EXTRACT(EPOCH FROM (
        o.order_delivered_carrier_date - o.order_approved_at)) / 86400.0)::numeric, 2
    ) AS avg_prep_days,
    ROUND(AVG(r.review_score), 2) AS avg_review_score
FROM top_sellers s
JOIN seller_orders so ON so.seller_id = s.seller_id
JOIN olist.orders o ON o.order_id = so.order_id
LEFT JOIN olist.order_reviews r ON r.order_id = o.order_id
GROUP BY s.seller_id, s.revenue
ORDER BY s.revenue DESC;
