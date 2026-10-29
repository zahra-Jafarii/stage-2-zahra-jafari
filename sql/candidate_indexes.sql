-- Candidate indexes. Each one is built, measured and dropped in solution.ipynb.
-- Do not put a semicolon inside a comment, the notebook splits this file on semicolons.

CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON olist.order_items (product_id);

CREATE INDEX IF NOT EXISTS idx_order_items_seller_cover ON olist.order_items (seller_id) INCLUDE (price);

CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON olist.orders (customer_id);

CREATE INDEX IF NOT EXISTS idx_orders_purchase_ts ON olist.orders (order_purchase_timestamp);

CREATE INDEX IF NOT EXISTS idx_order_reviews_order_id ON olist.order_reviews (order_id);

CREATE INDEX IF NOT EXISTS idx_order_payments_type_installments ON olist.order_payments (payment_type, payment_installments) INCLUDE (payment_value);
