SELECT ROUND(corr(payment_installments, payment_value)::numeric, 4) AS installments_value_corr
FROM olist.order_payments;
