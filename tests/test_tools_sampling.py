import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODEBASE = os.path.join(ROOT, "codebase")
if CODEBASE not in sys.path:
    sys.path.insert(0, CODEBASE)

import tools


class ReviewSamplingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.temp.name, "reviews.json")
        counts = {1: 10, 2: 20, 3: 30, 4: 40, 5: 30}
        reviews = []
        for stars, count in counts.items():
            for index in range(count):
                reviews.append({
                    "review_id": f"R{stars}-{index:03}",
                    "phone_model": "iPhone 15 Pro",
                    "case_variant": "Ốp trong suốt viền đen",
                    "stars": stars,
                    "text": "Fixture review",
                })
        data = {"version": "sampling-test", "products": [{
            "product_id": "p1",
            "product_url": "https://shopee.vn/fixture-bactrung-case-clear-001",
            "title": "Sampling fixture",
            "reviews": reviews,
        }]}
        with open(self.path, "w", encoding="utf-8") as output:
            json.dump(data, output, ensure_ascii=False)
        self.path_patch = patch.object(tools, "DATA_PATH", self.path)
        self.path_patch.start()

    def tearDown(self):
        self.path_patch.stop()
        self.temp.cleanup()

    def request(self, limit=100, seed=42):
        return tools.get_product_reviews(
            "https://shopee.vn/fixture-bactrung-case-clear-001",
            "iPhone 15 Pro",
            "Ốp trong suốt viền đen",
            limit=limit,
            seed=seed,
        )

    def test_analysis_sample_cap_is_100_and_preserves_each_observed_star_group(self):
        result = self.request()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["sample_limit"], 100)
        self.assertEqual(len(result["reviews"]), 100)
        self.assertEqual(set(result["sampled_star_counts"]), {"1", "2", "3", "4", "5"})
        self.assertEqual(self.request()["reviews"], result["reviews"])

    def test_sample_limit_over_100_is_rejected_instead_of_silently_clamped(self):
        result = self.request(limit=101)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["code"], "INVALID_INPUT")


if __name__ == "__main__":
    unittest.main()
