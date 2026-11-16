"""Contracts, preparation and the whole load through the stage 1 factory (csv destination)."""
import re
import tempfile
import unittest
from pathlib import Path

import pandas as pd
from nyc311_factory.contract import check_contract

from data_factory.config import SQL_DIR
from data_factory.contracts import ALL_TABLES, FOREIGN_KEYS, TABLE_SPECS
from data_factory.keys import folder_key_provider
from data_factory.olist_datasets import (
    TABLE_DEFINITIONS, build_contract, quarantine_table_sql,
)
from data_factory.olist_load import load_all, summary_row
from data_factory.prepare import (
    aggregate_geolocation, copy_with_new_header, find_missing_categories, prepare_inputs,
)

SQL_KEYWORDS = {"primary", "unique", "check", "foreign", "constraint"}

RAW_FILES = {
    "product_category_name_translation.csv":
        "product_category_name,product_category_name_english\ncat_a,Category A\n",
    "olist_customers_dataset.csv":
        "customer_id,customer_unique_id,customer_zip_code_prefix,customer_city,customer_state\n"
        "c1,u1,01001,sao paulo,SP\nc2,u2,01002,rio,RJ\n",
    "olist_sellers_dataset.csv":
        "seller_id,seller_zip_code_prefix,seller_city,seller_state\ns1,01001,sao paulo,SP\n",
    "olist_products_dataset.csv":
        "product_id,product_category_name,product_name_lenght,product_description_lenght,"
        "product_photos_qty,product_weight_g,product_length_cm,product_height_cm,product_width_cm\n"
        "p1,cat_a,10,100,1,500,10,10,10\np2,cat_missing,,,,,,,\n",
    "olist_orders_dataset.csv":
        "order_id,customer_id,order_status,order_purchase_timestamp,order_approved_at,"
        "order_delivered_carrier_date,order_delivered_customer_date,order_estimated_delivery_date\n"
        "o1,c1,delivered,2017-01-01 10:00:00,2017-01-01 11:00:00,2017-01-02 10:00:00,"
        "2017-01-05 10:00:00,2017-01-10 00:00:00\n"
        "o2,c2,shipped,2017-01-02 10:00:00,,,,2017-01-12 00:00:00\n"
        "o3,c9,delivered,2017-01-03 10:00:00,,,,2017-01-13 00:00:00\n",
    "olist_order_items_dataset.csv":
        "order_id,order_item_id,product_id,seller_id,shipping_limit_date,price,freight_value\n"
        "o1,1,p1,s1,2017-01-03 10:00:00,100,10\n"
        "o1,2,p1,s1,2017-01-03 10:00:00,100,10\n"
        "o2,1,p2,s1,2017-01-04 10:00:00,50,5\n"
        "o9,1,p1,s1,2017-01-04 10:00:00,70,7\n"
        "o1,1,p1,s1,2017-01-03 10:00:00,100,10\n"
        "o2,2,p9,s1,2017-01-04 10:00:00,30,3\n",
    "olist_order_payments_dataset.csv":
        "order_id,payment_sequential,payment_type,payment_installments,payment_value\n"
        "o1,1,credit_card,2,210\no9,1,boleto,1,70\n",
    "olist_order_reviews_dataset.csv":
        "review_id,order_id,review_score,review_comment_title,review_comment_message,"
        "review_creation_date,review_answer_timestamp\n"
        "r1,o1,5,,great,2017-01-06 00:00:00,2017-01-07 00:00:00\n"
        "r1,o2,1,,,2017-01-06 00:00:00,2017-01-07 00:00:00\n"
        "r2,o9,3,,,2017-01-06 00:00:00,2017-01-07 00:00:00\n"
        "r3,o1,7,,,2017-01-06 00:00:00,2017-01-07 00:00:00\n",
    "olist_geolocation_dataset.csv":
        "geolocation_zip_code_prefix,geolocation_lat,geolocation_lng,geolocation_city,"
        "geolocation_state\n01001,-23.0,-46.0,sao paulo,SP\n01001,-24.0,-47.0,sao paulo,SP\n"
        "01002,-22.0,-43.0,rio,RJ\n",
}


def write_raw_files(folder):
    for name, content in RAW_FILES.items():
        (Path(folder) / name).write_text(content, encoding="utf-8")


class ContractTest(unittest.TestCase):
    def test_every_contract_is_consistent(self):
        for table in TABLE_DEFINITIONS:
            check_contract(build_contract(table))

    def test_foreign_keys_become_row_rules(self):
        provider = lambda table, column: {"x"}
        for table, rules in FOREIGN_KEYS.items():
            self.assertEqual(len(build_contract(table, provider).row_rules), len(rules))

    def test_database_tables_and_contracts_have_the_same_columns(self):
        ddl = (SQL_DIR / "002_tables.sql").read_text(encoding="utf-8")
        for table, (columns, _) in TABLE_DEFINITIONS.items():
            block = re.search(rf"olist\.{table} \((.*?)\n\);", ddl, re.S).group(1)
            candidates = re.findall(r"^    ([a-z][a-z0-9_]*) ", block, re.M)
            names = {name for name in candidates if name not in SQL_KEYWORDS}
            self.assertEqual(names, {column.name for column in columns}, table)

    def test_quarantine_tables_file_matches_the_contracts(self):
        text = (SQL_DIR / "002_quarantine_tables.sql").read_text(encoding="utf-8")
        self.assertIn(quarantine_table_sql(), text)


class PrepareTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.raw = self.root / "raw"
        self.raw.mkdir()
        write_raw_files(self.raw)

    def test_header_rename_leaves_the_values_alone(self):
        source = self.raw / TABLE_SPECS["products"]["file"]
        target = self.root / "products.csv"
        copy_with_new_header(source, target, TABLE_SPECS["products"]["rename"])
        old_lines = source.read_text(encoding="utf-8").splitlines()
        new_lines = target.read_text(encoding="utf-8").splitlines()
        self.assertIn("product_name_length", new_lines[0])
        self.assertNotIn("lenght", new_lines[0])
        self.assertEqual(old_lines[1:], new_lines[1:])

    def test_missing_category_is_found(self):
        self.assertEqual(find_missing_categories(self.raw), ["cat_missing"])

    def test_geolocation_is_averaged_per_zip(self):
        chunks = pd.read_csv(self.raw / "olist_geolocation_dataset.csv", dtype=str, chunksize=2)
        result = aggregate_geolocation(chunks).set_index("geolocation_zip_code_prefix")
        self.assertEqual(result.loc["01001", "avg_lat"], -23.5)
        self.assertEqual(int(result.loc["01001", "point_count"]), 2)

    def test_prepared_inputs_cover_every_table(self):
        prepared = prepare_inputs(self.raw, self.root / "work")
        self.assertEqual(set(prepared.paths), set(ALL_TABLES))
        self.assertEqual(prepared.missing_categories_added, 1)
        self.assertEqual(prepared.geolocation_raw_points, 3)


class LoadThroughFactoryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        raw = self.root / "raw"
        raw.mkdir()
        write_raw_files(raw)
        self.curated = self.root / "curated"
        self.prepared = prepare_inputs(raw, self.root / "work")

    def run_load(self):
        return load_all(self.prepared, folder_key_provider(self.curated), self.curated,
                        destinations=("csv",), threshold=0.9)

    def row(self, summary, table):
        return summary[summary["table"] == table].iloc[0]

    def test_orphans_are_quarantined_with_fk_codes(self):
        summary = self.run_load()
        self.assertEqual(self.row(summary, "orders")["reasons"], {"FK_customer_id_customers": 1})
        self.assertEqual(self.row(summary, "order_payments")["reasons"],
                         {"FK_order_id_orders": 1})
        items = self.row(summary, "order_items")
        self.assertEqual(items["reasons"], {"FK_order_id_orders": 1, "DUPLICATE_KEY": 1,
                                            "FK_product_id_products": 1})

    def test_composite_keys_keep_several_items_of_one_order(self):
        summary = self.run_load()
        self.assertEqual(self.row(summary, "order_items")["inserted"], 3)
        self.assertEqual(self.row(summary, "order_reviews")["inserted"], 2)  # same review id twice

    def test_invalid_value_and_orphan_in_reviews(self):
        reasons = self.row(self.run_load(), "order_reviews")["reasons"]
        self.assertEqual(reasons, {"FK_order_id_orders": 1, "INVALID_REVIEW_SCORE": 1})

    def test_missing_category_lets_the_product_pass(self):
        summary = self.run_load()
        self.assertEqual(self.row(summary, "products")["quarantined"], 0)
        self.assertEqual(self.row(summary, "category_translation")["inserted"], 2)

    def test_every_table_has_its_own_manifest(self):
        self.run_load()
        for table in ALL_TABLES:
            self.assertTrue((self.curated / table / "manifest_run.json").is_file(), table)

    def test_second_run_gives_the_same_result(self):
        first = self.run_load().drop(columns=["reasons"])
        second = self.run_load().drop(columns=["reasons"])
        pd.testing.assert_frame_equal(first, second)

    def test_summary_row_counts_match_manifest(self):
        manifest = {"records": {"raw": 10, "passed": 8, "quarantined_rows": 2,
                                "quarantine_by_reason": {"X": 2}}}
        row = summary_row("t", manifest)
        self.assertEqual((row["read"], row["inserted"], row["quarantine_ratio"]), (10, 8, 0.2))


if __name__ == "__main__":
    unittest.main()
