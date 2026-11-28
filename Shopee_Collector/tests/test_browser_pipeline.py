"""No calls to Shopee. Exercise the actual passive-response handler with fakes."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from shopee_collector.browser import Collector
from shopee_collector.storage import Store

ROOT = Path(__file__).resolve().parent.parent


class Response:
    def __init__(self, url, payload=None, status=200):
        self.url, self.status = url, status
        self.headers = {"content-type": "application/json"}
        self.payload = payload
        self.body_called = False

    async def body(self):
        self.body_called = True
        return json.dumps(self.payload).encode()


class PipelineTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(self.tmp.name)
        config = json.loads((ROOT / "config/settings.json").read_text(encoding="utf-8"))
        self.c = Collector(self.store, config, [])

    async def asyncTearDown(self):
        self.store.close()
        self.tmp.cleanup()

    async def test_refused_cdp_does_not_refresh_or_recover_jobs(self):
        from playwright.async_api import Error as PlaywrightError

        partial, active = ("https://shopee.vn/product/1/2", "https://shopee.vn/product/1/3")
        self.c.cfg["seeds"] = [partial, active, "https://shopee.vn/product/1/4"]
        self.store.enqueue(partial, "product", "test")
        self.store.status(partial, "partial", "test")
        self.store.enqueue(active, "product", "test")
        self.store.status(active, "running", "test")
        pw = MagicMock()
        pw.chromium.connect_over_cdp = AsyncMock(side_effect=PlaywrightError("connect ECONNREFUSED"))
        with patch("playwright.async_api.async_playwright") as driver:
            driver.return_value.__aenter__.return_value = pw
            with self.assertRaisesRegex(ConnectionRefusedError, "remote-debugging-port"):
                await self.c.start(cdp="http://127.0.0.1:9222", refresh=True)
        rows = dict(self.store.db.execute("SELECT url, status FROM queue"))
        self.assertEqual(rows, {partial: "partial", active: "running"})

    async def test_matching_rating_request_can_supply_identity(self):
        r = Response("https://shopee.vn/api/test/rating?shopid=1&itemid=2",
                     {"ratings": [{"cmtid": 11, "rating_star": 5, "comment": "test"}]})
        await self.c.read_response(r, "https://shopee.vn/product/1/2")
        self.assertEqual(self.store.rows("review")[0]["product_key"], "1:2")

    async def test_other_rating_request_never_borrows_current_page_identity(self):
        r = Response("https://shopee.vn/api/test/rating?shopid=3&itemid=4",
                     {"ratings": [{"cmtid": 11, "rating_star": 5, "comment": "test"}]})
        await self.c.read_response(r, "https://shopee.vn/product/1/2")
        self.assertEqual(self.store.rows("review"), [])

    async def test_account_response_is_not_read(self):
        r = Response("https://shopee.vn/api/shop/account", {"secret": "do not capture"})
        await self.c.read_response(r, "https://shopee.vn/")
        self.assertFalse(r.body_called)

    async def test_external_response_is_not_read(self):
        r = Response("https://example.com/api/item", {"secret": "do not capture"})
        await self.c.read_response(r, "https://shopee.vn/")
        self.assertFalse(r.body_called)

    async def test_429_pauses_without_requesting_another_endpoint(self):
        r = Response("https://shopee.vn/api/test/item", {}, status=429)
        await self.c.read_response(r, "https://shopee.vn/")
        self.assertEqual(self.c.network_block, "http_429")
        self.assertFalse(r.body_called)

    async def test_stop_queue_on_first_block(self):
        self.store.enqueue("https://shopee.vn/", "listing", "test")
        self.store.enqueue("https://shopee.vn/search?keyword=test", "listing", "test")
        called = []

        async def blocked_visit(job):
            called.append(job["url"])
            self.store.status(job["url"], "blocked", "test", "captcha")
            return "captcha_or_verification"

        self.c.visit = blocked_visit
        self.c.accept_responses = True
        await self.c.run_queue()
        self.assertEqual(called, ["https://shopee.vn/"])
        self.assertFalse(self.c.accept_responses)
        self.assertEqual(self.store.report()["queue_status"], {"blocked": 1, "pending": 1})

    async def test_verified_product_already_open_is_not_reloaded(self):
        url = "https://shopee.vn/product/1/2"
        self.store.enqueue(url, "product", "test")
        self.c.page = SimpleNamespace(url=url, goto=AsyncMock())
        for name in ("settle", "scroll_and_collect", "collect_dom", "collect_gallery", "collect_reviews", "save_media"):
            setattr(self.c, name, AsyncMock(return_value=None))
        await self.c.visit({"url": url, "kind": "product"})
        self.c.page.goto.assert_not_awaited()
        self.c.collect_dom.assert_awaited_once()

    async def test_saved_block_stops_next_run(self):
        url = "https://shopee.vn/product/1/2"
        self.store.enqueue(url, "product", "test")
        self.store.status(url, "blocked", "test", "captcha")
        self.store.enqueue("https://shopee.vn/product/3/4", "product", "test")
        self.c.visit = AsyncMock()
        await self.c.run_queue()
        self.c.visit.assert_not_awaited()

    async def test_resume_from_last_committed_review_page_after_restart(self):
        url = "https://shopee.vn/product/1/2"
        key = "1:2"
        def view(number):
            return {"url": url, "name": "Sample", "reviews": [{"id": str(number), "comment": f"review {number}"}],
                    "review_page": number, "page_buttons": [1, 2, 3, 4]}

        widget = MagicMock()
        widget.count = AsyncMock(return_value=1)
        widget.scroll_into_view_if_needed = AsyncMock()
        def setup(collector, pages):
            collector.page = MagicMock(url=url)
            collector.page.locator.return_value.first = widget
            collector.page.evaluate = AsyncMock(side_effect=[view(p) for p in pages])
            collector.check = AsyncMock(return_value=None)
            collector.save_media = AsyncMock(return_value=None)
            collector.cfg["all_review_pages"] = True

        setup(self.c, [1, 2])
        self.c.next_visible = AsyncMock(return_value=True)
        self.c.settle = AsyncMock(side_effect=[None, None, "captcha_or_verification"])
        self.assertEqual(await self.c.collect_reviews(), "captcha_or_verification")
        self.assertEqual(self.store.get("review_progress", key)["next_page"], 3)
        self.assertEqual(len(self.store.rows("review")), 2)

        self.store.close()
        self.store = Store(self.tmp.name)
        resumed = Collector(self.store, self.c.cfg, [])
        setup(resumed, [1, 3, 4])
        resumed.settle = AsyncMock(return_value=None)
        resumed.next_visible = AsyncMock(side_effect=[True, False])
        button = widget.locator.return_value.filter.return_value
        button.count = AsyncMock(return_value=1)
        button.is_visible = AsyncMock(return_value=True)
        button.click = AsyncMock()
        self.assertIsNone(await resumed.collect_reviews())
        button.click.assert_awaited_once()
        self.assertTrue(widget.locator.return_value.filter.call_args.kwargs["has_text"].fullmatch("3"))
        self.assertEqual(self.store.get("review_progress", key)["next_page"], 5)
        self.assertEqual([r["review_id"] for r in self.store.rows("review")], ["1", "2", "3", "4"])
        self.assertEqual(resumed.save_media.await_count, 2)

    async def test_review_checkpoint_and_records_roll_back_together(self):
        row = {"review_key": "1:2:3", "product_key": "1:2", "review_id": "3"}
        with self.assertRaises(ValueError):
            self.store.ingest({"reviews": [row]}, review_page=("4:5", 1, "test"))
        self.assertEqual(self.store.rows("review"), [])
        self.assertEqual(self.store.rows("review_progress"), [])

    async def test_last_review_page_with_clickable_next(self):
        url = "https://shopee.vn/product/1/2"
        key = "1:2"
        old = {"review_key": "1:2:10", "review_id": "10", "product_key": key}
        self.store.ingest({"reviews": [old]}, review_page=(key, 1, "t1"))
        view = {"url": url, "name": "Sample", "review_page": 2, "page_buttons": [1, 2],
                "last_number_displayed": True, "reviews": [{"id": "20", "comment": "last"}]}
        self.c.cfg["all_review_pages"] = True
        self.c.page = MagicMock(url=url)
        self.c.page.evaluate = AsyncMock(return_value=view)
        widget = self.c.page.locator.return_value.first
        widget.count = AsyncMock(return_value=1)
        widget.scroll_into_view_if_needed = AsyncMock()
        self.c.settle = AsyncMock(return_value=None)
        self.c.next_visible = AsyncMock(return_value=True)
        self.c.save_media = AsyncMock(return_value="http_429")
        self.assertEqual(await self.c.collect_reviews(), "http_429")
        self.assertEqual(self.store.get("review_progress", key)["next_page"], 3)
        self.c.next_visible.assert_not_awaited()
        self.c.save_media = AsyncMock(return_value=None)
        self.assertIsNone(await self.c.collect_reviews())
        self.c.next_visible.assert_awaited_once()
        self.assertEqual(self.store.get("review_progress", key)["stop_reason"], "end_of_pagination_ui")
        self.assertEqual(len(self.store.rows("review")), 2)

    async def test_complete_listing_product_skips_navigation(self):
        self.store.ingest({"products": [{
            "product_key": "1:2", "shop_id": "1", "item_id": "2", "name": "test",
            "price": "100", "rating_average": 5, "observed_at": "test",
            "source_kind": "browser_response",
        }]})
        self.c.cfg["skip_detail_when_complete"] = True
        self.c.cfg["detail_required_fields"] = ["name", "price", "rating_average"]
        self.assertFalse(self.c.detail_is_needed("https://shopee.vn/product/1/2"))
        self.store.enqueue("https://shopee.vn/product/1/2", "product", "test")
        result = await self.c.visit({"url": "https://shopee.vn/product/1/2", "kind": "product"})
        self.assertIs(result, False)
        status = self.store.db.execute("SELECT status FROM queue WHERE url=?",
                                       ("https://shopee.vn/product/1/2",)).fetchone()
        self.assertEqual(status[0], "covered")


if __name__ == "__main__":
    unittest.main()
