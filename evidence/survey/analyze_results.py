"""Reproducible descriptive counts for the CP2 anonymized survey CSV."""
import csv
import json
from collections import Counter
from pathlib import Path


RESULTS = Path(__file__).with_name("results.csv")
RECENT = {"Trong 7 ngày gần đây", "Từ 8–30 ngày trước", "Từ 30–90 ngày trước"}
PAIN_OPTIONS = (
    "Có quá nhiều đánh giá, mất thời gian đọc và tổng hợp",
    "Đánh giá quá ngắn hoặc không cung cấp thông tin hữu ích",
    "Nghi ngờ đánh giá thiếu khách quan hoặc không đáng tin cậy",
    "Các đánh giá có nội dung mâu thuẫn nhau",
    "Đánh giá không liên quan đến mẫu mã, kích thước hoặc phiên bản sản phẩm mình định mua",
    "Hình ảnh/video đánh giá không thể hiện rõ chất lượng thực tế",
    "Khó xác định ưu điểm và nhược điểm của sản phẩm",
    "Khó so sánh giữa các sản phẩm hoặc cửa hàng",
)


def analyze(path=RESULTS):
    with open(path, encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    if not rows:
        raise ValueError("Survey results CSV has no data rows")

    fields = rows[0]
    # Use the stable question wording rather than positional indexes.
    by_prefix = {}
    for name in fields:
        if name.startswith("1. Lần gần nhất"):
            by_prefix["recent"] = name
        elif name.startswith("2. Trong lần mua sắm gần nhất, bạn sử dụng"):
            by_prefix["platform"] = name
        elif name.startswith("4. Trong lần mua sắm gần nhất, bạn tìm kiếm"):
            by_prefix["industry"] = name
        elif name.startswith("6. Bạn đã dành khoảng bao nhiêu thời gian"):
            by_prefix["time"] = name
        elif name.startswith("7. Trong quá trình tìm hiểu"):
            by_prefix["pain"] = name
        elif name.startswith("10. Bạn có thể chia sẻ"):
            by_prefix["story"] = name
    if set(by_prefix) != {"recent", "platform", "industry", "time", "pain", "story"}:
        raise ValueError("Survey CSV headers do not match the expected questionnaire")

    eligible = [
        (row, index)
        for index, row in enumerate(rows, 1)
        if row[by_prefix["platform"]].strip().casefold() == "shopee"
        and row[by_prefix["recent"]].strip() in RECENT
        and row[by_prefix["time"]].strip()
        and not row[by_prefix["time"]].strip().casefold().startswith("không đọc")
    ]
    industries = Counter(row[by_prefix["industry"]].strip() for row, _ in eligible)
    difficulty_count = sum(
        any(option in row[by_prefix["pain"]] for option in PAIN_OPTIONS)
        for row, _ in eligible
    )
    pain_counts = {
        option: sum(option in row[by_prefix["pain"]] for row, _ in eligible)
        for option in PAIN_OPTIONS
    }
    times = Counter(row[by_prefix["time"]].strip() for row, _ in eligible)
    case_mentions = [
        f"S{index:03d}"
        for row, index in eligible
        if "ốp" in row[by_prefix["story"]].casefold()
    ]
    return {
        "csv_rows": len(rows),
        "eligible_shopee_90d_with_review_time": len(eligible),
        "eligible_industries": dict(sorted(industries.items())),
        "reported_any_difficulty": difficulty_count,
        "reported_difficulties": pain_counts,
        "review_time_groups": dict(sorted(times.items())),
        "case_mentions": case_mentions,
    }


if __name__ == "__main__":
    print(json.dumps(analyze(), ensure_ascii=False, indent=2))
