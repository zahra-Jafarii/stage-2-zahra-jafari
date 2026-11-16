-- Quarantine tables of the stage 1 factory (one per table). Rejected rows keep every
-- source column as text plus the reason codes joined with a vertical bar.
-- Generated from olist_datasets.py; tests/test_olist_datasets.py keeps the two in sync.

CREATE TABLE IF NOT EXISTS olist.category_translation_quarantine (
    product_category_name TEXT,
    product_category_name_english TEXT,
    reason_codes TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS olist.customers_quarantine (
    customer_id TEXT,
    customer_unique_id TEXT,
    customer_zip_code_prefix TEXT,
    customer_city TEXT,
    customer_state TEXT,
    reason_codes TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS olist.sellers_quarantine (
    seller_id TEXT,
    seller_zip_code_prefix TEXT,
    seller_city TEXT,
    seller_state TEXT,
    reason_codes TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS olist.products_quarantine (
    product_id TEXT,
    product_category_name TEXT,
    product_name_length TEXT,
    product_description_length TEXT,
    product_photos_qty TEXT,
    product_weight_g TEXT,
    product_length_cm TEXT,
    product_height_cm TEXT,
    product_width_cm TEXT,
    reason_codes TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS olist.orders_quarantine (
    order_id TEXT,
    customer_id TEXT,
    order_status TEXT,
    order_purchase_timestamp TEXT,
    order_approved_at TEXT,
    order_delivered_carrier_date TEXT,
    order_delivered_customer_date TEXT,
    order_estimated_delivery_date TEXT,
    reason_codes TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS olist.order_items_quarantine (
    order_id TEXT,
    order_item_id TEXT,
    product_id TEXT,
    seller_id TEXT,
    shipping_limit_date TEXT,
    price TEXT,
    freight_value TEXT,
    reason_codes TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS olist.order_payments_quarantine (
    order_id TEXT,
    payment_sequential TEXT,
    payment_type TEXT,
    payment_installments TEXT,
    payment_value TEXT,
    reason_codes TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS olist.order_reviews_quarantine (
    review_id TEXT,
    order_id TEXT,
    review_score TEXT,
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date TEXT,
    review_answer_timestamp TEXT,
    reason_codes TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS olist.geolocation_quarantine (
    geolocation_zip_code_prefix TEXT,
    avg_lat TEXT,
    avg_lng TEXT,
    point_count TEXT,
    reason_codes TEXT NOT NULL
);
