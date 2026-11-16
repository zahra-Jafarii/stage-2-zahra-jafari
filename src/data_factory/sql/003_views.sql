-- Simple view: hides the delivered-order filter.
CREATE OR REPLACE VIEW olist.v_delivered_orders AS
SELECT *
FROM olist.orders
WHERE order_status = 'delivered'
  AND order_delivered_customer_date IS NOT NULL;

-- Multi-table view: one place for the repeated order, item, product and category joins.
CREATE OR REPLACE VIEW olist.v_order_items_enriched AS
SELECT
    o.order_id,
    o.order_status,
    o.order_purchase_timestamp,
    c.customer_state,
    i.order_item_id,
    i.seller_id,
    i.product_id,
    i.price,
    i.freight_value,
    COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') AS category
FROM olist.orders o
JOIN olist.customers c ON c.customer_id = o.customer_id
JOIN olist.order_items i ON i.order_id = o.order_id
JOIN olist.products p ON p.product_id = i.product_id
LEFT JOIN olist.category_translation t ON t.product_category_name = p.product_category_name;

-- One place to read every quarantined row: source table, reason codes and the row as JSON.
CREATE OR REPLACE VIEW olist.v_quarantine AS
SELECT 'category_translation' AS source_table, reason_codes, to_jsonb(q) - 'reason_codes' AS raw_record FROM olist.category_translation_quarantine q
UNION ALL
SELECT 'customers' AS source_table, reason_codes, to_jsonb(q) - 'reason_codes' AS raw_record FROM olist.customers_quarantine q
UNION ALL
SELECT 'sellers' AS source_table, reason_codes, to_jsonb(q) - 'reason_codes' AS raw_record FROM olist.sellers_quarantine q
UNION ALL
SELECT 'products' AS source_table, reason_codes, to_jsonb(q) - 'reason_codes' AS raw_record FROM olist.products_quarantine q
UNION ALL
SELECT 'orders' AS source_table, reason_codes, to_jsonb(q) - 'reason_codes' AS raw_record FROM olist.orders_quarantine q
UNION ALL
SELECT 'order_items' AS source_table, reason_codes, to_jsonb(q) - 'reason_codes' AS raw_record FROM olist.order_items_quarantine q
UNION ALL
SELECT 'order_payments' AS source_table, reason_codes, to_jsonb(q) - 'reason_codes' AS raw_record FROM olist.order_payments_quarantine q
UNION ALL
SELECT 'order_reviews' AS source_table, reason_codes, to_jsonb(q) - 'reason_codes' AS raw_record FROM olist.order_reviews_quarantine q
UNION ALL
SELECT 'geolocation' AS source_table, reason_codes, to_jsonb(q) - 'reason_codes' AS raw_record FROM olist.geolocation_quarantine q;
