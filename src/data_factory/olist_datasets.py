"""Stage 1 contracts for the Olist tables, with foreign key checks as row rules."""
from nyc311_factory.contract import Column, Contract, check_contract
from nyc311_factory.dataset import Dataset
from nyc311_factory.rules import in_keys_rule

from data_factory.contracts import FOREIGN_KEYS

ORDER_STATUSES = frozenset({
    "created", "approved", "invoiced", "processing",
    "shipped", "delivered", "unavailable", "canceled",
})


def text(name, nullable=False):
    return Column(name, "str", nullable=nullable)


def whole(name, nullable=False, min_value=None, max_value=None):
    return Column(name, "int", nullable=nullable, min_value=min_value, max_value=max_value)


def decimal(name, nullable=False, min_value=None):
    return Column(name, "float", nullable=nullable, min_value=min_value)


def stamp(name, nullable=False):
    return Column(name, "datetime", nullable=nullable)


# table -> (columns, key columns); column order follows the database tables
TABLE_DEFINITIONS = {
    "category_translation": (
        (text("product_category_name"), text("product_category_name_english", True)),
        ("product_category_name",),
    ),
    "customers": (
        (text("customer_id"), text("customer_unique_id"), text("customer_zip_code_prefix"),
         text("customer_city"), text("customer_state")),
        ("customer_id",),
    ),
    "sellers": (
        (text("seller_id"), text("seller_zip_code_prefix"), text("seller_city"),
         text("seller_state")),
        ("seller_id",),
    ),
    "products": (
        (text("product_id"), text("product_category_name", True),
         whole("product_name_length", True, 0), whole("product_description_length", True, 0),
         whole("product_photos_qty", True, 0), whole("product_weight_g", True, 0),
         whole("product_length_cm", True, 0), whole("product_height_cm", True, 0),
         whole("product_width_cm", True, 0)),
        ("product_id",),
    ),
    "orders": (
        (text("order_id"), text("customer_id"),
         Column("order_status", "str", nullable=False, allowed=ORDER_STATUSES),
         stamp("order_purchase_timestamp"), stamp("order_approved_at", True),
         stamp("order_delivered_carrier_date", True),
         stamp("order_delivered_customer_date", True),
         stamp("order_estimated_delivery_date")),
        ("order_id",),
    ),
    "order_items": (
        (text("order_id"), whole("order_item_id"), text("product_id"), text("seller_id"),
         stamp("shipping_limit_date", True), decimal("price", min_value=0),
         decimal("freight_value", min_value=0)),
        ("order_id", "order_item_id"),
    ),
    "order_payments": (
        (text("order_id"), whole("payment_sequential"), text("payment_type"),
         whole("payment_installments", min_value=0), decimal("payment_value", min_value=0)),
        ("order_id", "payment_sequential"),
    ),
    "order_reviews": (
        (text("review_id"), text("order_id"), whole("review_score", min_value=1, max_value=5),
         text("review_comment_title", True), text("review_comment_message", True),
         stamp("review_creation_date", True), stamp("review_answer_timestamp", True)),
        ("review_id", "order_id"),
    ),
    "geolocation": (
        (text("geolocation_zip_code_prefix"), decimal("avg_lat"), decimal("avg_lng"),
         whole("point_count", min_value=1)),
        ("geolocation_zip_code_prefix",),
    ),
}


def reference_rules(table, key_provider):
    """One row rule per foreign key; parent keys come from `key_provider(table, column)`."""
    return tuple(
        in_keys_rule(column, key_provider(parent_table, parent_column),
                     f"FK_{column}_{parent_table}")
        for column, parent_table, parent_column in FOREIGN_KEYS.get(table, [])
    )


def build_contract(table, key_provider=None):
    columns, keys = TABLE_DEFINITIONS[table]
    names = tuple(column.name for column in columns)
    rules = reference_rules(table, key_provider) if key_provider else ()
    contract = Contract(
        name=table, source_columns=columns, derived_columns=(),
        key_column=keys[0], key_columns=keys,
        content_columns=names, required_columns=keys, row_rules=rules,
    )
    check_contract(contract)
    return contract


def build_dataset(table, key_provider=None):
    """A stage 1 Dataset; parent keys are read when the run starts, not before."""
    return Dataset(name=table, build_contract=lambda config: build_contract(table, key_provider))


def quarantine_table_sql(schema="olist"):
    """The quarantine tables the database destination expects in `existing` mode."""
    blocks = []
    for table in TABLE_DEFINITIONS:
        names = [column.name for column in TABLE_DEFINITIONS[table][0]]
        lines = ",\n".join(f"    {name} TEXT" for name in names)
        blocks.append(
            f"CREATE TABLE IF NOT EXISTS {schema}.{table}_quarantine (\n"
            f"{lines},\n    reason_codes TEXT NOT NULL\n);\n"
        )
    return "\n".join(blocks)
