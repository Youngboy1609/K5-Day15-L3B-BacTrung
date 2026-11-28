from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit, urljoin

from .images import image_urls
from .videos import video_urls


def clean(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def fold(value):
    value = unicodedata.normalize("NFD", clean(value).lower().replace("đ", "d"))
    return "".join(c for c in value if unicodedata.category(c) != "Mn")


def ident(value):
    s = str(value) if value is not None else ""
    return s if re.fullmatch(r"[0-9]+", s) and int(s) > 0 else None


def canonical(url, base="https://shopee.vn/"):
    """Accept only Shopee VN URLs; strip tracking from product URLs."""
    p = urlsplit(urljoin(base, url))
    if p.scheme != "https" or p.hostname not in {"shopee.vn", "www.shopee.vn"}:
        return None
    if p.username or p.password or p.port not in (None, 443):
        return None
    m = re.search(r"(?:-i\.|/product/)(\d+)[./](\d+)(?:/|$)", p.path)
    if m:
        return f"https://shopee.vn/product/{m[1]}/{m[2]}"
    if any(s in p.path.lower() for s in ("/buyer", "/user", "/verify", "/cart", "/checkout")):
        return None
    return "https://shopee.vn" + (p.path or "/") + ("?" + p.query if p.query else "")


def product_ids(url):
    url = canonical(url)
    if not url:
        return None
    m = re.fullmatch(r"https://shopee.vn/product/(\d+)/(\d+)", url)
    return (m[1], m[2]) if m else None


def price(value, divisor):
    """Keep zero, reject negative/sentinel/NaN. Never guess units by magnitude."""
    if value is None or isinstance(value, bool):
        return None
    try:
        d, scale = Decimal(str(value)), Decimal(str(divisor))
        if not d.is_finite() or not scale.is_finite() or d < 0 or scale <= 0:
            return None
        result = format(d / scale, "f")
        return result.rstrip("0").rstrip(".") if "." in result else result
    except (InvalidOperation, ValueError, TypeError):
        return None


def integer(value):
    if isinstance(value, bool):
        return None
    try:
        d = Decimal(str(value))
        return int(d) if d.is_finite() and d >= 0 and d == int(d) else None
    except (InvalidOperation, ValueError, TypeError, OverflowError):
        return None


def timestamp_utc(value):
    """Normalize Unix seconds/milliseconds or an ISO timestamp with an offset."""
    try:
        number = integer(value)
        if number is not None:
            seconds = number / 1000 if number >= 100_000_000_000 else number
            dt = datetime.fromtimestamp(seconds, timezone.utc)
        elif isinstance(value, str):
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                return None
        else:
            return None
        return dt.astimezone(timezone.utc).isoformat()
    except (OSError, OverflowError, ValueError):
        return None


def first_count(node, *keys):
    for key in keys:
        count = integer(node.get(key))
        if count is not None:
            return count
    return None


def with_time_fields(node, prefix):
    raw = node.get("ctime")
    if raw is None:
        raw = node.get("created_at")
    if not isinstance(raw, (str, int, float)) or isinstance(raw, bool):
        raw = None
    return {f"{prefix}_raw": raw, f"{prefix}_utc": timestamp_utc(raw)}


def shop_reply_from(review):
    for key in ("item_rating_reply", "ItemRatingReply", "seller_reply", "shop_reply"):
        reply = review.get(key)
        if isinstance(reply, str) and reply.strip():
            return {"shop_reply_content": reply}
        if isinstance(reply, dict):
            content = reply.get("comment") or reply.get("content") or reply.get("text")
            if isinstance(content, str) and content.strip():
                return {"shop_reply_content": content, **with_time_fields(reply, "shop_reply_created_at")}
    return {}


def suggested_category(name, rules):
    text = " " + fold(name) + " "
    hits = []
    for rule in rules:
        matched = [w for w in rule["keywords"] if " " + fold(w) + " " in text]
        if matched:
            hits.append((len(matched), rule["label"], matched))
    if not hits:
        return {"suggested_category": "Chưa phân loại", "classification_method": "unclassified"}
    hits.sort(key=lambda h: (-h[0], h[1]))
    if len(hits) > 1 and hits[0][0] == hits[1][0]:
        return {"suggested_category": "Cần kiểm tra", "classification_method": "ambiguous_keyword"}
    return {"suggested_category": hits[0][1], "classification_method": "keyword_heuristic",
            "classification_evidence": ", ".join(hits[0][2])}


def walk(value, depth=0):
    if depth > 35:
        return
    if isinstance(value, dict):
        yield value
        for key, v in value.items():
            # Purchase snapshots describe the order at the time of review.
            if key == "product_items":
                continue
            yield from walk(v, depth + 1)
    elif isinstance(value, list):
        for v in value:
            yield from walk(v, depth + 1)


def categories_from(item):
    result = []
    for c in item.get("categories") or item.get("category_path") or []:
        if isinstance(c, dict):
            cid, name = c.get("catid", c.get("category_id")), c.get("display_name") or c.get("name")
            if name or cid:
                result.append({"category_id": str(cid) if cid is not None else None,
                               "name": clean(name) or None})
        elif isinstance(c, str):
            result.append({"category_id": None, "name": c})
    if not result and item.get("catid") is not None:
        result = [{"category_id": str(item["catid"]), "name": None}]
    return result


def videos_from(node):
    return video_urls(*(node.get(key) for key in ("video", "videos", "video_urls",
                                                  "video_info", "video_info_list", "video_list")))


def explicit_variant(value):
    return clean(value) if isinstance(value, str) and clean(value) else None


def page_bundle(view, expected_url, observed_at, rules=()):
    ids = product_ids(expected_url)
    if not view or not ids or product_ids(view.get("url") or "") != ids or not clean(view.get("name")):
        return {}
    tiers = view.get("tiers") or []
    rating = clean(view.get("rating")).replace(",", ".")
    count = clean(view.get("rating_count_display"))
    item = {"shopid": ids[0], "itemid": ids[1], "name": view["name"],
            "description": view.get("description"), "attributes": view.get("attributes"),
            "categories": view.get("categories"), "tier_variations": tiers,
            "shop_info": {"name": view.get("shop_name"), "username": view.get("shop_username")},
            "image": view.get("cover"), "images": view.get("gallery_images"), "videos": view.get("videos"),
            "item_rating": {"rating_star": float(rating) if re.fullmatch(r"[0-5](?:\.\d+)?", rating) else None,
                            "rating_count": int(count) if count.isdecimal() else None}}
    p = normalize_item(item, 1, rules, canonical(expected_url), observed_at)
    p.update(source_kind="product_page", sold_display=view.get("sold_display"),
             description_image_urls=image_urls(view.get("description_images")),
             price_display_text=view.get("price_text"), rating_count_display=count)
    if view.get("description_section_seen"):
        p["description_media_status"] = ("images_observed" if p["description_image_urls"] else
                                         "no_supported_images_in_rendered_section")
    # The price section may explicitly label a voucher or show a range.
    line = (view.get("price_text") or "").strip().splitlines()
    if line:
        vnd = r"(\d{1,3}(?:\.\d{3})+|\d+)"
        match = re.fullmatch(r"₫?\s*" + vnd + r"\s*₫?(?:\s*[-–]\s*₫?\s*" + vnd + r"\s*₫?)?", line[0].strip())
        if match and "₫" in line[0]:
            low = match[1].replace(".", "")
            high = (match[2] or match[1]).replace(".", "")
            p.update(price=low if low == high else None, price_min=low, price_max=high,
                     price_raw=low if low == high else None, currency="VND", currency_assumed=False,
                     price_unit_status="displayed_vnd_after_voucher" if "voucher" in fold(view["price_text"])
                     else "displayed_vnd")
    if len(tiers) == 1:
        tier = tiers[0]
        p["variants"] = [{"variant_name": name, "options": {tier["name"]: name}}
                         for name in tier["options"]]
        p["variant_capture_status"] = "single_tier_options_observed"
    reviews = []
    for row in view.get("reviews", []):
        rid = ident(row.get("id"))
        if rid:
            reviews.append({"review_key": f"{p['product_key']}:{rid}", "product_key": p["product_key"],
                            "review_id": rid, "shop_id": ids[0], "item_id": ids[1],
                            "phone_model": explicit_variant(row.get("phone_model")),
                            "case_variant": explicit_variant(row.get("case_variant")),
                            "created_at_display": row.get("time"), "like_count": integer(row.get("like")),
                            "dislike_count": integer(row.get("dislike")), "shop_reply_content": row.get("reply") or None,
                            "image_urls": image_urls(row.get("images")), "video_urls": video_urls(row.get("videos")),
                            "content": row.get("comment") or None, "content_status": "with_text" if row.get("comment") else None,
                            "source_url": canonical(expected_url), "observed_at": observed_at})
    return {"products": [p], "reviews": reviews}


def normalize_item(item, divisor, rules, source_url, observed_at):
    sid, iid = ident(item.get("shopid")), ident(item.get("itemid"))
    if not sid or not iid or not clean(item.get("name")):
        return None
    tiers = item.get("tier_variations") or []
    models = item.get("models")
    variants = []
    if isinstance(models, list):
        for m in models:
            if not isinstance(m, dict):
                continue
            options = {}
            for index, option_index in enumerate((m.get("extinfo") or {}).get("tier_index") or []):
                if index < len(tiers) and isinstance(tiers[index], dict):
                    tier = tiers[index]
                    opts = tier.get("options") or []
                    if isinstance(option_index, int) and 0 <= option_index < len(opts):
                        options[clean(tier.get("name")) or f"tier_{index}"] = opts[option_index]
            variant_price = m.get("price")
            if variant_price is None:
                variant_price = (m.get("price_info") or {}).get("price")
            variants.append({"variant_id": ident(m.get("modelid")), "variant_name": clean(m.get("name")),
                             "options": options, "price_raw": variant_price,
                             "price": price(variant_price, divisor),
                             "stock": integer(m.get("stock")),
                             "currency": item.get("currency") or "VND",
                             "price_divisor": divisor})
    rating = item.get("item_rating") or {}
    shop = item.get("shop_info") or item.get("shop") or {}
    cats = categories_from(item)
    attr = item.get("attributes") or []
    attr = [{"name": a.get("name"), "value": a.get("value") or a.get("values")}
            for a in attr if isinstance(a, dict)]
    rich = item.get("extended_description") or {}
    sections = (rich.get("field_list") or []) if isinstance(rich, dict) else []
    sections = [s for s in sections if isinstance(s, dict)]
    description_images = []
    for section in sections:
        image = section.get("image_info")
        if isinstance(image, dict):
            description_images.extend(image_urls(image, image.get("image_id_list"), image.get("url_list")))
    description = item.get("description") or "\n".join(
        s["text"] for s in sections if isinstance(s.get("text"), str))
    product = {
        "product_key": f"{sid}:{iid}", "shop_id": sid, "item_id": iid,
        "url": f"https://shopee.vn/product/{sid}/{iid}", "name": clean(item.get("name")),
        "description": description, "currency": item.get("currency") or "VND",
        "currency_assumed": not bool(item.get("currency")),
        "price_raw": item.get("price"), "price": price(item.get("price"), divisor),
        "price_min": price(item.get("price_min"), divisor),
        "price_max": price(item.get("price_max"), divisor),
        "price_divisor": divisor, "price_unit_status": "configured_adapter_assumption",
        "shop_name": clean(shop.get("name") or item.get("shop_name")) or None,
        "shop_username": clean(shop.get("username")) or None,
        "rating_average": rating.get("rating_star"),
        "rating_count": (rating.get("rating_count") or [None])[0] if isinstance(rating.get("rating_count"), list)
                        else integer(rating.get("rating_count")),
        "sold_period_reported": integer(item.get("sold")),
        "sold_total_reported": integer(item.get("historical_sold")),
        "sold_semantics": "upstream_fields_unverified; do not equate period and total",
        "category_path": cats, "attributes": attr, "images": item.get("images") or [],
        "cover_image_url": next(iter(image_urls(item.get("image"), item.get("images"))), None),
        "gallery_image_urls": image_urls(item.get("images")),
        "description_image_urls": list(dict.fromkeys(description_images)),
        "image_urls": image_urls(item.get("images"), item.get("image")),
        "variant_options": [{"name": clean(t.get("name")), "options": t["options"]}
                            for t in tiers if isinstance(t, dict) and t.get("options")],
        "video_urls": videos_from(item),
        "variants": variants,
        "variant_capture_status": "models_observed" if variants else "not_observed",
        "record_level": "detail" if any(k in item for k in ("description", "models", "tier_variations", "attributes")) else "listing",
        "source_kind": "browser_response", "source_url": source_url,
        "observed_at": observed_at,
    }
    product.update(suggested_category(product["name"], rules))
    if any(c.get("name") for c in cats):
        product["classification_method"] = "shopee_category_observed"
    return product


def extract_payload(payload, *, divisor=100000, rules=(), source_url="", observed_at="", review_product=None):
    """Adapter for *observed* JSON. Shapes are provisional, not official API contracts."""
    products, reviews, shops = [], [], []
    for node in walk(payload):
        p = normalize_item(node, divisor, rules, source_url, observed_at)
        if p:
            products.append(p)
        sid = ident(node.get("shopid"))
        if sid and not node.get("itemid") and (node.get("username") or node.get("shop_name")):
            shops.append({"shop_id": sid, "shop_name": clean(node.get("shop_name") or node.get("name")) or None,
                          "shop_username": clean(node.get("username")) or None, "observed_at": observed_at})
        # An unrelated response must never be assigned to the current product.
        # Fallback identity is provided only for a matching ratings request.
        if "rating_star" in node and ("cmtid" in node or "comment" in node):
            iid = ident(node.get("itemid"))
            review_sid = ident(node.get("shopid"))
            if review_product:
                if iid and iid != review_product[1] or review_sid and review_sid != review_product[0]:
                    continue
                iid, review_sid = iid or review_product[1], review_sid or review_product[0]
            if not iid or not review_sid:
                continue
            rid = ident(node.get("cmtid"))
            # Without a stable source ID, do not merge potentially distinct same-text reviews.
            if not rid:
                continue
            reviews.append({"review_key": f"{review_sid}:{iid}:{rid}", "review_id": rid,
                            "product_key": f"{review_sid}:{iid}", "shop_id": review_sid, "item_id": iid,
                            "phone_model": explicit_variant(node.get("phone_model")),
                            "case_variant": explicit_variant(node.get("case_variant")),
                            "rating": node.get("rating_star"), "content": node.get("comment"),
                            "content_status": ("with_text" if clean(node.get("comment")) else
                                               "empty_at_source" if isinstance(node.get("comment"), str) else None),
                            **with_time_fields(node, "created_at"),
                            "variant_name": node.get("product_items"),
                            "like_count": first_count(node, "like_count", "like_cnt"),
                            "dislike_count": first_count(node, "dislike_count", "dislike_cnt"),
                            "image_urls": image_urls(node.get("images"), node.get("image_urls"), node.get("image_ids")),
                            "video_urls": videos_from(node),
                            **shop_reply_from(node),
                            "observed_at": observed_at, "source_url": source_url})
    return {"products": products, "reviews": reviews, "shops": shops}


def jsonld_products(payload, url, observed_at, rules=()):
    ids = product_ids(url)
    if not ids:
        return []
    result = []
    for node in walk(payload):
        types = node.get("@type") or []
        if isinstance(types, str):
            types = [types]
        if "Product" not in types or not node.get("name"):
            continue
        # Refuse embedded recommendations whose URL explicitly points elsewhere.
        if node.get("url") and product_ids(node["url"]) != ids:
            continue
        offer = node.get("offers") or {}
        offer = offer[0] if isinstance(offer, list) and offer else offer
        if not isinstance(offer, dict):
            offer = {}
        aggregate = node.get("aggregateRating") or {}
        seller = offer.get("seller") or {}
        p = normalize_item({"shopid": ids[0], "itemid": ids[1], "name": node["name"],
                            "description": node.get("description"), "currency": offer.get("priceCurrency"),
                            "images": node.get("image"),
                            "videos": node.get("video"),
                            "shop_name": seller.get("name") if isinstance(seller, dict) else None,
                            "price": offer.get("price"), "price_min": offer.get("lowPrice"),
                            "price_max": offer.get("highPrice"),
                            "item_rating": {"rating_star": aggregate.get("ratingValue"),
                                            "rating_count": aggregate.get("ratingCount", aggregate.get("reviewCount"))}},
                           1, rules, url, observed_at)
        p.update(source_kind="jsonld", price_unit_status="jsonld_currency_units",
                 variant_capture_status="not_observed", record_level="jsonld")
        result.append(p)
    return result
