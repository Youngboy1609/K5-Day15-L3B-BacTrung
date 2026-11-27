from __future__ import annotations

import hashlib
import re
from http.client import HTTPException
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener

from .media import NoRedirect, download_assets


CDN = "down-vn.img.susercontent.com"
CDN_HOSTS = {CDN, "down-vn.img.shopee.vn", "cf.shopee.vn"}
IMAGE_ID = re.compile(r"[A-Za-z0-9_-]{12,180}(?:\.(?:jpg|jpeg|png|webp|gif|avif))?", re.I)
MAX_BYTES = 20 * 1024 * 1024


def image_url(value):
    if not isinstance(value, str):
        return None
    value = value.strip()
    if IMAGE_ID.fullmatch(value):
        return f"https://{CDN}/file/{value}"
    try:
        parsed = urlsplit("https:" + value if value.startswith("//") else value)
        file_id = parsed.path.removeprefix("/file/")
        if (parsed.scheme == "https" and parsed.netloc.lower() in CDN_HOSTS
                and parsed.path.startswith("/file/") and IMAGE_ID.fullmatch(file_id)):
            return f"https://{parsed.netloc.lower()}/file/{file_id}"
    except ValueError:
        pass
    return None


def image_urls(*values):
    urls = {}
    for value in values:
        for entry in value if isinstance(value, list) else [value]:
            if isinstance(entry, dict):
                candidates = (entry.get(key) for key in ("url", "id", "image_id", "image_url", "contentUrl"))
            else:
                candidates = [entry]
            for candidate in candidates:
                url = image_url(candidate)
                if url:
                    urls[url] = None
                    break
    return list(urls)


def image_extension(data):
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "webp"
    if data[4:8] == b"ftyp" and data[8:12] in (b"avif", b"avis"):
        return "avif"
    return None


def fetch_image(folder: Path, url):
    """Download one public CDN asset without browser credentials or redirects."""
    if image_url(url) != url:
        return {"status": "unsupported_url"}
    opener = build_opener(NoRedirect())
    try:
        with opener.open(Request(url, headers={"Accept": "image/*"}), timeout=12) as response:
            if response.status != 200 or response.headers.get("Content-Range"):
                return {"status": "partial_response"}
            if not response.headers.get_content_type().startswith("image/"):
                return {"status": "unsupported_image"}
            size = response.headers.get("Content-Length", "")
            data = response.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            return {"status": "too_large"}
        if size.isdecimal() and size != str(len(data)):
            return {"status": "partial_response"}
        extension = image_extension(data)
        if not extension:
            return {"status": "unsupported_image"}
        name = hashlib.sha256(url.encode()).hexdigest()
        relative = Path("images") / f"{name}.{extension}"
        path = folder / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with NamedTemporaryFile(dir=path.parent, suffix=".part", delete=False) as file:
                temporary = Path(file.name)
                file.write(data)
            temporary.replace(path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        return {"status": "saved", "local_path": relative.as_posix(), "bytes": len(data)}
    except HTTPError as exc:
        code = exc.code
        exc.close()
        return {"status": f"http_{code}", "http_status": code}
    except (OSError, HTTPException) as exc:
        return {"status": "download_error", "error": type(exc).__name__}


async def download_images(store, blocked, urls=None):
    return await download_assets(store, "image", fetch_image, blocked, urls)
