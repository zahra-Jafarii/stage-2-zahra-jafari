TABLE_SPECS = {
    "category_translation": {
        "file": "product_category_name_translation.csv",
        "rename": {}, "dates": [], "numbers": [], "integers": [],
    },
    "customers": {
        "file": "olist_customers_dataset.csv",
        "rename": {}, "dates": [], "numbers": [], "integers": [],
    },
    "sellers": {
        "file": "olist_sellers_dataset.csv",
        "rename": {}, "dates": [], "numbers": [], "integers": [],
    },
    "products": {
        "file": "olist_products_dataset.csv",
        "rename": {
            "product_name_lenght": "product_name_length",
            "product_description_lenght": "product_description_length",
        },
        "dates": [], "numbers": [],
        "integers": [
            "product_name_length", "product_description_length",
            "product_photos_qty", "product_weight_g",
            "product_length_cm", "product_height_cm", "product_width_cm",
        ],
    },
    "orders": {
        "file": "olist_orders_dataset.csv",
        "rename": {},
        "dates": [
            "order_purchase_timestamp", "order_approved_at",
            "order_delivered_carrier_date", "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
        "numbers": [], "integers": [],
    },
    "order_items": {
        "file": "olist_order_items_dataset.csv",
        "rename": {}, "dates": ["shipping_limit_date"],
        "numbers": ["price", "freight_value"], "integers": ["order_item_id"],
    },
    "order_payments": {
        "file": "olist_order_payments_dataset.csv",
        "rename": {}, "dates": [],
        "numbers": ["payment_value"],
        "integers": ["payment_sequential", "payment_installments"],
    },
    "order_reviews": {
        "file": "olist_order_reviews_dataset.csv",
        "rename": {},
        "dates": ["review_creation_date", "review_answer_timestamp"],
        "numbers": [], "integers": ["review_score"],
    },
}

LOAD_ORDER = [
    "category_translation", "customers", "sellers", "products",
    "orders", "order_items", "order_payments", "order_reviews",
]

NOT_NULL_COLUMNS = {
    "customers": ["customer_id", "customer_unique_id", "customer_zip_code_prefix"],
    "sellers": ["seller_id", "seller_zip_code_prefix"],
    "products": ["product_id"],
    "orders": ["order_id", "customer_id", "order_purchase_timestamp",
               "order_estimated_delivery_date"],
    "order_items": ["order_id", "order_item_id", "product_id", "seller_id", "price"],
    "order_payments": ["order_id", "payment_sequential", "payment_value"],
    "order_reviews": ["review_id", "order_id", "review_score"],
}

ALLOWED_VALUES = {
    "orders": {"order_status": {
        "created", "approved", "invoiced", "processing",
        "shipped", "delivered", "unavailable", "canceled"}},
    "order_reviews": {"review_score": {1, 2, 3, 4, 5}},
}

MIN_VALUES = {
    "order_items": {"price": 0, "freight_value": 0},
    "order_payments": {"payment_value": 0, "payment_installments": 0},
}

FOREIGN_KEYS = {
    "orders": [("customer_id", "customers", "customer_id")],
    "order_items": [
        ("order_id", "orders", "order_id"),
        ("product_id", "products", "product_id"),
        ("seller_id", "sellers", "seller_id"),
    ],
    "order_payments": [("order_id", "orders", "order_id")],
    "order_reviews": [("order_id", "orders", "order_id")],
}