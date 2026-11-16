SELECT
    payment_type,
    payment_installments,
    COUNT(*) AS payments,
    ROUND(AVG(payment_value), 2) AS avg_payment_value,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS share_percent
FROM olist.order_payments
GROUP BY 1, 2
ORDER BY 1, 2;
