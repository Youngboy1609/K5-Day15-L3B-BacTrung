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
import urllib.error
import urllib.request

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
if os.environ.get("BACTRUNG_FAKE_FOR_TESTS"):
    MODEL_PROVIDER = "fake"


POSITIVE_PHRASES = (
    "vừa khít", "vừa máy", "đúng mẫu", "nút bấm nhạy", "ôm máy chắc",
    "dễ cầm", "không che", "không bị cấn", "chưa thấy lỏng", "chưa trầy", "đẹp",
)
NEGATIVE_PHRASES = (
    "cấn", "lỏng", "ố vàng", "xê dịch", "bị kênh", "nút bấm cứng",
    "cạnh hơi cứng", "che ống kính", "nứt", "bong", "không vừa", "sai mẫu",
)
NEGATED_PHRASES = ("không bị cấn", "không che", "chưa thấy lỏng", "chưa trầy")
SPECIFIC_DETAILS = (
    "camera", "ống kính", "nút", "viền", "cạnh", "góc", "tuần", "ngày",
    "lần rơi", "âm lượng", "màn hình",
)


def _mock_judge(user):
    """Deterministic mock classifier; it is not an AI result and ignores media."""
    try:
        payload = json.loads(user)
        reviews = payload.get("reviews", [])
    except (TypeError, ValueError):
        reviews = []
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
        positive = [phrase for phrase in POSITIVE_PHRASES if phrase in normalized]
        negative = [phrase for phrase in NEGATIVE_PHRASES if phrase in normalized]
        sentiment = (
            "mixed" if positive and negative else
            "positive" if positive else
            "negative" if negative else
            "unknown"
        )
        details = [term for term in SPECIFIC_DETAILS if term in normalized]
        if len(details) >= 2 or any(phrase in normalized for phrase in ("hai tuần", "một tuần", "lần rơi")):
            strength = "high"
            reason = "Nêu chi tiết có thể đối chiếu: " + ", ".join(details[:2]) + "."
        elif len(text.strip()) >= 45:
            strength = "medium"
            reason = "Có mô tả trải nghiệm nhưng chi tiết kiểm chứng còn hạn chế."
        else:
            strength = "low"
            reason = "Review ngắn, chưa nêu đủ chi tiết để kiểm chứng."
        judged.append({
            "review_id": review_id,
            "sentiment": sentiment,
            "evidence_strength": strength,
            "reason": reason,
            "media_assessment": "not_assessed",
        })
    return json.dumps({"reviews": judged}, ensure_ascii=False)


CHAT_URLS = {
    "openai": "https://api.openai.com/v1/chat/completions",
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
}

JUDGEMENT_SCHEMA = {
    "type": "object",
    "required": ["reviews"],
    "additionalProperties": False,
    "properties": {
        "reviews": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "review_id",
                    "sentiment",
                    "evidence_strength",
                    "reason",
                    "media_assessment",
                ],
                "additionalProperties": False,
                "properties": {
                    "review_id": {"type": "string"},
                    "sentiment": {"type": "string", "enum": ["positive", "negative", "mixed", "unknown"]},
                    "evidence_strength": {"type": "string", "enum": ["high", "medium", "low"]},
                    "reason": {"type": "string"},
                    "media_assessment": {
                        "type": "string",
                        "enum": ["not_assessed", "not_applicable", "supported", "unsupported"],
                    },
                },
            },
        },
    },
}


def _post_chat(url: str, body: dict) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + API_KEY},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


@model_call
def call_model(system: str, user: str, images=()) -> dict:
    if MODEL_PROVIDER == "fake":
        return {
            "text": _mock_judge(user),
            "model": "fake",
            "tokens_in": 0,
            "tokens_out": 0,
        }
    url = CHAT_URLS.get(MODEL_PROVIDER)
    if url is None:
        raise NotImplementedError("CP4 demo supports MODEL_PROVIDER=openai, openrouter, or fake")
    if not MODEL_NAME or not API_KEY:
        raise RuntimeError("Chưa điền MODEL_NAME/API_KEY trong .env")

    content = [{"type": "text", "text": user}]
    for index, image in enumerate(images, start=1):
        if isinstance(image, dict):
            review_id = image.get("review_id", "unknown")
            image_index = image.get("image_index", index)
            image_url = image.get("data_url")
            if image.get("media_type") == "video_frame":
                description = (
                    "One still frame only from a review video; do not infer motion, "
                    "events across time, or audio."
                )
            else:
                description = "Review image."
            content.append({
                "type": "text",
                "text": (
                    f"Image index {image_index}; belongs only to review_id {review_id}. "
                    f"{description} {image.get('analysis_note') or ''}"
                ).strip(),
            })
        else:
            image_url = image
        content.append({"type": "image_url", "image_url": {"url": image_url}})
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": content},
    ]
    strict_body = {
        "model": MODEL_NAME,
        "messages": messages,
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "review_judgements", "strict": True, "schema": JUDGEMENT_SCHEMA},
        },
    }
    if MODEL_PROVIDER == "openrouter":
        strict_body["provider"] = {"require_parameters": True}
    try:
        data = _post_chat(url, strict_body)
    except urllib.error.HTTPError as error:
        if error.code != 400:
            raise RuntimeError(f"{MODEL_PROVIDER} HTTP {error.code}") from None
        fallback_body = {
            "model": MODEL_NAME,
            "messages": messages,
            "response_format": {"type": "json_object"},
        }
        try:
            data = _post_chat(url, fallback_body)
        except urllib.error.HTTPError as fallback_error:
            raise RuntimeError(f"{MODEL_PROVIDER} HTTP {fallback_error.code}") from None
    except (urllib.error.URLError, TimeoutError):
        raise RuntimeError(f"Không kết nối được {MODEL_PROVIDER} trong thời gian chờ") from None
    usage = data["usage"]
    return {
        "text": data["choices"][0]["message"].get("content") or json.dumps(data["choices"][0]["message"].get("refusal") or ""),
        "model": MODEL_NAME,
        "tokens_in": int(usage["prompt_tokens"]),
        "tokens_out": int(usage["completion_tokens"]),
    }
