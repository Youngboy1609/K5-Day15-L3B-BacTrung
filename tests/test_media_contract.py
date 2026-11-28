import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODEBASE = os.path.join(ROOT, "codebase")
if CODEBASE not in sys.path:
    sys.path.insert(0, CODEBASE)

from tools import get_product_reviews  # noqa: E402


VALID = {
    "product_url": "https://shopee.vn/fixture-bactrung-case-clear-001",
    "phone_model": "iPhone 15 Pro",
    "case_variant": "Ốp trong suốt viền đen",
}


class MediaContractTests(unittest.TestCase):
    def test_media_paths_are_local_and_exact_variant_only(self):
        listing = get_product_reviews(**VALID)

        self.assertEqual(listing["status"], "ok")
        self.assertTrue(any(review.get("media") for review in listing["reviews"]))
        review_with_frame = next(
            review for review in listing["reviews"]
            if review["review_id"] == "R004"
        )
        self.assertTrue(any(item.get("type") == "video_frame" for item in review_with_frame["media"]))
        for review in listing["reviews"]:
            self.assertEqual(review["phone_model"], VALID["phone_model"])
            self.assertEqual(review["case_variant"], VALID["case_variant"])
            for item in review.get("media", []):
                self.assertFalse(os.path.isabs(item["path"]))
                self.assertNotIn("..", item["path"].split("/"))

    def test_answer_contract_is_json_text(self):
        from agent import answer

        result = answer(json.dumps(VALID, ensure_ascii=False))

        self.assertEqual(set(result), {"output"})
        self.assertIsInstance(result["output"], str)
        self.assertEqual(json.loads(result["output"])["status"], "ok")

    def test_missing_local_image_is_skipped_without_aborting_text_analysis(self):
        from agent import _media_images

        self.assertEqual(
            _media_images([{"review_id": "R404", "media": [{"path": "media/missing.png"}]}]),
            [],
        )

    def test_media_loader_preserves_still_frame_provenance(self):
        from agent import _media_images

        with tempfile.TemporaryDirectory() as temp:
            Path(temp, "frame.png").write_bytes(b"synthetic frame")
            media = _media_images([{
                "review_id": "R010",
                "media": [{
                    "type": "video_frame",
                    "path": "frame.png",
                    "analysis_note": "One still frame only",
                }],
            }], media_root=temp)

        self.assertEqual(media[0]["media_type"], "video_frame")
        self.assertEqual(media[0]["analysis_note"], "One still frame only")
        self.assertTrue(media[0]["data_url"].startswith("data:image/png;base64,"))


if __name__ == "__main__":
    unittest.main()
