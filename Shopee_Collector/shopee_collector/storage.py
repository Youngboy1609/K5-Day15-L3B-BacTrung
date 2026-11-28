from __future__ import annotations

import csv
import json
import sqlite3
from collections import Counter
from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile
from .parsing import product_ids, timestamp_utc


def detail_fields(p):
    return {
        "name": bool(p.get("name")), "description": bool(p.get("description")),
        "price": any(p.get(k) is not None for k in ("price", "price_min", "price_max")),
        "rating": p.get("rating_average") is not None, "shop_name": bool(p.get("shop_name")),
        "sold": bool(p.get("sold_display")) or any(p.get(k) is not None for k in ("sold_period_reported", "sold_total_reported")),
        "categories": any(c.get("name") for c in p.get("category_path", [])),
        "attributes": any(a.get("name") and a.get("value") for a in p.get("attributes", [])),
        "variant_options_or_models": bool(p.get("variants") or p.get("variant_options")),
        "cover_image": bool(p.get("cover_image_url")), "gallery": bool(p.get("gallery_image_urls")),
    }


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def csv_value(value):
    if isinstance(value, (list, dict)):
        value = encode(value)
    # Product names/reviews are untrusted; prevent formula execution in Excel.
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


@contextmanager
def export_file(path, encoding):
    temporary = NamedTemporaryFile(mode="w", dir=path.parent, prefix=path.name + ".",
                                  suffix=".tmp", encoding=encoding, newline="", delete=False)
    staged = Path(temporary.name)
    try:
        with temporary as stream:
            yield stream
        staged.replace(path)
    finally:
        staged.unlink(missing_ok=True)


class Store:
    def __init__(self, folder, *, recover_queue=True):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.folder / "catalog.sqlite3")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript('''
          CREATE TABLE IF NOT EXISTS entities(kind TEXT, key TEXT, data TEXT, PRIMARY KEY(kind,key));
          CREATE TABLE IF NOT EXISTS observations(id INTEGER PRIMARY KEY, product_key TEXT, data TEXT);
          CREATE TABLE IF NOT EXISTS queue(url TEXT PRIMARY KEY, kind TEXT, status TEXT DEFAULT 'pending',
             attempts INTEGER DEFAULT 0, last_error TEXT, updated_at TEXT);
          CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, at TEXT, kind TEXT, message TEXT);
        ''')
        if recover_queue:
            self.recover_running_jobs()

    def recover_running_jobs(self):
        with self.db:
            self.db.execute("UPDATE queue SET status='pending' WHERE status IN ('running','review_paused')")

    def get(self, kind, key):
        r = self.db.execute("SELECT data FROM entities WHERE kind=? AND key=?", (kind, key)).fetchone()
        return json.loads(r[0]) if r else None

    def rows(self, kind):
        return [json.loads(r[0]) for r in self.db.execute(
            "SELECT data FROM entities WHERE kind=? ORDER BY key", (kind,))]

    def product_reviews(self, key):
        return [json.loads(r[0]) for r in self.db.execute(
            "SELECT data FROM entities WHERE kind='review' AND key GLOB ?", (key + ":*",))]

    def put(self, kind, key, data):
        self.db.execute("INSERT INTO entities VALUES(?,?,?) ON CONFLICT(kind,key) DO UPDATE SET data=excluded.data",
                        (kind, key, encode(data)))

    def ingest(self, bundle, *, review_page=None):
        with self.db:
            self._merge_bundle(bundle)
            if review_page:
                key, number, at = review_page
                reviews = bundle["reviews"]
                if not reviews or any(r["product_key"] != key for r in reviews):
                    raise ValueError("Review page does not match saved reviews")
                progress = self.get("review_progress", key) or {}
                if number == progress.get("next_page", 1):
                    self.put("review_progress", key, {
                        "product_key": key, "pages_observed": number, "next_page": number + 1,
                        "last_review_ids": [r["review_id"] for r in reviews],
                        "stop_reason": "page_saved", "at": at,
                    })

    def _merge_bundle(self, bundle):
        for shop in bundle.get("shops", []):
            old = self.get("shop", shop["shop_id"]) or {}
            old.update({k: v for k, v in shop.items() if v is not None})
            self.put("shop", shop["shop_id"], old)
        for p in bundle.get("products", []):
            self.db.execute("INSERT INTO observations(product_key,data) VALUES(?,?)", (p["product_key"], encode(p)))
            old = self.get("product", p["product_key"]) or {}
            sources = old.get("field_observations", {})
            price_fields = {"price", "price_raw", "price_min", "price_max", "price_divisor",
                            "price_unit_status", "currency", "currency_assumed"}
            has_price = any(p.get(k) is not None for k in ("price", "price_min", "price_max"))
            if p["source_kind"] == "product_page" and old.get("price") is not None and old.get("price_unit_status") not in ("displayed_vnd", "displayed_vnd_after_voucher"):
                has_price = False
            if has_price:
                # Price values and units are one observation: do not mix JSON-LD units
                # with an older scaled API value.
                for k in price_fields:
                    old[k] = p.get(k)
                    sources[k] = {"at": p["observed_at"], "source": p["source_kind"]}
            for k, v in p.items():
                if k in price_fields:
                    continue
                if v is None or v == [] or v == {} or v == "":
                    continue
                if k in ("image_urls", "gallery_image_urls", "description_image_urls", "video_urls"):
                    v = list(dict.fromkeys([*old.get(k, []), *v]))
                if k in ("variants", "variant_capture_status") and old.get("variant_capture_status") == "models_observed" and p.get("variant_capture_status") == "single_tier_options_observed":
                    continue
                if k == "category_path" and any(c.get("name") for c in old.get(k, [])) and not any(c.get("name") for c in v):
                    continue
                if k in {"record_level", "variant_capture_status", "classification_method"} and old.get(k):
                    if k == "record_level" and old[k] == "detail" and v != "detail":
                        continue
                    if k == "variant_capture_status" and v == "not_observed":
                        continue
                    if k == "classification_method" and old[k] == "shopee_category_observed" and v != old[k]:
                        continue
                old[k] = v
                sources[k] = {"at": p["observed_at"], "source": p["source_kind"]}
            old["field_observations"] = sources
            self.put("product", p["product_key"], old)
        for review in bundle.get("reviews", []):
            key = review["review_key"]
            old = self.get("review", key) or {}
            if review.get("shop_reply_content") and review["shop_reply_content"] != old.get("shop_reply_content"):
                old.pop("shop_reply_created_at_raw", None)
                old.pop("shop_reply_created_at_utc", None)
            review = review.copy()
            for field in ("image_urls", "video_urls"):
                if review.get(field):
                    review[field] = list(dict.fromkeys([*old.get(field, []), *review[field]]))
            if old.get("content") and not review.get("content"):
                review.pop("content_status", None)
            if old.get("content") and review.get("source_url") == f"https://shopee.vn/product/{review.get('shop_id')}/{review.get('item_id')}":
                review.pop("content", None)
            old.update({k: v for k, v in review.items() if v not in (None, [], "")})
            self.put("review", key, old)

    def review_stop(self, key, reason, at):
        with self.db:
            progress = self.get("review_progress", key) or {"product_key": key, "pages_observed": 0}
            progress.update(stop_reason=reason, at=at)
            self.put("review_progress", key, progress)

    def media_links(self, media_kind, products=None, reviews=None):
        for kind, records in (("product", products), ("review", reviews)):
            for record in records if records is not None else self.rows(kind):
                if media_kind == "image" and kind == "product":
                    groups = {"cover": [record.get("cover_image_url")],
                              "gallery": record.get("gallery_image_urls", record.get("image_urls", [])),
                              "description": record.get("description_image_urls", [])}
                else:
                    groups = {kind: record.get(f"{media_kind}_urls", [])}
                for role, urls in groups.items():
                    for url in dict.fromkeys(filter(None, urls)):
                        yield {"owner_kind": kind, "role": role, "product_key": record["product_key"],
                               "review_key": record.get("review_key"), f"{media_kind}_url": url}

    def media_manifest(self, kind, products, reviews):
        saved = {key: json.loads(data) for key, data in self.db.execute(
            "SELECT key,data FROM entities WHERE kind=?", (kind,))}
        manifest = []
        for link in self.media_links(kind, products, reviews):
            asset = saved.get(link[f"{kind}_url"], {"status": "pending"})
            if asset["status"] == "saved" and not self.file_saved(asset):
                asset = {"status": "file_missing_or_incomplete"}
            manifest.append({**link, **asset})
        return manifest

    def file_saved(self, asset):
        path = self.folder / asset.get("local_path", "")
        return path.is_file() and path.stat().st_size == asset.get("bytes") and asset.get("bytes", 0) > 0

    def enqueue(self, url, kind, now):
        self.enqueue_many([(url, kind)], now)

    def enqueue_many(self, jobs, now):
        """Insert a discovery batch with one transaction instead of one per link."""
        self.db.executemany(
            "INSERT OR IGNORE INTO queue(url,kind,updated_at) VALUES(?,?,?)",
            ((url, kind, now) for url, kind in jobs),
        )
        self.db.commit()

    def queue_size(self):
        return self.db.execute("SELECT COUNT(*) FROM queue").fetchone()[0]

    def next_job(self, prefer_listings=False):
        first_kind = "listing" if prefer_listings else "product"
        r = self.db.execute(
            "SELECT url,kind FROM queue WHERE status='pending' "
            "ORDER BY CASE WHEN kind=? THEN 0 ELSE 1 END, rowid LIMIT 1",
            (first_kind,),
        ).fetchone()
        return {"url": r[0], "kind": r[1]} if r else None

    def status(self, url, status, now, error=None):
        self.db.execute("UPDATE queue SET status=?, updated_at=?, last_error=?, attempts=attempts+? WHERE url=?",
                        (status, now, error, int(status == "running"), url))
        self.db.commit()

    def event(self, now, kind, message):
        self.db.execute("INSERT INTO events(at,kind,message) VALUES(?,?,?)", (now, kind, message))
        self.db.commit()

    def retry(self, max_attempts=2, *, confirmed_access=False):
        self.db.execute(
            "UPDATE queue SET status='pending' "
            "WHERE (status IN ('blocked','failed','no_data') AND attempts < ?) "
            "OR (status='blocked' AND ?) OR status='review_paused'",
            (max_attempts, confirmed_access),
        )
        self.db.commit()

    def blocked_job(self):
        return self.db.execute("SELECT url FROM queue WHERE status='blocked' LIMIT 1").fetchone()

    def refresh_products(self, urls):
        with self.db:
            self.db.executemany("UPDATE queue SET status='pending' WHERE url=? AND kind='product' "
                                "AND status IN ('partial','covered','detail_complete','no_data')",
                                ((url,) for url in urls))

    def record_scope(self, config):
        with self.db:
            self.put("run_settings", "scope", {
                "seed_product_keys": [":".join(ids) for url in config.get("seeds", []) if (ids := product_ids(url))],
                "required_fields": config.get("detail_required_fields", []),
                "max_reviews_per_product": config.get("max_reviews_per_product", 100),
                "all_review_pages": bool(config.get("all_review_pages")),
            })

    def report(self):
        products, reviews = self.rows("product"), self.rows("review")
        checks = {}
        for p in products:
            if not p.get("shop_name"):
                p["shop_name"] = (self.get("shop", p["shop_id"]) or {}).get("shop_name")
            checks[p["product_key"]] = detail_fields(p)
        field_counts = {k: sum(fields[k] for fields in checks.values()) for k in detail_fields({})}
        scope = self.get("run_settings", "scope") or {}
        by_key = {p["product_key"]: p for p in products}
        required = scope.get("required_fields", [])
        seed_keys = scope.get("seed_product_keys", [])
        seed_checks = {key: {field: by_key.get(key, {}).get(field) not in (None, "", [], {})
                             for field in required} for key in seed_keys}
        media = {}
        for kind, roles in (("image", ("cover", "gallery", "description", "review")), ("video", ("product", "review"))):
            manifest = self.media_manifest(kind, products, reviews)
            for role in roles:
                rows = [r for r in manifest if r["role"] == role]
                media[f"{role}_{kind}"] = {"observed_urls": len({r[f"{kind}_url"] for r in rows}),
                                           "saved_files": len({r["local_path"] for r in rows if r["status"] == "saved"}),
                                           "frame_only_files": len({r["local_path"] for r in rows if r["status"] == "frame_only"}),
                                           "products_with_files": len({r["product_key"] for r in rows if r["status"] == "saved"})}
        with_reviews = {r["product_key"] for r in reviews}
        missing = Counter()
        for p in products:
            for field in ("shop_name", "rating_average", "sold_total_reported", "variants"):
                val = p.get(field)
                if field == "shop_name" and not val:
                    val = (self.get("shop", p["shop_id"]) or {}).get("shop_name")
                if val is None or val == []:
                    missing[field] += 1
            if p["product_key"] not in with_reviews:
                missing["reviews_not_observed"] += 1
        sampling_reviews = {}
        for review in reviews:
            sampling_reviews.setdefault(review["product_key"], []).append(review)
        review_sampling = {}
        progress_by_key = {
            row["product_key"]: row for row in self.rows("review_progress")
        }
        for key in sorted(set(sampling_reviews) | set(progress_by_key)):
            rows = sampling_reviews.get(key, [])
            progress = progress_by_key.get(key, {})
            star_counts = Counter(
                str(row["rating"]) for row in rows if row.get("rating") is not None
            )
            review_sampling[key] = {
                "observed_count": len(rows),
                "cap": None if scope.get("all_review_pages") else scope.get("max_reviews_per_product", 100),
                "observed_by_star": dict(sorted(star_counts.items())),
                "stop_reason": progress.get("stop_reason", "not_stopped"),
                "representativeness": "unknown_observed_subset_only",
            }
        return {
            "products_observed": len(products), "reviews_observed": len(reviews),
            "variants_observed": sum(len(p.get("variants") or []) for p in products),
            "image_urls_observed": len({row["image_url"] for row in self.media_links("image", products, reviews)}),
            "image_download_status": dict(Counter(row["status"] for row in self.rows("image"))),
            "video_urls_observed": len({row["video_url"] for row in self.media_links("video", products, reviews)}),
            "video_download_status": dict(Counter(row["status"] for row in self.rows("video"))),
            "product_fields_observed": field_counts, "product_checks": checks, "media_by_role": media,
            "product_jobs": self.db.execute("SELECT COUNT(*) FROM queue WHERE kind='product'").fetchone()[0],
            "configured_seed_checks": seed_checks,
            "seed_products_meeting_required_fields": sum(bool(v) and all(v.values()) for v in seed_checks.values()),
            "products_meeting_detail_checks": sum(all(fields.values()) for fields in checks.values()),
            "reviews_with_text": sum(bool((r.get("content") or "").strip()) for r in reviews),
            "reviews_empty_at_source": sum(r.get("content_status") == "empty_at_source" for r in reviews),
            "reviews_text_unknown": sum(not r.get("content") and r.get("content_status") != "empty_at_source" for r in reviews),
            "review_pagination": self.rows("review_progress"),
            "review_sampling": review_sampling,
            "queue_status": dict(self.db.execute("SELECT status,COUNT(*) FROM queue GROUP BY status").fetchall()),
            "missing_fields_count": dict(missing),
            "classification_methods": dict(Counter(p.get("classification_method", "unknown") for p in products)),
            "coverage": "unknown; discovered subset only; never whole-market coverage",
            "price_note": "browser-response units are configured assumptions; verify raw price against UI",
            "review_note": "only observed review pages; counts do not prove all reviews were collected",
            "merge_note": "latest nonempty fields merged; field_observations records each field freshness",
        }

    def export(self):
        products, reviews = self.rows("product"), self.rows("review")
        for r in reviews:
            if not r.get("created_at_utc"):
                r["created_at_utc"] = timestamp_utc(r.get("created_at_raw"))
            if not r.get("content_status"):
                r["content_status"] = "with_text" if r.get("content") else "unknown"
        shops = {s["shop_id"]: s for s in self.rows("shop")}
        variants = []
        categories = {c["category_id"]: c for c in self.rows("category_link")}
        for p in products:
            s = shops.get(p["shop_id"], {})
            if not p.get("shop_name") and s.get("shop_name"):
                p["shop_name"] = s["shop_name"]
            shops.setdefault(p["shop_id"], {"shop_id": p["shop_id"], "shop_name": p.get("shop_name"),
                                            "shop_username": p.get("shop_username")})
            for v in p.get("variants") or []:
                variants.append({"product_key": p["product_key"], **v,
                                 "observed_at": p.get("field_observations", {}).get("variants", {}).get("at")})
            for c in p.get("category_path") or []:
                key = c.get("category_id") or c.get("name")
                previous = categories.get(key) or {}
                categories[key] = {**previous, **{k: v for k, v in c.items() if v is not None}}
        fields = {
            "products": ["product_key", "item_id", "shop_id", "url", "name", "description", "shop_name",
                         "shop_username", "currency", "currency_assumed", "price", "price_raw", "price_min",
                         "price_max", "price_divisor", "price_unit_status", "rating_average", "rating_count",
                         "sold_period_reported", "sold_total_reported", "sold_semantics", "category_path",
                         "suggested_category", "classification_method", "classification_evidence", "attributes",
                         "images", "cover_image_url", "gallery_image_urls", "description_image_urls", "image_urls", "video_urls",
                         "variant_options", "sold_display", "price_display_text", "rating_count_display", "description_media_status",
                         "variant_capture_status", "record_level", "source_kind", "source_url",
                         "observed_at", "field_observations"],
            "variants": ["product_key", "variant_id", "variant_name", "options", "price", "price_raw",
                         "price_divisor", "currency", "stock", "observed_at"],
            "reviews": ["review_key", "review_id", "product_key", "shop_id", "item_id", "rating", "content",
                        "created_at_raw", "variant_name", "phone_model", "case_variant", "observed_at",
                        "source_url", "created_at_utc", "created_at_display",
                        "content_status", "like_count", "dislike_count", "shop_reply_content", "shop_reply_created_at_raw",
                        "shop_reply_created_at_utc", "image_urls", "video_urls"],
            "images": ["owner_kind", "role", "product_key", "review_key", "image_url", "status", "local_path",
                       "bytes", "http_status", "error", "fallback_kind"],
            "videos": ["owner_kind", "role", "product_key", "review_key", "video_url", "status", "local_path",
                       "bytes", "http_status", "error", "fallback_kind", "source_status", "analysis_note"],
            "shops": ["shop_id", "shop_name", "shop_username", "observed_at"],
            "categories": ["category_id", "name"],
        }
        datasets = {"products": products, "variants": variants, "reviews": reviews,
                    "shops": list(shops.values()), "categories": list(categories.values())}
        for kind in ("image", "video"):
            datasets[f"{kind}s"] = self.media_manifest(kind, products, reviews)
        for name, data in datasets.items():
            with export_file(self.folder / (name + ".csv"), "utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=fields[name], extrasaction="ignore")
                writer.writeheader()
                writer.writerows({k: csv_value(v) for k, v in row.items()} for row in data)
        with export_file(self.folder / "products.jsonl", "utf-8") as f:
            for p in products:
                f.write(encode(p) + "\n")
        report = self.report()
        with export_file(self.folder / "coverage_report.json", "utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        return report

    def close(self):
        self.db.close()
