import csv
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
CODEBASE = ROOT / "codebase"
if str(CODEBASE) not in sys.path:
    sys.path.insert(0, str(CODEBASE))

from collector_data import load_latest_collector_dataset
import tools


class CollectorDataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.output_root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def write_export(self, name, *, mapped=True, image_status="saved"):
        folder = self.output_root / name
        folder.mkdir()
        (folder / "coverage_report.json").write_text(
            json.dumps({
                "coverage": "unknown; discovered subset only; never whole-market coverage",
                "review_sampling": {
                    "1:2": {
                        "observed_count": 1,
                        "cap": 100,
                        "representativeness": "unknown_observed_subset_only",
                    }
                },
            }),
            encoding="utf-8",
        )
        with (folder / "products.csv").open("w", encoding="utf-8-sig", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=["product_key", "url", "name"])
            writer.writeheader()
            writer.writerow({
                "product_key": "1:2",
                "url": "https://shopee.vn/product/1/2",
                "name": "Ốp",
            })
        fields = [
            "review_key", "review_id", "product_key", "rating", "content",
            "phone_model", "case_variant", "like_count",
        ]
        with (folder / "reviews.csv").open("w", encoding="utf-8-sig", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=fields)
            writer.writeheader()
            writer.writerow({
                "review_key": "1:2:3",
                "review_id": "3",
                "product_key": "1:2",
                "rating": "5",
                "content": "Khít máy",
                "phone_model": "iPhone 15 Pro" if mapped else "",
                "case_variant": "Ốp viền đen" if mapped else "",
                "like_count": "2",
            })
        (folder / "images").mkdir()
        image = folder / "images" / "r3.png"
        image.write_bytes(b"synthetic image bytes")
        with (folder / "images.csv").open("w", encoding="utf-8-sig", newline="") as output:
            writer = csv.DictWriter(
                output,
                fieldnames=["owner_kind", "role", "product_key", "review_key", "image_url", "status", "local_path"],
            )
            writer.writeheader()
            writer.writerow({
                "owner_kind": "review",
                "role": "review",
                "product_key": "1:2",
                "review_key": "1:2:3",
                "image_url": "https://cdn.example/image.png",
                "status": image_status,
                "local_path": "images/r3.png",
            })
        (folder / "review_video_frames").mkdir()
        (folder / "review_video_frames" / "r3.png").write_bytes(b"synthetic frame")
        with (folder / "videos.csv").open("w", encoding="utf-8-sig", newline="") as output:
            writer = csv.DictWriter(
                output,
                fieldnames=[
                    "owner_kind", "role", "product_key", "review_key", "video_url",
                    "status", "local_path", "fallback_kind", "analysis_note",
                ],
            )
            writer.writeheader()
            writer.writerow({
                "owner_kind": "review",
                "role": "review",
                "product_key": "1:2",
                "review_key": "1:2:3",
                "video_url": "https://video.example/review.mp4",
                "status": "frame_only",
                "local_path": "review_video_frames/r3.png",
                "fallback_kind": "video_frame_screenshot",
                "analysis_note": "One visible frame only",
            })
        return folder

    def test_loads_newest_valid_export_and_attaches_local_media(self):
        self.write_export("older")
        newer = self.write_export("newer")
        data = load_latest_collector_dataset(self.output_root)

        self.assertEqual(Path(data["source_dir"]), newer)
        review = data["products"][0]["reviews"][0]
        self.assertEqual(review["phone_model"], "iPhone 15 Pro")
        self.assertEqual(review["case_variant"], "Ốp viền đen")
        self.assertEqual(review["media"][0]["path"], "images/r3.png")
        self.assertEqual(review["media"][1]["type"], "video_frame")
        self.assertIn("frame only", review["media"][1]["analysis_note"])
        self.assertEqual(data["review_sampling"]["1:2"]["representativeness"],
                         "unknown_observed_subset_only")

    def test_ignores_reviews_without_explicit_exact_variant_fields(self):
        self.write_export("unmapped", mapped=False)
        data = load_latest_collector_dataset(self.output_root)
        self.assertEqual(data["products"][0]["reviews"], [])
        self.assertEqual(data["unmatched_variant_reviews"], 1)

    def test_ignores_paths_outside_export_and_unsaved_media(self):
        folder = self.write_export("unsafe", image_status="http_403")
        with (folder / "images.csv").open("a", encoding="utf-8") as output:
            output.write("review,review,1:2,1:2:3,https://cdn.example/other.png,saved,../../secret.png\n")
        data = load_latest_collector_dataset(self.output_root)
        media = data["products"][0]["reviews"][0]["media"]
        self.assertEqual([item["type"] for item in media], ["video_frame"])
        self.assertNotIn("../../secret.png", [item["path"] for item in media])

    def test_returns_none_without_a_valid_export(self):
        (self.output_root / "incomplete").mkdir()
        self.assertIsNone(load_latest_collector_dataset(self.output_root))

    def test_analysis_tool_uses_latest_collector_export_and_exact_variant_only(self):
        self.write_export("latest")
        with patch("collector_data.DEFAULT_OUTPUT_ROOT", self.output_root):
            result = tools.get_product_reviews(
                "https://shopee.vn/product/1/2",
                "iPhone 15 Pro",
                "Ốp viền đen",
            )
            no_match = tools.get_product_reviews(
                "https://shopee.vn/product/1/2",
                "iPhone 15",
                "Ốp viền đen",
            )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["source_type"], "collector")
        self.assertEqual([r["review_id"] for r in result["reviews"]], ["3"])
        self.assertEqual(no_match["status"], "needs_input")


if __name__ == "__main__":
    unittest.main()
