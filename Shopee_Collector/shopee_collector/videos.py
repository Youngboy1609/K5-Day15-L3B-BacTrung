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


VIDEO_HOST = re.compile(
    r"(?:[a-z0-9-]+\.)*vod\.(?:susercontent\.com|shopee\.com)|(?:cvf|cf)\.shopee\.vn"
)
VIDEO_PATH = re.compile(r"/[a-zA-Z0-9_./%-]+")
STREAM_EXTENSIONS = (".m3u8", ".mpd")
MAX_VIDEO_BYTES = 250 * 1024 * 1024
CHUNK_BYTES = 256 * 1024


def video_url(value):
    if not isinstance(value, str):
        return None
    value = value.strip()
    try:
        parsed = urlsplit("https:" + value if value.startswith("//") else value)
        host = parsed.netloc.lower()
        if parsed.scheme == "https" and VIDEO_HOST.fullmatch(host) and VIDEO_PATH.fullmatch(parsed.path):
            if host.startswith(("cvf.", "cf.")) and not parsed.path.lower().endswith(
                    (".mp4", ".webm", ".mov", *STREAM_EXTENSIONS)):
                return None
            return f"https://{host}{parsed.path}"
    except ValueError:
        pass
    return None


def video_urls(*values):
    """Follow only media fields within structured video data."""
    def references(value, remaining):
        if remaining < 0:
            return
        if isinstance(value, str):
            if url := video_url(value):
                yield url
        elif isinstance(value, list):
            for entry in value:
                yield from references(entry, remaining - 1)
        elif isinstance(value, dict):
            for key in ("url", "contentUrl", "video_url", "play_url", "download_url", "video_urls",
                        "default_format", "formats", "sources", "url_list", "video_list", "videos"):
                yield from references(value.get(key), remaining - 1)

    return list(dict.fromkeys(url for value in values for url in references(value, 8)))


def video_extension(header):
    if header[4:8] == b"ftyp":
        if header[8:12] in (b"avif", b"avis", b"heic", b"mif1", b"M4A "):
            return None
        return "mov" if header[8:12] == b"qt  " else "mp4"
    if header.startswith(b"\x1a\x45\xdf\xa3") and b"webm" in header:
        return "webm"
    return None


def fetch_video(folder: Path, url):
    if video_url(url) != url:
        return {"status": "unsupported_url"}
    if urlsplit(url).path.lower().endswith(STREAM_EXTENSIONS):
        return {"status": "unsupported_stream"}
    opener = build_opener(NoRedirect())
    temporary = None
    try:
        with opener.open(Request(url, headers={"Accept": "video/*, application/octet-stream"}), timeout=20) as response:
            content_type = response.headers.get_content_type()
            if content_type in {"application/vnd.apple.mpegurl", "application/x-mpegurl", "application/dash+xml"}:
                return {"status": "unsupported_stream"}
            if response.status != 200 or response.headers.get("Content-Range"):
                return {"status": "partial_response"}
            if not (content_type.startswith("video/") or content_type == "application/octet-stream"):
                return {"status": "unsupported_video"}
            size_header = response.headers.get("Content-Length", "")
            expected = None
            if size_header.isascii() and size_header.isdecimal():
                if len(size_header) > 20:
                    return {"status": "too_large"}
                expected = int(size_header)
            if expected is not None and expected > MAX_VIDEO_BYTES:
                return {"status": "too_large"}
            header = response.read(1024)
            extension = video_extension(header)
            if not extension:
                return {"status": "unsupported_video"}
            relative = Path("videos") / f"{hashlib.sha256(url.encode()).hexdigest()}.{extension}"
            path = folder / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            total = len(header)
            with NamedTemporaryFile(dir=path.parent, suffix=".part", delete=False) as file:
                temporary = Path(file.name)
                file.write(header)
                while chunk := response.read(CHUNK_BYTES):
                    total += len(chunk)
                    if total > MAX_VIDEO_BYTES:
                        return {"status": "too_large"}
                    file.write(chunk)
            if expected is not None and total != expected:
                return {"status": "partial_response"}
        temporary.replace(path)
        return {"status": "saved", "local_path": relative.as_posix(), "bytes": total}
    except HTTPError as exc:
        code = exc.code
        exc.close()
        return {"status": f"http_{code}", "http_status": code}
    except (OSError, HTTPException) as exc:
        return {"status": "download_error", "error": type(exc).__name__}
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


async def download_videos(store, blocked, urls=None):
    return await download_assets(store, "video", fetch_video, blocked, urls)
