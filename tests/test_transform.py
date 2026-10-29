import unittest

import pandas as pd

from data_factory.transform import apply_rules, rule_in_keys, rule_min_value


class ApplyRulesTest(unittest.TestCase):
    def setUp(self):
        self.chunk = pd.DataFrame({
            "order_id": ["a", "b", "c"],
            "price": [10.0, -5.0, 20.0],
        })

    def test_negative_price_is_quarantined(self):
        clean, quarantined = apply_rules(self.chunk, [rule_min_value("price", 0)])
        self.assertEqual(list(clean["order_id"]), ["a", "c"])
        self.assertEqual(list(quarantined["reason_code"]), ["MIN_price"])

    def test_unknown_parent_key_is_quarantined(self):
        rules = [rule_in_keys("order_id", {"a", "b"}, "orders")]
        clean, quarantined = apply_rules(self.chunk, rules)
        self.assertEqual(list(quarantined["order_id"]), ["c"])

    def test_no_violation_gives_empty_quarantine(self):
        _, quarantined = apply_rules(self.chunk, [rule_min_value("price", -100)])
        self.assertTrue(quarantined.empty)


if __name__ == "__main__":
    unittest.main()
