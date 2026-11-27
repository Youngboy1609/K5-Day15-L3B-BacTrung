"""Nối model — chỗ DUY NHẤT trong bản chạy thử gọi model AI. NHÓM VIẾT phần gọi model thật.

Hợp đồng (giữ nguyên để khung đo được token):
    call_model(system: str, user: str) -> dict với 4 khoá
        "text":       str   chữ model trả về
        "model":      str   tên model đã gọi (để tra giá ở bảng giá model)
        "tokens_in":  int   số token vào, lấy từ trường usage trong phản hồi API — KHÔNG ước lượng
        "tokens_out": int   số token ra, gồm cả token suy luận / suy nghĩ nếu API tính riêng
    @model_call (từ tracing.py) tự ghi mỗi lần gọi vào trace; agent.py gọi call_model bao nhiêu lần
    cũng được, khung tự cộng token.
    Lỗi gọi model (hết lượt, sai key, mất mạng): cứ để exception bay ra — khung ghi lỗi vào cột error.

Chế độ giả (mặc định khi .env chưa có MODEL_PROVIDER, hoặc MODEL_PROVIDER=fake):
    trả một câu giả cố định, model "fake", token 0 — để luồng chạy hết từ trước CP2 (guide bước 3.2).
    Lượt `run.py eval` / `run.py simulate` chạy bằng model giả KHÔNG được tính.

Nối model thật: điền .env (chép từ .env.example), rồi viết nhánh gọi API ở dưới theo docs/connect-model.md
(có ví dụ OpenAI, Claude, model chạy trên máy, và cách nối nhà cung cấp khác). Không dán API key vào file này.
"""
import os
import json

from tracing import model_call

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_env(path=os.path.join(ROOT, ".env")):
    """Đọc file .env (KEY=VALUE mỗi dòng) vào biến môi trường, không ghi đè biến đã có. Khung — không cần sửa."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env()
MODEL_PROVIDER = (os.environ.get("MODEL_PROVIDER") or "fake").strip().lower()
MODEL_NAME = (os.environ.get("MODEL_NAME") or "").strip()
API_KEY = (os.environ.get("API_KEY") or "").strip()


POSITIVE_PHRASES = (
    "vừa khít", "vừa máy", "đúng mẫu", "đúng cho", "nút bấm nhạy",
    "ôm máy chắc", "dễ cầm", "không che", "không bị cấn", "chưa trầy",
    "chưa thấy lỏng", "dùng ổn", "đẹp",
)
NEGATIVE_PHRASES = (
    "cấn", "lỏng", "ố vàng", "xê dịch", "bị kênh", "nút bấm cứng",
    "cạnh hơi cứng", "che ống kính", "bị trầy", "nứt", "bong",
    "không vừa", "sai mẫu",
)
NEGATED_PHRASES = (
    "không bị cấn", "không che", "chưa thấy lỏng", "chưa trầy",
)
SPECIFIC_DETAILS = (
    "camera", "ống kính", "nút", "viền", "cạnh", "góc", "tuần", "ngày",
    "lần rơi", "âm lượng", "màn hình",
)


def _mock_review_judge(user: str) -> str:
    """Deterministic CP2 mock; it is not an AI/model result and ignores media."""
    try:
        payload = json.loads(user)
    except (TypeError, ValueError):
        return json.dumps({"reviews": []}, ensure_ascii=False)
    reviews = payload.get("reviews") if isinstance(payload, dict) else None
    if not isinstance(reviews, list):
        return json.dumps({"reviews": []}, ensure_ascii=False)

    judged = []
    for review in reviews[:12]:
        if not isinstance(review, dict):
            continue
        review_id = review.get("review_id")
        text = review.get("text")
        if not isinstance(review_id, str) or not isinstance(text, str):
            continue
        normalized = " ".join(text.casefold().split())
        for phrase in NEGATED_PHRASES:
            normalized = normalized.replace(phrase, " ")
        positive_hits = [phrase for phrase in POSITIVE_PHRASES if phrase in normalized]
        negative_hits = [phrase for phrase in NEGATIVE_PHRASES if phrase in normalized]
        if positive_hits and negative_hits:
            sentiment = "mixed"
        elif positive_hits:
            sentiment = "positive"
        elif negative_hits:
            sentiment = "negative"
        else:
            sentiment = "unknown"

        details = [detail for detail in SPECIFIC_DETAILS if detail in normalized]
        if len(details) >= 2 or any(
            term in normalized for term in ("hai tuần", "một tuần", "khoảng một tuần", "lần rơi")
        ):
            strength = "high"
            reason = "Nêu chi tiết có thể đối chiếu: " + ", ".join(details[:2]) + "."
        elif len(text.strip()) >= 45:
            strength = "medium"
            reason = "Có mô tả trải nghiệm nhưng chi tiết kiểm chứng còn hạn chế."
        else:
            strength = "low"
            reason = "Review ngắn, chưa nêu đủ chi tiết để kiểm chứng."
        judged.append(
            {
                "review_id": review_id,
                "sentiment": sentiment,
                "evidence_strength": strength,
                "reason": reason,
                "media_assessment": "not_assessed",
            }
        )
    return json.dumps({"reviews": judged}, ensure_ascii=False)


@model_call
def call_model(system: str, user: str) -> dict:
    if MODEL_PROVIDER == "fake":
        return {
            "text": _mock_review_judge(user),
            "model": "fake",
            "tokens_in": 0,
            "tokens_out": 0,
        }

    # NHÓM VIẾT: gọi model thật ở đây (theo MODEL_PROVIDER, MODEL_NAME, API_KEY) rồi trả đúng 4 khoá.
    # Ví dụ chép được cho từng nhà cung cấp: docs/connect-model.md mục 2.
    raise NotImplementedError(
        "chưa viết phần gọi model thật cho MODEL_PROVIDER=%s trong codebase/ai.py — xem docs/connect-model.md"
        % MODEL_PROVIDER)
