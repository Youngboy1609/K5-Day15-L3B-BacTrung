"""Gọi model OpenAI/OpenRouter hoặc chạy giả lập, với token từ usage của API."""
import base64
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from tracing import model_call

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = Path(ROOT) / "data"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
CHAT_URLS = {"openai": OPENAI_URL, "openrouter": "https://openrouter.ai/api/v1/chat/completions"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_IMAGE_PAYLOAD = 32 * 1024 * 1024


@dataclass(frozen=True)
class ImageInput:
    ref: str
    data_url: str = field(repr=False)


def load_image(ref: str, relative_path: str) -> ImageInput | None:
    """Đọc một ảnh demo cục bộ để đính kèm vào yêu cầu model."""
    try:
        if Path(relative_path).anchor:
            return None
        path = (DATA_DIR / relative_path).resolve()
        if not path.is_relative_to(DATA_DIR.resolve()) or not path.is_file():
            return None
        with path.open("rb") as image:
            content = image.read(MAX_IMAGE_BYTES + 1)
    except (OSError, TypeError, ValueError, RuntimeError):
        return None
    if len(content) > MAX_IMAGE_BYTES:
        return None
    if content.startswith(b"\xff\xd8\xff"):
        mime = "image/jpeg"
    elif content.startswith(b"\x89PNG\r\n\x1a\n"):
        mime = "image/png"
    elif content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        mime = "image/webp"
    else:
        return None
    encoded = base64.b64encode(content).decode("ascii")
    return ImageInput(ref, f"data:{mime};base64,{encoded}")


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


@model_call
def call_model(system: str, user: str, *, images=(), schema=None, mock_text=None) -> dict:
    if MODEL_PROVIDER == "fake":
        if mock_text is None:
            last = (user.strip().splitlines() or [""])[-1]
            mock_text = "[câu trả lời giả — chưa nối model] " + last[:60]
        return {"text": mock_text, "model": "fake", "tokens_in": 0, "tokens_out": 0}
    url = CHAT_URLS.get(MODEL_PROVIDER)
    if url is None:
        raise NotImplementedError("MODEL_PROVIDER hỗ trợ: fake, openai, openrouter.")
    if not MODEL_NAME or not API_KEY:
        raise RuntimeError(f"Điền MODEL_NAME và API_KEY trong .env để gọi {MODEL_PROVIDER}.")

    content = user
    if images:
        content = [{"type": "text", "text": user}]
        for image in images:
            content.extend([
                {"type": "text", "text": f"Ảnh hoặc khung hình có mã {image.ref}:"},
                {"type": "image_url", "image_url": {"url": image.data_url}},
            ])
    messages = [{"role": "system", "content": system}] if system else []
    messages.append({"role": "user", "content": content})
    payload = {"model": MODEL_NAME, "messages": messages}
    if schema is not None:
        payload["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": "review_analysis", "strict": True, "schema": schema},
        }
        if MODEL_PROVIDER == "openrouter":
            payload["provider"] = {"require_parameters": True}
    request = urllib.request.Request(
        url, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), method="POST",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"{MODEL_PROVIDER} trả HTTP {error.code}.") from None
    except (urllib.error.URLError, TimeoutError):
        raise RuntimeError(f"Không kết nối được với {MODEL_PROVIDER} trong thời gian chờ.") from None

    choice = data["choices"][0]
    message = choice["message"]
    usage = data["usage"]
    return {
        "text": (message.get("content") or "") if choice["finish_reason"] == "stop" else "",
        "model": data.get("model") or MODEL_NAME,
        "tokens_in": usage["prompt_tokens"],
        "tokens_out": usage["completion_tokens"],
    }
