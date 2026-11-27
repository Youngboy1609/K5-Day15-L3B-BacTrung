import csv
import io
import json
import tempfile
import unittest
from email.message import Message
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from shopee_collector.images import download_images, fetch_image, image_url
from shopee_collector.parsing import extract_payload, jsonld_products
from shopee_collector.storage import Store


class ImageResponse(io.BytesIO):
    def __init__(self, data, content_type="image/gif"):
        super().__init__(data)
        self.status = 200
        self.headers = Message()
        self.headers["Content-Type"] = content_type


class ImageTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Store(self.tmp.name)
        self.addCleanup(self.store.close)
        payload = json.loads(Path(__file__).with_name("synthetic_payload.json").read_text(encoding="utf-8"))
        self.store.ingest(extract_payload(payload))

    async def test_images_and_review_metadata_export(self):
        # A subsequent sparse response should preserve media, counts, and shop reply.
        self.store.ingest(extract_payload({"ratings": [{
            "cmtid": 888001, "itemid": 99900002, "shopid": 99900001, "rating_star": 5,
        }]}))
        with patch("shopee_collector.images.build_opener") as opener:
            opener.return_value.open.side_effect = lambda *args, **kwargs: ImageResponse(b"GIF89a" + b"x" * 20)
            self.assertIsNone(await download_images(self.store, lambda: None))
            self.assertIsNone(await download_images(self.store, lambda: None))
            self.assertEqual(opener.return_value.open.call_count, 2)
        self.store.export()
        with (self.store.folder / "images.csv").open(encoding="utf-8-sig", newline="") as f:
            images = list(csv.DictReader(f))
        self.assertEqual(len(images), 4)
        self.assertEqual({row["role"] for row in images}, {"cover", "gallery", "review"})
        self.assertEqual({row["owner_kind"] for row in images}, {"product", "review"})
        self.assertTrue(all(row["status"] == "saved" for row in images))
        product_path = next(row["local_path"] for row in images if row["owner_kind"] == "product")
        self.assertEqual(sum(row["local_path"] == product_path for row in images), 3)
        self.assertTrue(all((self.store.folder / row["local_path"]).read_bytes().startswith(b"GIF89a")
                            for row in images))

        with (self.store.folder / "reviews.csv").open(encoding="utf-8-sig", newline="") as f:
            first, second = list(csv.DictReader(f))
        self.assertEqual(first["created_at_utc"], "2023-11-14T22:13:20+00:00")
        self.assertEqual(first["shop_reply_created_at_utc"], "2023-11-14T22:16:40+00:00")
        self.assertEqual(first["like_count"], "4")
        self.assertEqual(first["dislike_count"], "0")
        self.assertIn("Cảm ơn", first["shop_reply_content"])
        self.assertEqual(second["like_count"], "")
        self.assertEqual(second["dislike_count"], "")
        self.assertEqual(second["shop_reply_content"], "")

    async def test_429_stops_after_first_image(self):
        with patch("shopee_collector.images.build_opener") as opener:
            opener.return_value.open.side_effect = HTTPError("test", 429, "rate limit", {}, None)
            self.assertEqual(await download_images(self.store, lambda: None), "image_http_429")
            self.assertEqual(opener.return_value.open.call_count, 1)
        self.assertEqual(self.store.report()["image_download_status"], {"http_429": 1})

    def test_image_validation_and_jsonld(self):
        self.assertIsNone(image_url("https://example.com/file/vn-test-image-001"))
        self.assertIsNone(image_url("https://user@down-vn.img.susercontent.com/file/vn-test-image-001"))
        url = image_url("vn-test-image-001")
        payload = {"@type": "Product", "name": "demo", "image": url}
        product = jsonld_products(payload, "https://shopee.vn/product/1/2", "test")[0]
        self.assertEqual(product["image_urls"], [url])
        with patch("shopee_collector.images.build_opener") as opener:
            opener.return_value.open.return_value = ImageResponse(b"<html>blocked</html>")
            self.assertEqual(fetch_image(self.store.folder, url)["status"], "unsupported_image")
        self.assertFalse((self.store.folder / "images").exists())
