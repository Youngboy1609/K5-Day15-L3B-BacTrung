import csv
import os
import sys
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SURVEY_DIR = os.path.join(ROOT, "evidence", "survey")
if SURVEY_DIR not in sys.path:
    sys.path.insert(0, SURVEY_DIR)

from analyze_results import analyze  # noqa: E402


class SurveyAnalysisTests(unittest.TestCase):
    def test_public_csv_uses_anonymous_ids_not_exact_timestamps(self):
        path = os.path.join(SURVEY_DIR, "results.csv")
        with open(path, encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            rows = list(reader)
            self.assertEqual(reader.fieldnames[0], "response_id")
            self.assertNotIn("Dấu thời gian", reader.fieldnames)
        self.assertEqual(rows[0]["response_id"], "S001")
        self.assertEqual(rows[-1]["response_id"], "S064")

    def test_cp2_counts_reproduce_from_anonymized_csv(self):
        result = analyze()

        self.assertEqual(result["csv_rows"], 64)
        self.assertEqual(result["eligible_shopee_90d_with_review_time"], 42)
        self.assertEqual(result["reported_any_difficulty"], 41)
        self.assertEqual(result["reported_difficulties"][
            "Đánh giá quá ngắn hoặc không cung cấp thông tin hữu ích"
        ], 28)
        self.assertEqual(result["reported_difficulties"][
            "Nghi ngờ đánh giá thiếu khách quan hoặc không đáng tin cậy"
        ], 28)
        self.assertEqual(result["case_mentions"], ["S055"])
        self.assertEqual(sum(result["eligible_industries"].values()), 42)


if __name__ == "__main__":
    unittest.main()
