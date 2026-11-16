"""Facts about the Olist files and how the tables point at each other.

Validation rules (types, not-null, domains) live in olist_datasets.py as
stage 1 contracts. This file only describes files and relationships.
"""
TABLE_SPECS = {
    "category_translation": {"file": "product_category_name_translation.csv", "rename": {}},
    "customers": {"file": "olist_customers_dataset.csv", "rename": {}},
    "sellers": {"file": "olist_sellers_dataset.csv", "rename": {}},
    "products": {
        "file": "olist_products_dataset.csv",
        "rename": {
            "product_name_lenght": "product_name_length",
            "product_description_lenght": "product_description_length",
        },
    },
    "orders": {"file": "olist_orders_dataset.csv", "rename": {}},
    "order_items": {"file": "olist_order_items_dataset.csv", "rename": {}},
    "order_payments": {"file": "olist_order_payments_dataset.csv", "rename": {}},
    "order_reviews": {"file": "olist_order_reviews_dataset.csv", "rename": {}},
}

GEOLOCATION_FILE = "olist_geolocation_dataset.csv"

LOAD_ORDER = [
    "category_translation", "customers", "sellers", "products",
    "orders", "order_items", "order_payments", "order_reviews",
]

# every table the loader fills, in dependency order (geolocation has no parent)
ALL_TABLES = LOAD_ORDER + ["geolocation"]

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
