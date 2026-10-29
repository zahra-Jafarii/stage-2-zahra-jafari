CREATE TABLE IF NOT EXISTS olist.category_translation (
    product_category_name TEXT PRIMARY KEY,
    product_category_name_english TEXT
);

CREATE TABLE IF NOT EXISTS olist.customers (
    customer_id CHAR(32) PRIMARY KEY,
    customer_unique_id CHAR(32) NOT NULL,
    customer_zip_code_prefix CHAR(5) NOT NULL,
    customer_city TEXT NOT NULL,
    customer_state CHAR(2) NOT NULL
);

CREATE TABLE IF NOT EXISTS olist.sellers (
    seller_id CHAR(32) PRIMARY KEY,
    seller_zip_code_prefix CHAR(5) NOT NULL,
    seller_city TEXT NOT NULL,
    seller_state CHAR(2) NOT NULL
);

CREATE TABLE IF NOT EXISTS olist.products (
    product_id CHAR(32) PRIMARY KEY,
    product_category_name TEXT REFERENCES olist.category_translation (product_category_name),
    product_name_length SMALLINT CHECK (product_name_length >= 0),
    product_description_length INTEGER CHECK (product_description_length >= 0),
    product_photos_qty SMALLINT CHECK (product_photos_qty >= 0),
    product_weight_g INTEGER CHECK (product_weight_g >= 0),
    product_length_cm SMALLINT CHECK (product_length_cm >= 0),
    product_height_cm SMALLINT CHECK (product_height_cm >= 0),
    product_width_cm SMALLINT CHECK (product_width_cm >= 0)
);

CREATE TABLE IF NOT EXISTS olist.orders (
    order_id CHAR(32) PRIMARY KEY,
    customer_id CHAR(32) NOT NULL REFERENCES olist.customers (customer_id),
    order_status TEXT NOT NULL CHECK (order_status IN (
        'created', 'approved', 'invoiced', 'processing',
        'shipped', 'delivered', 'unavailable', 'canceled')),
    order_purchase_timestamp TIMESTAMP NOT NULL,
    order_approved_at TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS olist.order_items (
    order_id CHAR(32) NOT NULL REFERENCES olist.orders (order_id),
    order_item_id SMALLINT NOT NULL,
    product_id CHAR(32) NOT NULL REFERENCES olist.products (product_id),
    seller_id CHAR(32) NOT NULL REFERENCES olist.sellers (seller_id),
    shipping_limit_date TIMESTAMP,
    price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    freight_value NUMERIC(10, 2) NOT NULL CHECK (freight_value >= 0),
    PRIMARY KEY (order_id, order_item_id)
);

CREATE TABLE IF NOT EXISTS olist.order_payments (
    order_id CHAR(32) NOT NULL REFERENCES olist.orders (order_id),
    payment_sequential SMALLINT NOT NULL,
    payment_type TEXT NOT NULL,
    payment_installments SMALLINT NOT NULL CHECK (payment_installments >= 0),
    payment_value NUMERIC(10, 2) NOT NULL CHECK (payment_value >= 0),
    PRIMARY KEY (order_id, payment_sequential)
);

CREATE TABLE IF NOT EXISTS olist.order_reviews (
    review_id CHAR(32) NOT NULL,
    order_id CHAR(32) NOT NULL REFERENCES olist.orders (order_id),
    review_score SMALLINT NOT NULL CHECK (review_score BETWEEN 1 AND 5),
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date TIMESTAMP,
    review_answer_timestamp TIMESTAMP,
    PRIMARY KEY (review_id, order_id)
);

CREATE TABLE IF NOT EXISTS olist.geolocation (
    geolocation_zip_code_prefix CHAR(5) PRIMARY KEY,
    avg_lat DOUBLE PRECISION NOT NULL,
    avg_lng DOUBLE PRECISION NOT NULL,
    point_count INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS olist.quarantine (
    quarantine_id BIGSERIAL PRIMARY KEY,
    source_table TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    raw_record JSONB NOT NULL,
    record_hash CHAR(32) NOT NULL,
    quarantined_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source_table, reason_code, record_hash)
);

CREATE TABLE IF NOT EXISTS olist.benchmark_results (
    query_name TEXT NOT NULL,
    variant TEXT NOT NULL,
    median_ms NUMERIC(10, 2) NOT NULL,
    PRIMARY KEY (query_name, variant)
);