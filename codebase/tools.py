"""Read-only local fixture lookup for the Shopee phone-case CP2 demo."""
import json
import os
import random
from collections import defaultdict
from urllib.parse import urlsplit

from tracing import tool

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(ROOT, "data", "reviews.json")
MAX_REVIEWS = 12
ALLOWED_HOSTS = {"shopee.vn", "www.shopee.vn"}


def _valid_shopee_url(value):
    if not isinstance(value, str) or len(value) > 500:
        return False
    try:
        parsed = urlsplit(value)
        return (
            parsed.scheme == "https"
            and parsed.hostname in ALLOWED_HOSTS
            and parsed.username is None
            and parsed.password is None
            and parsed.port is None
            and not parsed.query
            and not parsed.fragment
        )
    except ValueError:
        return False


def _load_products():
    with open(DATA_PATH, encoding="utf-8") as source:
        data = json.load(source)
    products = data.get("products")
    if not isinstance(products, list):
        raise ValueError("data/reviews.json must contain a products list")
    return data, products


def _sample_by_stars(reviews, limit=MAX_REVIEWS, seed=42):
    """Sample deterministically by star group, keeping every represented group."""
    if len(reviews) <= limit:
        return sorted(reviews, key=lambda item: item["review_id"])

    buckets = defaultdict(list)
    for review in reviews:
        buckets[int(review["stars"])].append(review)
    stars = sorted(buckets)
    quota = {star: 0 for star in stars}

    for star in stars[:limit]:
        quota[star] = 1
    remaining = limit - sum(quota.values())
    while remaining:
        capacity = {star: len(buckets[star]) - quota[star] for star in stars}
        total_capacity = sum(capacity.values())
        if total_capacity <= 0:
            break
        exact = {star: remaining * capacity[star] / total_capacity for star in stars}
        allocation = {star: min(capacity[star], int(exact[star])) for star in stars}
        used = sum(allocation.values())
        for star, count in allocation.items():
            quota[star] += count
        remaining -= used
        if not remaining:
            break
        order = sorted(stars, key=lambda star: (-(exact[star] - allocation[star]), star))
        progressed = False
        for star in order:
            if remaining and quota[star] < len(buckets[star]):
                quota[star] += 1
                remaining -= 1
                progressed = True
        if not progressed:
            break

    selected = []
    for star in stars:
        pool = sorted(buckets[star], key=lambda item: item["review_id"])
        selected.extend(random.Random(seed + star).sample(pool, quota[star]))
    return sorted(selected, key=lambda item: item["review_id"])


@tool
def get_product_reviews(product_url, phone_model, case_variant, limit=MAX_REVIEWS, seed=42):
    """Look up a registered local listing and exact-model/variant reviews.
    Input: Shopee URL, phone model, case variant, sample limit and seed.
    Output: listing metadata, matching reviews and counts, or typed error.
    External side effect: none; reads only the local synthetic fixture.
    """
    if not _valid_shopee_url(product_url):
        return {"status": "error", "code": "INVALID_INPUT", "message": "Hãy nhập URL HTTPS của shopee.vn."}
    if not isinstance(phone_model, str) or not phone_model.strip() or len(phone_model) > 100:
        return {"status": "error", "code": "INVALID_INPUT", "message": "Cần chọn dòng điện thoại."}
    if not isinstance(case_variant, str) or not case_variant.strip() or len(case_variant) > 120:
        return {"status": "error", "code": "INVALID_INPUT", "message": "Cần chọn biến thể ốp."}
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= MAX_REVIEWS:
        return {"status": "error", "code": "INVALID_INPUT", "message": "Số review mỗi lần phải từ 1 đến 12."}
    if not isinstance(seed, int) or isinstance(seed, bool):
        return {"status": "error", "code": "INVALID_INPUT", "message": "Seed lấy mẫu phải là số nguyên."}

    data, products = _load_products()
    product = next((item for item in products if item.get("product_url") == product_url), None)
    if product is None:
        return {
            "status": "error",
            "code": "NO_LOCAL_DEMO_DATA",
            "message": "Chưa có review cục bộ cho link này; demo không truy cập Shopee.",
        }

    model = phone_model.strip()
    variant = case_variant.strip()
    product_reviews = product.get("reviews", [])
    variants = sorted({
        item["case_variant"]
        for item in product_reviews
        if item.get("phone_model") == model and item.get("case_variant")
    })
    if variant not in variants:
        return {
            "status": "needs_input",
            "code": "VARIANT_NOT_FOUND",
            "message": "Chưa có review đúng biến thể cho dòng máy đã chọn; hãy chọn lại.",
            "available_variants": variants,
        }

    eligible = [
        item for item in product_reviews
        if item.get("phone_model") == model and item.get("case_variant") == variant
    ]
    sampled = _sample_by_stars(eligible, limit=min(limit, MAX_REVIEWS), seed=seed)
    star_counts = {
        str(star): sum(item.get("stars") == star for item in eligible)
        for star in range(1, 6)
        if any(item.get("stars") == star for item in eligible)
    }
    sampled_star_counts = {
        str(star): sum(item.get("stars") == star for item in sampled)
        for star in range(1, 6)
        if any(item.get("stars") == star for item in sampled)
    }
    return {
        "status": "ok",
        "dataset_version": data.get("version", "unversioned"),
        "product_id": product["product_id"],
        "product_title": product["title"],
        "phone_model": model,
        "case_variant": variant,
        "eligible_count": len(eligible),
        "star_counts": star_counts,
        "sampled_star_counts": sampled_star_counts,
        "sample_limit": min(limit, MAX_REVIEWS),
        "sample_seed": seed,
        "reviews": sampled,
    }
