"""Read-only adapter for local Shopee Collector exports."""

import csv
import json
from pathlib import Path
from urllib.parse import urlsplit

DEFAULT_OUTPUT_ROOT = (
    Path(__file__).resolve().parent.parent / "Shopee_Collector" / "output"
)
REQUIRED_FILES = ("coverage_report.json", "products.csv", "reviews.csv")


def _csv_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def _safe_media_path(root, value):
    if not isinstance(value, str) or not value:
        return None
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        return None
    try:
        resolved = (root / relative).resolve()
        resolved.relative_to(root.resolve())
    except (OSError, ValueError):
        return None
    return relative.as_posix() if resolved.is_file() else None


def _valid_product_url(value):
    try:
        parsed = urlsplit(value or "")
        return (
            parsed.scheme == "https"
            and parsed.hostname in {"shopee.vn", "www.shopee.vn"}
            and parsed.username is None
            and parsed.password is None
        )
    except ValueError:
        return False


def _media_by_review(folder):
    result = {}
    for filename, media_type, url_field, accepted_statuses in (
        ("images.csv", "image", "image_url", {"saved"}),
        ("videos.csv", "video_frame", "video_url", {"frame_only"}),
    ):
        path = folder / filename
        if not path.is_file():
            continue
        for row in _csv_rows(path):
            if (
                row.get("owner_kind") != "review"
                or row.get("role") != "review"
                or row.get("status") not in accepted_statuses
            ):
                continue
            local_path = _safe_media_path(folder, row.get("local_path"))
            review_key = row.get("review_key")
            if local_path and review_key:
                item = {
                    "type": media_type,
                    "path": local_path,
                    "source_url": row.get(url_field) or "",
                    "fallback_kind": row.get("fallback_kind") or "download",
                }
                if media_type == "video_frame":
                    item["analysis_note"] = row.get("analysis_note") or (
                        "One still frame only; do not infer motion or audio."
                    )
                result.setdefault(review_key, []).append(item)
    return result


def _load_export(folder):
    report = json.loads((folder / "coverage_report.json").read_text(encoding="utf-8"))
    products = {}
    for row in _csv_rows(folder / "products.csv"):
        url = row.get("url")
        product_key = row.get("product_key")
        if not product_key or not _valid_product_url(url):
            continue
        products[product_key] = {
            "product_id": product_key,
            "product_url": url,
            "title": row.get("name") or url,
            "reviews": [],
            "phone_models": {},
            "source_type": "collector",
            "source_label": "Dữ liệu collector đã crawl",
            "media_root": str(folder),
        }

    media = _media_by_review(folder)
    unmatched_variant_reviews = 0
    for row in _csv_rows(folder / "reviews.csv"):
        product = products.get(row.get("product_key"))
        if product is None:
            continue
        model = (row.get("phone_model") or "").strip()
        variant = (row.get("case_variant") or "").strip()
        if not model or not variant:
            unmatched_variant_reviews += 1
            continue
        try:
            stars = int(row.get("rating", ""))
        except (TypeError, ValueError):
            continue
        if stars < 1 or stars > 5:
            continue
        review = {
            "review_id": row.get("review_id") or row.get("review_key"),
            "phone_model": model,
            "case_variant": variant,
            "stars": stars,
            "text": row.get("content") or "",
            "helpful_count": _nonnegative_int(row.get("like_count")),
            "synthetic": False,
            "media": media.get(row.get("review_key"), []),
        }
        product["reviews"].append(review)
        model_entry = product["phone_models"].setdefault(
            model, {"phone_model": model, "case_variants": []}
        )
        if variant not in model_entry["case_variants"]:
            model_entry["case_variants"].append(variant)

    for product in products.values():
        product["sampling"] = report.get("review_sampling", {}).get(
            product["product_id"], {}
        )
        product["phone_models"] = sorted(
            product["phone_models"].values(), key=lambda item: item["phone_model"]
        )
        for model in product["phone_models"]:
            model["case_variants"].sort()

    return {
        "version": f"collector:{folder.name}",
        "source_type": "collector",
        "source_label": f"Dữ liệu collector · {folder.name}",
        "source_dir": str(folder),
        "media_root": str(folder),
        "products": list(products.values()),
        "review_sampling": report.get("review_sampling", {}),
        "unmatched_variant_reviews": unmatched_variant_reviews,
    }


def _nonnegative_int(value):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def load_latest_collector_dataset(output_root=None):
    root = Path(output_root) if output_root is not None else DEFAULT_OUTPUT_ROOT
    try:
        root = root.resolve()
        if not root.is_dir():
            return None
        candidates = [
            folder for folder in root.iterdir()
            if folder.is_dir()
            and all((folder / name).is_file() for name in REQUIRED_FILES)
        ]
        candidates.sort(
            key=lambda folder: (folder / "coverage_report.json").stat().st_mtime_ns,
            reverse=True,
        )
        for folder in candidates:
            try:
                resolved = folder.resolve()
                resolved.relative_to(root)
                return _load_export(resolved)
            except (OSError, ValueError, csv.Error, json.JSONDecodeError):
                continue
    except OSError:
        return None
    return None
