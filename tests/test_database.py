import datetime
import os
import unittest

import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from data_factory.config import SQL_DIR
from data_factory.db import make_engine, run_sql_file
from data_factory.destinations.postgres import PostgresDestination

TEST_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://olist_user:olist_pass@localhost:5432/olist_test",
)
SQL_FILES = ["001_schemas.sql", "002_tables.sql", "003_views.sql",
             "004_functions.sql", "005_procedures.sql"]


def make_key(prefix):
    return prefix.ljust(32, "x")


def build_test_schema(engine):
    with engine.begin() as connection:
        connection.exec_driver_sql("DROP SCHEMA IF EXISTS olist CASCADE")
        connection.exec_driver_sql("DROP SCHEMA IF EXISTS stage1 CASCADE")
    for file_name in SQL_FILES:
        run_sql_file(engine, SQL_DIR / file_name)


def insert_fixture(engine):
    day = datetime.datetime
    with engine.begin() as connection:
        connection.execute(text(
            "INSERT INTO olist.category_translation VALUES ('cat_a', 'Category A')"))
        connection.execute(text(
            "INSERT INTO olist.customers VALUES (:id, :uid, '01001', 'sao paulo', 'SP')"),
            {"id": make_key("c1"), "uid": make_key("u1")})
        connection.execute(text(
            "INSERT INTO olist.sellers VALUES (:id, '01001', 'sao paulo', 'SP')"),
            {"id": make_key("s1")})
        connection.execute(text(
            "INSERT INTO olist.products (product_id, product_category_name) "
            "VALUES (:id, 'cat_a')"), {"id": make_key("p1")})
        orders = [
            ("o1", "delivered", day(2017, 11, 5), day(2017, 11, 20), day(2017, 11, 25)),
            ("o2", "delivered", day(2017, 11, 10), day(2017, 11, 30), day(2017, 11, 28)),
            ("o3", "canceled", day(2017, 11, 12), day(2017, 11, 30), None),
        ]
        for key, status, purchased, estimated, delivered in orders:
            connection.execute(text(
                "INSERT INTO olist.orders (order_id, customer_id, order_status, "
                "order_purchase_timestamp, order_estimated_delivery_date, "
                "order_delivered_customer_date) "
                "VALUES (:id, :customer, :status, :purchased, :estimated, :delivered)"),
                {"id": make_key(key), "customer": make_key("c1"), "status": status,
                 "purchased": purchased, "estimated": estimated, "delivered": delivered})
        for key, price in [("o1", 100), ("o2", 50), ("o3", 70)]:
            connection.execute(text(
                "INSERT INTO olist.order_items VALUES (:order, 1, :product, :seller, "
                "NULL, :price, 10)"),
                {"order": make_key(key), "product": make_key("p1"),
                 "seller": make_key("s1"), "price": price})


class DatabaseLayerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = make_engine(TEST_URL)
        build_test_schema(cls.engine)
        insert_fixture(cls.engine)

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def scalar(self, sql, params=None):
        with self.engine.connect() as connection:
            return connection.execute(text(sql), params or {}).scalar_one()

    def test_delay_function_returns_days(self):
        value = self.scalar(
            "SELECT olist.delivery_delay_days(:delivered, :estimated)",
            {"delivered": datetime.datetime(2017, 11, 25),
             "estimated": datetime.datetime(2017, 11, 20)})
        self.assertEqual(float(value), 5.0)

    def test_delay_function_returns_null_when_not_delivered(self):
        value = self.scalar(
            "SELECT olist.delivery_delay_days(NULL, :estimated)",
            {"estimated": datetime.datetime(2017, 11, 20)})
        self.assertIsNone(value)

    def test_procedure_builds_expected_snapshot(self):
        with self.engine.begin() as connection:
            connection.execute(text("CALL olist.rebuild_monthly_snapshot(:month)"),
                               {"month": datetime.date(2017, 11, 1)})
        row = self.scalar(
            "SELECT total_sales || '/' || order_count || '/' || avg_order_value "
            "FROM olist.monthly_category_snapshot")
        self.assertEqual(row, "150.00/2/75.00")

    def test_procedure_is_idempotent(self):
        for _ in range(2):
            with self.engine.begin() as connection:
                connection.execute(text("CALL olist.rebuild_monthly_snapshot(:month)"),
                                   {"month": datetime.date(2017, 11, 1)})
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM olist.monthly_category_snapshot"), 1)

    def test_view_returns_only_delivered_orders(self):
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM olist.v_delivered_orders"), 2)

    def test_foreign_key_rejects_orphan_item(self):
        with self.assertRaises(IntegrityError):
            with self.engine.begin() as connection:
                connection.execute(text(
                    "INSERT INTO olist.order_items VALUES (:order, 9, :product, :seller, "
                    "NULL, 5, 1)"),
                    {"order": make_key("missing"), "product": make_key("p1"),
                     "seller": make_key("s1")})

    def test_check_constraint_rejects_negative_price(self):
        with self.assertRaises(IntegrityError):
            with self.engine.begin() as connection:
                connection.execute(text(
                    "INSERT INTO olist.order_items VALUES (:order, 8, :product, :seller, "
                    "NULL, -1, 1)"),
                    {"order": make_key("o1"), "product": make_key("p1"),
                     "seller": make_key("s1")})

    def test_write_clean_twice_adds_rows_once(self):
        destination = PostgresDestination(self.engine)
        frame = pd.DataFrame({
            "customer_id": [make_key("c9")], "customer_unique_id": [make_key("u9")],
            "customer_zip_code_prefix": ["02002"], "customer_city": ["rio"],
            "customer_state": ["RJ"],
        })
        before = destination.count_rows("customers")
        destination.write_clean("customers", frame)
        destination.write_clean("customers", frame)
        self.assertEqual(destination.count_rows("customers"), before + 1)


if __name__ == "__main__":
    unittest.main()
