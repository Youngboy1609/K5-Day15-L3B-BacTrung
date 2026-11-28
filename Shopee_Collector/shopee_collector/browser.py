from __future__ import annotations

import asyncio
import hashlib
import json
import random
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit, quote

from .parsing import canonical, product_ids, extract_payload, jsonld_products, page_bundle
from .storage import detail_fields
from .images import download_images
from .videos import download_videos


PRODUCT_PAGE = Path(__file__).with_name("product_page.js").read_text(encoding="utf-8")


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def blocker(url, text):
    path = urlsplit(url).path.lower()
    if "/verify" in path or "/captcha" in path:
        return "captcha_or_verification"
    if "/buyer/login" in path or "/account/login" in path:
        return "login_required"
    text = text.lower()
    if "page unavailable" in text and "something went wrong" in text:
        return "page_unavailable"
    if any(x in text for x in ("verify you are human", "unusual traffic", "automated requests",
                                "xác nhận để tiếp tục", "truy cập bất thường")):
        return "verification_required"
    return None


class Collector:
    def __init__(self, store, config, rules):
        self.store, self.cfg, self.rules = store, config, rules
        self.tasks, self.response_errors = set(), []
        self.network_block = None
        self.page = None
        self.context = None
        self.visiting_product = None
        self.accept_responses = False
        self.capture_count = 0

    def response(self, response):
        if not self.accept_responses or self.network_block:
            return
        # Capture page identity at event time; never use a later page as fallback.
        page_url = self.page.url
        task = asyncio.create_task(self.read_response(response, page_url, self.visiting_product))
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)

    async def drain(self):
        while self.tasks:
            await asyncio.gather(*list(self.tasks), return_exceptions=True)

    async def read_response(self, response, page_url, expected_product=None):
        if expected_product and product_ids(page_url) != expected_product:
            return
        u = urlsplit(response.url)
        path = u.path.lower()
        if u.hostname not in {"shopee.vn", "www.shopee.vn"} or "/api/" not in path:
            return
        if not any(t in path for t in ("item", "pdp", "search", "rating", "shop", "category", "recommend")):
            return
        if any(t in path for t in ("account", "login", "order", "payment", "address", "wallet", "chat")):
            return
        if response.status in (401, 403, 429):
            self.network_block = f"http_{response.status}"
            return
        if response.status != 200 or "json" not in response.headers.get("content-type", ""):
            return
        try:
            size = response.headers.get("content-length")
            if size and int(size) > 5_000_000:
                return
            raw = await response.body()
            if len(raw) > 5_000_000:
                return
            payload = json.loads(raw)
            # Missing review identity can be filled only from a matching request.
            fallback = None
            ids = product_ids(page_url)
            q = parse_qs(u.query)
            if ids and "rating" in path and q.get("itemid") == [ids[1]] and q.get("shopid") == [ids[0]]:
                fallback = ids
            bundle = extract_payload(payload, divisor=self.cfg["network_price_divisor"], rules=self.rules,
                                     source_url=f"https://shopee.vn{u.path}", observed_at=now(),
                                     review_product=fallback)
            if ids:
                key = ":".join(ids)
                bundle["products"] = [p for p in bundle["products"] if p["product_key"] == key]
                bundle["reviews"] = [r for r in bundle["reviews"] if r["product_key"] == key]
                bundle["shops"] = [s for s in bundle["shops"] if s["shop_id"] == ids[0]]
            # Raw responses, request headers, cookies and author profiles are not stored.
            captured = sum(len(bundle.get(kind, [])) for kind in ("products", "reviews", "shops"))
            if captured:
                self.store.ingest(bundle)
                self.capture_count += captured
        except Exception as exc:
            # Avoid exception strings which might include URLs with session parameters.
            self.response_errors.append(type(exc).__name__)
            self.store.event(now(), "response_parse_error", type(exc).__name__)

    async def check(self):
        reason = self.network_block or blocker(self.page.url, "")
        if reason:
            return reason
        text = await self.page.locator("body").inner_text(timeout=10000)
        return self.network_block or blocker(self.page.url, text[:20000])

    async def settle(self, check_body=True):
        await self.page.wait_for_timeout(self.cfg["settle_ms"])
        await self.drain()
        if self.network_block:
            return self.network_block
        url_block = blocker(self.page.url, "")
        if url_block or not check_body:
            return url_block
        return await self.check()

    async def collect_dom(self, *, checkpoint=False):
        url = self.page.url
        if not product_ids(url):
            return
        scripts = await self.page.locator('script[type="application/ld+json"]').all_text_contents()
        for script in scripts:
            try:
                products = jsonld_products(json.loads(script), url, now(), self.rules)
                self.store.ingest({"products": products})
            except (ValueError, TypeError, AttributeError):
                self.store.event(now(), "jsonld_parse_error", "Unsupported JSON-LD shape")
        selector = self.cfg["selectors"].get("review_container", ".product-ratings")
        view = await self.page.evaluate(PRODUCT_PAGE, selector)
        bundle = page_bundle(view, url, now(), self.rules)
        if bundle:
            rows = bundle["reviews"]
            number = view.get("review_page")
            review_page = None
            if (checkpoint and not self.store.sample_reviews and rows and number and len(rows) == len(view["reviews"])
                    and view.get("review_filter") in (None, "", "tat ca", "all")):
                review_page = (rows[0]["product_key"], number, now())
            return self.store.ingest(bundle, review_page=review_page)

    async def collect_gallery(self):
        # The desktop carousel only mounts the thumbnails in its current window.
        gallery = self.page.locator("section.card").filter(has=self.page.locator("h1"))
        arrow = gallery.locator('button:has(img[alt="icon arrow right bold"])')
        seen = set()
        while await arrow.count() == 1 and await arrow.is_visible() and await arrow.is_enabled():
            if await arrow.get_attribute("aria-disabled") == "true":
                break
            urls = tuple(await gallery.locator("section:first-child picture img").evaluate_all(
                "els => els.map(e => e.getAttribute('src'))"))
            if not urls or urls in seen:
                break
            seen.add(urls)
            await arrow.click(timeout=5000)
            block = await self.settle()
            if block:
                return block
            await self.collect_dom()
        return None

    async def discover(self, include_categories=False):
        links = await self.page.locator("a[href]").evaluate_all(
            "els => els.map(e => ({href:e.href, text:(e.innerText || '').trim()}))")
        jobs = []
        remaining = max(0, self.cfg["max_queue_size"] - self.store.queue_size())
        for link in links:
            try:
                url = canonical(link["href"])
            except ValueError:
                continue
            if not url:
                continue
            if product_ids(url):
                kind = "product"
            elif include_categories and re.search(r"-cat\.\d+", urlsplit(url).path):
                kind = "listing"
                cid = re.search(r"-cat\.(\d+)", urlsplit(url).path)[1]
                self.store.put("category_link", cid, {"category_id": cid, "name": link["text"], "url": url})
            else:
                continue
            jobs.append((url, kind))
            if len(jobs) >= remaining:
                break
        if jobs:
            self.store.enqueue_many(jobs, now())

    async def scroll_and_collect(self, listing=False):
        idle_scrolls = 0
        last_capture = self.capture_count
        for _ in range(self.cfg["scroll_steps"]):
            await self.page.mouse.wheel(0, 850)
            block = await self.settle(check_body=False)
            if block:
                return block
            if listing:
                await self.discover(include_categories=False)
            if self.capture_count == last_capture:
                idle_scrolls += 1
            else:
                idle_scrolls = 0
                last_capture = self.capture_count
            # Listing pages can stop as soon as scrolling stops discovering data.
            # Product pages keep scrolling so lazy detail sections can initialize.
            if listing and idle_scrolls >= self.cfg.get("max_idle_scrolls", 2):
                break
        await self.collect_dom()
        return await self.check()

    async def collect_reviews(self):
        product_url = self.page.url
        ids = product_ids(product_url)
        if not ids:
            return await self.check() or "review_paused"
        key = ":".join(ids)
        selector = self.cfg["selectors"].get("review_container", ".product-ratings")
        widget = self.page.locator(selector).first
        if self.store.sample_reviews:
            return await self.collect_star_sample(key, widget, selector)
        progress = self.store.get("review_progress", key) or {}
        review_cap = self.cfg.get("max_reviews_per_product", 100)
        if not self.cfg.get("all_review_pages"):
            if len(self.store.product_reviews(key)) >= review_cap:
                self.store.review_stop(key, "sample_cap_reached", now())
                return None
        # Older runs stored an encounter count, not an actual page number.
        target = progress.get("next_page", 1)
        last_ids = tuple(progress.get("last_review_ids", []))
        previous_ids = ()
        next_clicked_on = None
        limit = None if self.cfg.get("all_review_pages") else self.cfg["review_pages_per_product"]
        if limit and target > limit:
            return None
        if await widget.count():
            await widget.scroll_into_view_if_needed(timeout=5000)
        block = await self.settle()
        seen = set()
        unnumbered_pages = 0
        while not block:
            view = await self.page.evaluate(PRODUCT_PAGE, selector)
            rows = page_bundle(view, product_url, now(), self.rules).get("reviews", [])
            if not rows:
                if block := await self.check():
                    break
                if not seen and target == 1 and (self.store.get("product", key) or {}).get("rating_count") == 0:
                    self.store.review_stop(key, "zero_ratings_observed", now())
                    return None
                reason = "review_rows_unavailable"
                break
            number = view.get("review_page")
            fingerprint = tuple(r["review_id"] for r in rows)
            if view.get("review_filter") not in (None, "", "tat ca", "all") or len(rows) != len(view["reviews"]):
                self.store.ingest({"reviews": rows})
                reason = "review_filter_or_ids_changed"
                break
            if (number == target - 1 and fingerprint == last_ids and view.get("last_number_displayed")
                    and (next_clicked_on == number or progress.get("stop_reason") in (
                        "end_of_pagination_ui", "next_unavailable"))):
                self.store.review_stop(key, "end_of_pagination_ui", now())
                return None
            if (number, fingerprint) in seen or fingerprint == previous_ids or (number == target and fingerprint == last_ids):
                reason = "review_page_not_changed"
                break
            seen.add((number, fingerprint))
            previous_ids = fingerprint
            if not self.cfg.get("all_review_pages"):
                existing_ids = {
                    str(row["review_id"]) for row in self.store.product_reviews(key)
                }
                remaining = max(0, review_cap - len(existing_ids))
                selected, new_ids = [], set()
                for row in rows:
                    review_id = str(row["review_id"])
                    if review_id in existing_ids:
                        selected.append(row)
                    elif review_id not in new_ids and len(new_ids) < remaining:
                        selected.append(row)
                        new_ids.add(review_id)
                rows = selected
                if not rows:
                    self.store.review_stop(key, "sample_cap_reached", now())
                    return None
            if number and number != target:
                self.store.ingest({"reviews": rows})
                # Reach the first unfinished page using only the widget's displayed controls.
                buttons = view.get("page_buttons", [])
                if number < target:
                    jump = max((n for n in buttons if number < n <= target), default=None)
                else:
                    jump = min((n for n in buttons if target <= n < number), default=None)
                if jump is not None:
                    button = widget.locator(".shopee-page-controller button").filter(has_text=re.compile(rf"^{jump}$"))
                    if await button.count() != 1 or not await button.is_visible():
                        reason = "resume_page_unavailable"
                        break
                    await button.click(timeout=5000)
                    block = await self.settle()
                    continue
                if number != target - 1 or fingerprint != last_ids:
                    reason = "resume_page_unavailable"
                    break
            else:
                if number:
                    self.store.ingest({"reviews": rows}, review_page=(key, number, now()))
                    target, last_ids = number + 1, fingerprint
                else:
                    # Without an active page number, save by review ID and leave the cursor intact.
                    self.store.ingest({"reviews": rows})
                    unnumbered_pages += 1
                saved_rows = [self.store.get("review", row["review_key"]) for row in rows]
                if block := await self.save_media(products=[], reviews=saved_rows):
                    break
                if (
                    not self.cfg.get("all_review_pages")
                    and len(self.store.product_reviews(key)) >= review_cap
                ):
                    self.store.review_stop(key, "sample_cap_reached", now())
                    return None
                if limit and (target > limit or unnumbered_pages >= limit):
                    self.store.review_stop(key, "configured_page_limit", now())
                    return None
            if not await self.next_visible(self.cfg["selectors"]["review_next"]):
                if block := await self.check():
                    break
                if not await widget.count() or product_ids(self.page.url) != ids or (not number and target > 1):
                    reason = "review_widget_disappeared"
                    break
                self.store.review_stop(key, "next_unavailable", now())
                return None
            next_clicked_on = number
            block = await self.settle()
        self.store.review_stop(key, block or reason, now())
        return block or "review_paused"

    async def collect_star_sample(self, key, widget, selector):
        if await widget.count():
            await widget.scroll_into_view_if_needed(timeout=5000)
        block = await self.settle()
        if block:
            self.store.review_stop(key, block, now())
            return block
        await self.collect_dom()
        groups = self.store.sample_progress(key)
        for star in groups:
            if product_ids(self.page.url) != tuple(key.split(":")):
                break
            group = self.store.sample_progress(key)[star]
            if group["saved"] >= group["target"]:
                continue
            label = re.compile(rf"^\s*{star}\s*(?:sao|stars?)\b", re.I)
            button = widget.locator(".product-rating-overview__filter").filter(has_text=label)
            if await button.count() != 1 or not await button.is_visible():
                continue
            if block := await self.check():
                break
            await button.click(timeout=5000)
            seen = set()
            while True:
                block = await self.settle()
                if block:
                    break
                view = await self.page.evaluate(PRODUCT_PAGE, selector)
                if not view or product_ids(view.get("url", "")) != tuple(key.split(":")):
                    break
                if not label.match(view.get("review_filter", "")):
                    break
                bundle = page_bundle(view, self.page.url, now(), self.rules)
                self.store.ingest(bundle)
                current = self.store.sample_progress(key)[star]
                if current["saved"] >= current["target"]:
                    break
                page = (view.get("review_page"), tuple(row.get("id") for row in view.get("reviews", [])))
                if page in seen or (not page[0] and not page[1]):
                    break
                seen.add(page)
                if not await self.next_visible(self.cfg["selectors"]["review_next"]):
                    break
            if block:
                break
        groups = self.store.sample_progress(key)
        complete = len(groups) == 5 and all(g["saved"] == g["target"] for g in groups.values())
        reason = "star_sample_complete" if complete else "star_sample_incomplete"
        self.store.review_stop(key, block or reason, now())
        return block

    def detail_is_needed(self, url):
        ids = product_ids(url)
        if not ids or not self.cfg.get("skip_detail_when_complete", True):
            return True
        if self.store.sample_reviews and self.cfg.get("collect_reviews", True):
            groups = self.store.sample_progress(":".join(ids))
            if len(groups) < 5 or any(g["saved"] < g["target"] for g in groups.values()):
                return True
        product = self.store.get("product", ":".join(ids))
        if not product:
            return True
        for field in self.cfg.get("detail_required_fields", ["name", "price"]):
            if product.get(field) in (None, "", [], {}):
                return True
        return False

    async def next_visible(self, selector):
        """UI pagination only. No constructed API endpoints or fabricated page requests."""
        buttons = self.page.locator(selector)
        if await buttons.count() != 1:
            return False
        button = buttons.first
        classes = await button.get_attribute("class") or ""
        if (not await button.is_visible() or not await button.is_enabled()
                or await button.get_attribute("aria-disabled") == "true" or "disabled" in classes):
            return False
        await button.click(timeout=5000)
        return True

    async def visit(self, job):
        url, kind = job["url"], job["kind"]
        if kind == "product" and not self.detail_is_needed(url):
            self.store.status(url, "covered", now(), "listing_data_satisfied_required_fields")
            return False
        self.network_block = None
        self.visiting_product = product_ids(url) if kind == "product" else None
        stage = "open_page"
        self.store.status(url, "running", now())
        try:
            if not self.visiting_product or product_ids(self.page.url) != self.visiting_product:
                response = await self.page.goto(url, wait_until="domcontentloaded", timeout=45000)
                if response and response.status in (401, 403, 429):
                    self.network_block = f"http_{response.status}"
            block = await self.settle()
            if block:
                self.store.status(url, "blocked", now(), block, stage=stage)
                return block
            if kind == "product":
                if product_ids(self.page.url) != self.visiting_product:
                    self.store.status(url, "no_data", now(), "product_page_not_displayed")
                    return None
                stage = "read_product"
                await self.collect_dom()
                stage = "scroll_product"
                block = await self.scroll_and_collect()
                if not block and product_ids(self.page.url) == product_ids(url):
                    stage = "gallery"
                    block = await self.collect_gallery()
                if not block:
                    stage = "product_media"
                    key = ":".join(self.visiting_product)
                    product = self.store.get("product", key)
                    block = await self.save_media(products=[product] if product else [], reviews=self.store.product_reviews(key))
                if not block and self.cfg.get("collect_reviews", True):
                    stage = "reviews"
                    block = await self.collect_reviews()
                if not block:
                    stage = "save_media"
                    block = await self.save_media()
                key = ":".join(product_ids(url))
                p = self.store.get("product", key)
                # This records only a successful detail visit; full review coverage stays unknown.
                status = "partial" if p else "no_data"
                note = "detail_visit; coverage_unknown" if p else "No supported product payload or JSON-LD observed"
                if p and all(detail_fields(p).values()) and product_ids(self.page.url) == product_ids(url):
                    status, note = "detail_complete", "observed_detail_fields_present"
            else:
                stage = "listing"
                for page_index in range(self.cfg["listing_pages_per_seed"]):
                    block = await self.scroll_and_collect(listing=True)
                    if block:
                        break
                    if page_index + 1 >= self.cfg["listing_pages_per_seed"]:
                        break
                    if not await self.next_visible(self.cfg["selectors"]["listing_next"]):
                        break
                    block = await self.settle()
                    if block:
                        break
                status, note = "visited", "discovery_attempt; coverage_unknown"
            if block:
                self.store.status(url, "review_paused" if block == "review_paused" else "blocked", now(), block, stage=stage)
                return block
            self.store.status(url, status, now(), note)
        except Exception as exc:
            reason = self.network_block or blocker(self.page.url, "")
            if stage == "reviews":
                self.store.review_stop(":".join(self.visiting_product), reason or type(exc).__name__, now())
                self.store.status(url, "blocked" if reason else "review_paused", now(), reason or type(exc).__name__, stage=stage)
                return reason or "review_paused"
            if reason:
                self.store.status(url, "blocked", now(), reason, stage=stage)
                return reason
            self.store.status(url, "failed", now(), type(exc).__name__, stage=stage)
            print(f"Trang bị lỗi: {type(exc).__name__}; đã lưu tiến độ.")
        finally:
            await self.drain()
            self.visiting_product = None
        return None

    async def run_queue(self):
        if self.store.blocked_job():
            self.accept_responses = False
            print("Hàng chờ đang dừng ở trang xác minh. Khi xem được Shopee, nhập retry rồi run.")
            return
        visited, products_visited = 0, 0
        while visited < self.cfg["max_pages_per_run"]:
            job = self.store.next_job(prefer_listings=self.cfg.get("prefer_listings", False))
            if not job:
                print("Đã hết URL đang chờ. Điều này không có nghĩa đã lấy toàn bộ Shopee.")
                break
            if job["kind"] == "product" and products_visited >= self.cfg["max_products_per_run"]:
                break
            print(f"[{visited + 1}] {job['kind']}: {job['url']}")
            block = await self.visit(job)
            if block is False:
                continue
            visited += 1
            products_visited += int(job["kind"] == "product")
            if block:
                if block == "review_paused":
                    print("Đã lưu tiến độ. Phần đánh giá chưa hiển thị đủ để đi tiếp. Dùng retry rồi run khi trang sẵn sàng.")
                    break
                print(f"DỪNG: {block}. Không chuyển URL để né chặn. Dùng trình duyệt để xử lý thủ công,")
                print("sau đó lệnh retry sẽ kiểm tra lại trang hiện tại trước khi cho chạy tiếp.")
                self.accept_responses = False
                break
            await self.page.wait_for_timeout(int(self.cfg["delay_ms"] * random.uniform(0.8, 1.5)))
        self.store.export()

    async def save_media(self, *, products=None, reviews=None):
        for kind, download in (("image", download_images), ("video", download_videos)):
            urls = None
            if products is not None and reviews is not None:
                urls = [r[f"{kind}_url"] for r in self.store.media_links(kind, products, reviews)]
            reason = await download(self.store, lambda: self.network_block or blocker(self.page.url, ""), urls=urls)
            if kind == "image" and reviews is not None:
                await self.capture_review_screenshots(reviews)
            if kind == "video" and reviews is not None:
                await self.capture_review_video_frames(reviews)
            if reason:
                self.network_block = reason
                self.accept_responses = False
                print(f"Đã dừng tải media: {reason}")
                return reason
        return None

    async def capture_review_screenshots(self, reviews):
        if self.page is None:
            return
        for review in reviews:
            image_urls = review.get("image_urls", [])
            if not image_urls:
                continue
            target = None
            for index, candidate_url in enumerate(image_urls):
                candidate = self.store.get("image", candidate_url) or {}
                if candidate.get("status") == "saved" and self.store.file_saved(candidate):
                    continue
                if candidate.get("http_status") in {401, 403, 429} or candidate.get("status") in {
                    "http_401", "http_403", "http_429",
                }:
                    continue
                if candidate.get("status") in {"", "pending", "saved", None}:
                    continue
                target = (index, candidate_url, candidate)
                break
            if target is None:
                continue
            media_index, url, asset = target
            review_id = str(review.get("review_id") or "")
            if not review_id.isdigit():
                continue
            # Clip to a single image wrapper inside this review, never the page or row.
            wrappers = self.page.locator(
                f'[data-cmtid="{review_id}"] .rating-media-list__image-wrapper'
            )
            locator = wrappers.first if media_index == 0 else wrappers.nth(media_index)
            try:
                if not await locator.count() or not await locator.is_visible():
                    continue
                loaded = await locator.evaluate(
                    "el => Array.from(el.querySelectorAll('img')).some("
                    "img => img.complete && img.naturalWidth > 0 && img.naturalHeight > 0)"
                )
                if not loaded:
                    continue
                relative = Path("review_screenshots") / (
                    hashlib.sha256(review["review_key"].encode("utf-8")).hexdigest() + ".png"
                )
                path = self.store.folder / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                await locator.screenshot(path=str(path))
                if not path.is_file() or path.stat().st_size <= 0:
                    continue
                screenshot = {
                    **asset,
                    "status": "saved",
                    "local_path": relative.as_posix(),
                    "bytes": path.stat().st_size,
                    "fallback_kind": "rendered_review_image_screenshot",
                }
                with self.store.db:
                    self.store.put("image", url, screenshot)
                    saved_review = self.store.get("review", review["review_key"]) or review.copy()
                    saved_review.update(
                        screenshot_media_path=relative.as_posix(),
                        screenshot_media_status="saved",
                        screenshot_media_source="rendered_review_image",
                    )
                    self.store.put("review", review["review_key"], saved_review)
            except (OSError, ValueError, RuntimeError):
                continue

    async def capture_review_video_frames(self, reviews):
        if self.page is None:
            return
        for review in reviews:
            for url in review.get("video_urls", []):
                asset = self.store.get("video", url) or {}
                if asset.get("status") == "saved" and self.store.file_saved(asset):
                    continue
                if asset.get("http_status") in {401, 403, 429} or asset.get("status") in {
                    "http_401", "http_403", "http_429",
                }:
                    continue
                if asset.get("status") in {"", "pending", "saved", None}:
                    continue
                review_id = str(review.get("review_id") or "")
                if not review_id.isdigit():
                    continue
                locator = self.page.locator(f'[data-cmtid="{review_id}"] video').first
                try:
                    has_frame = (
                        await locator.count()
                        and await locator.is_visible()
                        and await locator.evaluate(
                            "el => el.readyState >= 2 && el.videoWidth > 0 && el.videoHeight > 0"
                        )
                    )
                    if not has_frame:
                        with self.store.db:
                            self.store.put("video", url, {
                                **asset,
                                "status": "not_assessed",
                                "source_status": asset.get("status"),
                                "fallback_kind": "no_visible_video_frame",
                            })
                        continue
                    relative = Path("review_video_frames") / (
                        hashlib.sha256(review["review_key"].encode("utf-8")).hexdigest() + ".png"
                    )
                    path = self.store.folder / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    await locator.screenshot(path=str(path))
                    if not path.is_file() or path.stat().st_size <= 0:
                        continue
                    with self.store.db:
                        self.store.put("video", url, {
                            **asset,
                            "status": "frame_only",
                            "local_path": relative.as_posix(),
                            "bytes": path.stat().st_size,
                            "fallback_kind": "video_frame_screenshot",
                            "analysis_note": "One visible frame only; no inference about motion or audio.",
                        })
                except (OSError, ValueError, RuntimeError):
                    continue

    async def console(self):
        print("\nLệnh: run | capture | retry | stats | export | quit")
        print("Bạn có thể tự điều hướng trang, đăng nhập hoặc xử lý CAPTCHA trong cửa sổ trình duyệt.")
        while True:
            command = (await asyncio.to_thread(input, "shopee> ")).strip().lower()
            if command in {"quit", "q", "exit"}:
                break
            if command == "run":
                await self.drain()
                if not self.accept_responses or self.network_block:
                    self.accept_responses = False
                    print("Đang tạm dừng; xử lý trang hiện tại rồi dùng retry.")
                else:
                    await self.run_queue()
            elif command in {"capture", "retry"}:
                await self.drain()
                if command == "capture" and not self.accept_responses:
                    print("Đang tạm dừng. Kiểm tra trang trong Chrome rồi dùng retry.")
                    continue
                if command == "retry":
                    self.accept_responses = False
                    self.network_block = None
                block = await self.check()
                if block:
                    self.accept_responses = False
                    print(f"Vẫn bị chặn: {block}.")
                    continue
                if not canonical(self.page.url):
                    print("Hãy mở trang sản phẩm hoặc danh mục Shopee trong tab đã kết nối.")
                    continue
                self.accept_responses = True
                if command == "retry":
                    self.store.retry(self.cfg.get("max_attempts", 2), confirmed_access=True)
                    print("Đã mở lại hàng chờ. Dùng capture để lưu trang hiện tại hoặc run để chạy hàng chờ.")
                else:
                    if product_ids(self.page.url):
                        count = await self.collect_dom(checkpoint=True)
                        if count is None:
                            print("Chưa đọc được nội dung sản phẩm. Chờ trang hiển thị rồi nhập capture.")
                        else:
                            print(f"Đã ghi nhận sản phẩm và {count} đánh giá có mã trên trang hiện tại.")
                    else:
                        await self.discover(include_categories=True)
                        print("Đã ghi nhận các liên kết sản phẩm và danh mục đang hiển thị.")
                    await self.drain()
                    block = await self.check() or await self.save_media()
                    self.store.export()
                    if block:
                        self.accept_responses = False
                        print(f"Đã lưu tiến độ và tạm dừng: {block}.")
            elif command == "stats":
                print(json.dumps(self.store.report(), ensure_ascii=False, indent=2))
            elif command == "export":
                await self.drain()
                self.store.export()
                print("Đã xuất dữ liệu.")
            else:
                print("Dùng run, capture, retry, stats, export hoặc quit.")

    async def start(self, auto=False, remember=False, cdp=None, refresh=False):
        from playwright.async_api import Error as PlaywrightError, async_playwright

        if cdp and remember:
            raise ValueError("--cdp and --remember-session cannot be used together")

        seeds = [canonical(seed) for seed in self.cfg.get("seeds", [])]
        if not all(seeds):
            raise ValueError("Seed must be an HTTPS Shopee VN URL")

        async with async_playwright() as pw:
            browser = None
            is_cdp = bool(cdp)
            if is_cdp:
                try:
                    browser = await pw.chromium.connect_over_cdp(cdp)
                except PlaywrightError as exc:
                    if "ECONNREFUSED" not in str(exc):
                        raise
                    raise ConnectionRefusedError(
                        "Chrome từ chối kết nối CDP (ECONNREFUSED). "
                        "Hãy mở Chrome với --remote-debugging-port trùng cổng trong --cdp "
                        "và giữ cửa sổ đó mở khi chạy crawler."
                    ) from exc
                if not browser.contexts:
                    raise RuntimeError("Chrome CDP không có browser context")
                self.context = browser.contexts[0]
                shopee_pages = [p for p in self.context.pages if urlsplit(p.url).hostname in ("shopee.vn", "www.shopee.vn")]
                self.page = (shopee_pages[-1] if shopee_pages else
                             (self.context.pages[-1] if self.context.pages else await self.context.new_page()))
                print(f"Đã kết nối Chrome CDP. Tab hiện tại: {urlsplit(self.page.url).hostname or 'trang trống'}")
            else:
                opts = {"headless": False}
                if self.cfg.get("browser_channel"):
                    opts["channel"] = self.cfg["browser_channel"]
                if remember:
                    self.context = await pw.chromium.launch_persistent_context("browser-profile", **opts)
                    print("Đang dùng browser-profile được lưu theo yêu cầu --remember-session.")
                else:
                    browser = await pw.chromium.launch(**opts)
                    self.context = await browser.new_context()
                    print("Đang dùng phiên trình duyệt mới; không tái sử dụng chrome_profile cũ.")
                self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()

            # Only this tab supplies the identity for the responses we process.
            blocked_types = set(self.cfg.get("block_resource_types", []))
            if blocked_types:
                async def route_resource(route):
                    if route.request.resource_type in blocked_types:
                        await route.abort()
                    else:
                        await route.continue_()
                await self.context.route("**/*", route_resource)
            self.page.on("response", self.response)
            self.store.recover_running_jobs()
            if refresh or self.store.sample_reviews != bool(self.cfg.get("sample_reviews")):
                self.store.refresh_products(seeds)
            for url in seeds:
                self.store.enqueue(url, "product" if product_ids(url) else "listing", now())
            for keyword in self.cfg.get("keywords", []):
                self.store.enqueue("https://shopee.vn/search?keyword=" + quote(keyword), "listing", now())
            self.store.record_scope(self.cfg)
            self.accept_responses = not self.store.blocked_job()

            try:
                if auto:
                    await self.run_queue()
                else:
                    # Không tự gọi self.visit(job) ngay lúc khởi động để tránh kích hoạt CAPTCHA
                    await self.console()
            finally:
                self.accept_responses = False
                await self.drain()
                self.store.export()
                if not is_cdp:
                    await self.context.close()
                    if browser:
                        await browser.close()
