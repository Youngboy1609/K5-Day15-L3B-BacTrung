import csv
import tempfile
import unittest
from pathlib import Path

from shopee_collector.parsing import extract_payload
from shopee_collector.storage import Store


def product(item, totals):
    return {"product_key": f"1:{item}", "shop_id": "1", "source_kind": "product_page",
            "observed_at": "test", "star_counts": totals}


def reviews(item, star, count):
    return [{"review_key": f"1:{item}:{star}{i:03}", "product_key": f"1:{item}",
             "review_id": f"{star}{i:03}", "rating": star} for i in range(count)]


class SampleTests(unittest.TestCase):
    def test_sample_per_product_resume_and_legacy_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(tmp)
            try:
                legacy = reviews(2, 5, 20)
                store.ingest({"reviews": legacy})
                store.record_scope({"sample_reviews": True})
                totals = {"1": 0, "2": 19, "3": 99, "4": 100, "5": 2351}
                for item in (2, 3):
                    rows = [r for star in range(1, 6) for r in reviews(item, star, 110)]
                    rows.append(dict(rows[0], review_key=f"1:{item}:999", rating=None))
                    store.ingest({"products": [product(item, totals)], "reviews": rows + rows})
                    self.assertEqual([g["saved"] for g in store.sample_progress(f"1:{item}").values()],
                                     [0, 19, 99, 100, 100])
            finally:
                store.close()
            store = Store(tmp)
            try:
                self.assertTrue(store.sample_reviews)
                store.ingest({"products": [product(2, {"5": 1000})], "reviews": legacy})
                self.assertEqual(store.sample_progress("1:2")["5"], {"total": 2351, "target": 100, "saved": 100})
                self.assertEqual(store.export()["reviews_observed"], 636)
                with (Path(tmp) / "reviews.csv").open(encoding="utf-8-sig", newline="") as stream:
                    self.assertEqual(len(list(csv.DictReader(stream))), 636)
                store.record_scope({"sample_reviews": False})
                self.assertEqual(len(store.product_reviews("1:2")), 318)
            finally:
                store.close()

    def test_missing_or_inconsistent_totals(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(tmp)
            try:
                store.record_scope({"sample_reviews": True})
                item = {"shopid": 1, "itemid": 2, "name": "Demo", "item_rating": {"rating_count": [50, 0, 0, 0, 0, 17]}}
                store.ingest(extract_payload({"item": item}))
                self.assertEqual(store.ingest({"reviews": reviews(2, 5, 10)}), 10)
                self.assertEqual(store.sample_progress("1:2")["5"], {"total": None, "target": 100, "saved": 10})
                item["item_rating"]["rating_count"][0] = 17
                store.ingest(extract_payload({"item": item}))
                store.ingest({"reviews": reviews(2, 5, 30)})
                self.assertEqual(store.sample_progress("1:2")["5"], {"total": 17, "target": 17, "saved": 17})
            finally:
                store.close()

    def test_upgrade_percentage_sample_reuses_reviews_and_caps_large_groups(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(tmp)
            try:
                store.ingest({"reviews": [r for star in range(1, 6) for r in reviews(2, star, 130)]})
                with store.db:
                    store.put("run_settings", "sample_reviews", True)
                    store.db.execute("DELETE FROM entities WHERE kind='run_settings' AND key='reviews_per_star'")
                    for star in range(1, 6):
                        total = 1300 if star == 5 else 130
                        store.db.execute("INSERT INTO sample_targets VALUES('1:2',?,?)", (star, total))
                        store.db.executemany("INSERT INTO sample_members VALUES(?,'1:2',?)",
                                             [(r["review_key"], star) for r in reviews(2, star, total // 10)])
                store.enqueue("https://shopee.vn/product/1/2", "product", "test")
                store.status("https://shopee.vn/product/1/2", "partial", "test")
            finally:
                store.close()
            store = Store(tmp)
            try:
                self.assertEqual([group["saved"] for group in store.sample_progress("1:2").values()], [100] * 5)
                report = store.export()
                self.assertEqual(report["reviews_observed"], 500)
                self.assertEqual(report["review_sampling"]["1:2"]["cap"], 500)
                self.assertEqual(store.next_job()["kind"], "product")
                store.record_scope({"sample_reviews": False})
                self.assertEqual(len(store.product_reviews("1:2")), 650)
            finally:
                store.close()
