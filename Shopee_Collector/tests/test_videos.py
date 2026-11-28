import csv
import io
import tempfile
import unittest
from email.message import Message
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from shopee_collector.parsing import extract_payload, jsonld_products
from shopee_collector.storage import Store
from shopee_collector.videos import download_videos, fetch_video


CDN = "https://down-ws-vn.vod.susercontent.com"
CLIP = f"{CDN}/api/v4/clip.mp4"
STREAM = f"{CDN}/api/v4/stream.m3u8"
MP4_BYTES = b"\x00\x00\x00\x18ftypisom" + b"x" * 1800


class VideoResponse(io.BytesIO):
    def __init__(self, data=MP4_BYTES, length=None):
        super().__init__(data)
        self.status = 200
        self.headers = Message()
        self.headers["Content-Type"] = "video/mp4"
        self.headers["Content-Length"] = str(len(data) if length is None else length)


class VideoTests(unittest.IsolatedAsyncioTestCase):
    async def test_record_product_and_review_video_and_reuse_file(self):
        item = {"shopid": 1, "itemid": 2, "name": "Product",
                "video_info_list": [{"default_format": {"url": CLIP}}]}
        review = {"shopid": 1, "itemid": 2, "cmtid": 3, "rating_star": 5, "comment": "Test",
                  "videos": [{"formats": [{"url": CLIP}, {"url": STREAM}]}]}
        with tempfile.TemporaryDirectory() as temp:
            store = Store(temp)
            try:
                store.ingest(extract_payload({"item": item, "rating": review}))
                store.ingest(extract_payload({"rating": {k: v for k, v in review.items() if k != "videos"}}))
                with patch("shopee_collector.videos.build_opener") as opener:
                    opener.return_value.open.side_effect = lambda *args, **kwargs: VideoResponse()
                    self.assertIsNone(await download_videos(store, lambda: None))
                    self.assertIsNone(await download_videos(store, lambda: None))
                    self.assertEqual(opener.return_value.open.call_count, 1)
                report = store.export()
                self.assertEqual(report["video_download_status"], {"saved": 1, "unsupported_stream": 1})
                with (Path(temp) / "videos.csv").open(encoding="utf-8-sig", newline="") as file:
                    rows = list(csv.DictReader(file))
                self.assertEqual(len(rows), 3)
                files = [row["local_path"] for row in rows if row["status"] == "saved"]
                self.assertEqual(len(files), 2)
                self.assertEqual(files[0], files[1])
                self.assertEqual((Path(temp) / files[0]).read_bytes(), MP4_BYTES)
                self.assertTrue(any(row["review_key"] == "1:2:3" for row in rows))
            finally:
                store.close()

    def test_incomplete_video_is_not_kept(self):
        with tempfile.TemporaryDirectory() as temp, patch("shopee_collector.videos.build_opener") as opener:
            opener.return_value.open.return_value = VideoResponse(length=len(MP4_BYTES) + 50)
            self.assertEqual(fetch_video(Path(temp), CLIP)["status"], "partial_response")
            self.assertEqual(list((Path(temp) / "videos").iterdir()), [])

    async def test_403_pauses_video_download(self):
        item = {"shopid": 1, "itemid": 2, "name": "Product",
                "videos": [CLIP, f"{CDN}/other.mp4"]}
        with tempfile.TemporaryDirectory() as temp:
            store = Store(temp)
            try:
                store.ingest(extract_payload(item))
                with patch("shopee_collector.videos.build_opener") as opener:
                    opener.return_value.open.side_effect = HTTPError(CLIP, 403, "Forbidden", {}, None)
                    self.assertEqual(await download_videos(store, lambda: None), "video_http_403")
                    self.assertEqual(opener.return_value.open.call_count, 1)
            finally:
                store.close()

    def test_only_allow_valid_video_hosts_and_jsonld(self):
        payload = {"@type": "Product", "name": "Product", "video": [
            {"@type": "VideoObject", "contentUrl": CLIP},
            {"@type": "VideoObject", "contentUrl": "https://example.test/clip.mp4"},
        ]}
        rows = jsonld_products(payload, "https://shopee.vn/product/1/2", "test")
        self.assertEqual(rows[0]["video_urls"], [CLIP])
