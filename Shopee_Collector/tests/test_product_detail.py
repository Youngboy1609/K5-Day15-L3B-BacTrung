import tempfile
import unittest

from shopee_collector.parsing import extract_payload, page_bundle
from shopee_collector.storage import Store, detail_fields


URL = "https://shopee.vn/product/1/2"
VIEW = {
    "url": URL, "name": "Tai nghe", "shop_name": "Shop A", "sold_display": "Đã bán 1k+",
    "price_text": "0₫\nGiá Sau Voucher", "rating": "4,7", "rating_count_display": "445",
    "description": "Mô tả thật", "description_section_seen": True,
    "categories": [{"category_id": "20", "name": "Tai nghe"}],
    "attributes": [{"name": "Kết nối", "value": "Bluetooth"}],
    "tiers": [{"name": "Màu", "options": ["Đen", "Trắng"]}],
    "cover": "vn-cover-example", "gallery_images": ["vn-cover-example", "vn-gallery-example"],
    "description_images": ["vn-description-example"],
    "reviews": [{"id": "7", "images": ["vn-review-example"]}],
}


class ProductDetailTests(unittest.TestCase):
    def test_visible_product_fields_and_media_roles(self):
        with tempfile.TemporaryDirectory() as folder:
            store = Store(folder)
            try:
                store.ingest(page_bundle(VIEW, URL, "now"))
                p = store.get("product", "1:2")
                self.assertTrue(all(detail_fields(p).values()))
                self.assertEqual(p["price"], "0")
                self.assertEqual(p["price_unit_status"], "displayed_vnd_after_voucher")
                self.assertEqual(p["sold_display"], "Đã bán 1k+")
                self.assertIsNone(p.get("sold_total_reported"))
                self.assertEqual([v["variant_name"] for v in p["variants"]], ["Đen", "Trắng"])
                report = store.export()
                self.assertEqual(report["products_meeting_detail_checks"], 1)
                self.assertEqual(report["media_by_role"]["description_image"]["observed_urls"], 1)
                self.assertEqual(report["media_by_role"]["description_image"]["saved_files"], 0)
                roles = {r["role"] for r in store.media_links("image")}
                self.assertEqual(roles, {"cover", "gallery", "description", "review"})
            finally:
                store.close()

    def test_purchase_snapshot_is_neither_live_model_nor_customer_photo(self):
        p = {"shopid": 1, "itemid": 2, "name": "Historic name", "image": "vn-snapshot-example"}
        payload = {"rating_star": 5, "cmtid": 7, "itemid": 2, "shopid": 1, "comment": "",
                   "product_items": [p], "images": []}
        result = extract_payload(payload)
        self.assertEqual(result["products"], [])
        self.assertEqual(result["reviews"][0]["image_urls"], [])
        self.assertEqual(result["reviews"][0]["content_status"], "empty_at_source")
        del payload["comment"]
        self.assertIsNone(extract_payload(payload)["reviews"][0]["content_status"])

    def test_other_product_and_multi_tier(self):
        self.assertEqual(page_bundle(VIEW, "https://shopee.vn/product/3/4", "now"), {})
        tiers = VIEW["tiers"] + [{"name": "Size", "options": ["S", "L"]}]
        p = page_bundle({**VIEW, "tiers": tiers}, URL, "now")["products"][0]
        self.assertEqual(p["variants"], [])
        self.assertEqual(p["variant_options"], tiers)

    def test_review_variant_fields_are_exported_only_when_explicit(self):
        view = {**VIEW, "reviews": [{
            "id": "7", "phone_model": "iPhone 15 Pro", "case_variant": "Ốp viền đen",
        }]}
        review = page_bundle(view, URL, "now")["reviews"][0]
        self.assertEqual(review.get("phone_model"), "iPhone 15 Pro")
        self.assertEqual(review.get("case_variant"), "Ốp viền đen")

        untagged = page_bundle(VIEW, URL, "now")["reviews"][0]
        self.assertIsNone(untagged["phone_model"])
        self.assertIsNone(untagged["case_variant"])

    def test_retry_after_verification_and_refresh(self):
        with tempfile.TemporaryDirectory() as folder:
            store = Store(folder)
            try:
                store.enqueue(URL, "product", "now")
                store.status(URL, "running", "now")
                store.status(URL, "blocked", "now")
                store.refresh_products([URL])
                self.assertIsNotNone(store.blocked_job())
                store.retry(max_attempts=1, confirmed_access=True)
                self.assertEqual(store.next_job()["url"], URL)
                store.status(URL, "partial", "now")
                store.refresh_products([URL])
                self.assertEqual(store.next_job()["url"], URL)
            finally:
                store.close()
