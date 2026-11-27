import json
import os
import sys
import threading
import time
import unittest

try:
    from playwright.sync_api import expect, sync_playwright
except ImportError:
    expect = None
    sync_playwright = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODEBASE = os.path.join(ROOT, "codebase")
if CODEBASE not in sys.path:
    sys.path.insert(0, CODEBASE)

import app


@unittest.skipUnless(sync_playwright, "Playwright is optional for the web smoke tests")
class WebDemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = app.make_server(port=0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = "http://127.0.0.1:%d" % cls.server.server_port
        cls.playwright = sync_playwright().start()
        try:
            cls.browser = cls.playwright.chromium.launch(
                headless=True, executable_path=os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH")
            )
        except Exception as error:
            if "Executable doesn't exist" not in str(error):
                cls.playwright.stop()
                cls.server.shutdown()
                cls.server.server_close()
                cls.thread.join(timeout=2)
                raise
            cls.playwright.stop()
            cls.server.shutdown()
            cls.server.server_close()
            cls.thread.join(timeout=2)
            raise unittest.SkipTest("Playwright Chromium is not installed; set PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH or run playwright install")

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def setUp(self):
        self.context = self.browser.new_context(viewport={"width": 1280, "height": 800})
        self.page = self.context.new_page()
        self.page.goto(self.base_url)

    def tearDown(self):
        self.context.close()

    def analyze(self):
        with self.page.expect_response(lambda response: response.url.endswith("/analyze")):
            self.page.get_by_role("button", name="Phân tích review").click()
        response = self.page.wait_for_timeout(50)

    def test_initial_screen_has_no_fabricated_result_and_demo_is_one_click(self):
        expect(self.page.get_by_role("heading", name="Đọc review đúng mẫu ốp")).to_be_visible()
        expect(self.page.locator(".result")).to_be_hidden()
        expect(self.page.locator(".coverage-number")).to_have_text("— / —")
        self.page.get_by_role("button", name="Dùng mẫu demo").click()
        expect(self.page.get_by_label("Link Shopee")).to_have_value(
            "https://shopee.vn/fixture-bactrung-case-clear-001"
        )
        expect(self.page.get_by_label("Dòng máy")).to_be_enabled()
        expect(self.page.get_by_label("Biến thể ốp")).to_be_enabled()

    def test_switching_phone_model_changes_coverage_and_evidence(self):
        self.page.get_by_role("button", name="Dùng mẫu demo").click()
        self.analyze()
        expect(self.page.locator(".coverage-number")).to_have_text("8 / 8")
        expect(self.page.locator(".result")).to_be_focused()
        expect(self.page.locator(".evidence-meta").first).to_contain_text("R010")

        self.page.get_by_label("Dòng máy").select_option(label="iPhone 15")
        expect(self.page.locator(".result")).to_be_hidden()
        expect(self.page.get_by_role("status")).to_contain_text("Đã thay đổi mẫu")
        self.analyze()
        expect(self.page.locator(".coverage-number")).to_have_text("1 / 1")
        expect(self.page.locator(".evidence-meta").first).to_contain_text("R007")
        expect(self.page.locator(".result")).to_contain_text("Chỉ có 1 review đúng mẫu")

    def test_unknown_listing_shows_no_data_without_recommendation(self):
        self.page.get_by_label("Link Shopee").fill("https://shopee.vn/chua-co-trong-fixture")
        self.page.keyboard.press("Tab")
        expect(self.page.locator(".feedback")).to_contain_text("Chưa có dữ liệu cho link này")
        expect(self.page.locator(".result")).to_be_hidden()
        expect(self.page.locator(".recommendation")).to_be_hidden()

    def test_evidence_keeps_mixed_and_negative_labels(self):
        self.page.get_by_label("Link Shopee").fill(
            "https://shopee.vn/fixture-bactrung-case-rugged-002"
        )
        self.page.get_by_label("Dòng máy").select_option(label="Samsung Galaxy S24")
        self.page.get_by_label("Biến thể ốp").select_option(label="Ốp chống sốc viền nhám")
        self.analyze()
        expect(self.page.locator(".coverage-number")).to_have_text("3 / 3")
        labels = self.page.locator(".evidence-label").all_text_contents()
        self.assertEqual(len(labels), 3)
        self.assertIn("Chưa rõ", labels)
        self.assertIn("Đáng lưu ý", labels)

    def test_stale_response_is_ignored_after_input_changes(self):
        def delayed(route):
            time.sleep(0.6)
            route.continue_()

        self.page.route("**/analyze", delayed)
        self.page.get_by_role("button", name="Dùng mẫu demo").click()
        with self.page.expect_response(lambda response: response.url.endswith("/analyze")):
            self.page.get_by_role("button", name="Phân tích review").click()
        self.page.get_by_label("Dòng máy").select_option(label="iPhone 15")
        expect(self.page.get_by_role("status")).to_contain_text("Đã thay đổi mẫu")
        self.page.wait_for_timeout(800)
        expect(self.page.locator(".result")).to_be_hidden()

    def test_model_failure_is_safe_and_retryable(self):
        self.page.route(
            "**/analyze",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(
                    {
                        "status": "error",
                        "code": "ANALYSIS_UNAVAILABLE",
                        "message": "Chưa xác thực được phân tích review; chưa đưa ra khuyến nghị.",
                    }
                ),
            ),
        )
        self.page.get_by_role("button", name="Dùng mẫu demo").click()
        self.analyze()
        expect(self.page.locator(".feedback")).to_contain_text("Chưa xác thực được phân tích")
        expect(self.page.get_by_role("button", name="Thử lại")).to_be_visible()
        expect(self.page.locator(".result")).to_be_hidden()
        self.assertNotIn("Traceback", self.page.locator("body").inner_text())


    def test_partial_url_does_not_show_an_error_until_blur(self):
        url = self.page.get_by_label("Link Shopee")
        url.fill("https://shopee.vn/fi")
        expect(self.page.locator(".feedback")).to_be_hidden()
        self.assertIsNone(url.get_attribute("aria-invalid"))
        self.page.keyboard.press("Tab")
        expect(self.page.locator(".feedback")).to_contain_text("Chưa có dữ liệu cho link này")

    def test_details_disclosure_shows_analysis_metadata(self):
        self.page.get_by_role("button", name="Dùng mẫu demo").click()
        self.analyze()
        self.page.locator(".details summary").click()
        expect(self.page.locator("#details-content")).to_be_visible()
        expect(self.page.locator("#details-content")).to_contain_text("Chế độ")
        expect(self.page.locator("#details-content")).to_contain_text("Mock")

    def test_variant_not_found_is_safe_and_asks_for_a_new_choice(self):
        self.page.route(
            "**/analyze",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(
                    {
                        "output": json.dumps(
                            {
                                "status": "needs_input",
                                "code": "VARIANT_NOT_FOUND",
                                "message": "Chưa thấy đúng biến thể. Hãy chọn lại.",
                                "available_variants": ["Ốp trong suốt viền đen"],
                            }
                        )
                    }
                ),
            ),
        )
        self.page.get_by_role("button", name="Dùng mẫu demo").click()
        self.analyze()
        expect(self.page.locator(".feedback")).to_contain_text("Cần chọn lại mẫu")
        expect(self.page.locator(".result")).to_be_hidden()
    def test_keyboard_focus_and_reduced_motion_are_supported(self):
        self.page.keyboard.press("Tab")
        focused = self.page.evaluate("document.activeElement.id")
        self.assertEqual(focused, "product-url")
        outline = self.page.get_by_label("Link Shopee").evaluate(
            "element => getComputedStyle(element).outlineStyle"
        )
        self.assertNotEqual(outline, "none")
        self.page.emulate_media(reduced_motion="reduce")
        duration = self.page.get_by_role("button", name="Phân tích review").evaluate(
            "element => getComputedStyle(element).transitionDuration"
        )
        self.assertTrue(duration.startswith("0.01s") or duration.startswith("0s"))

    def test_mobile_and_large_text_do_not_scroll_horizontally(self):
        for width in (320, 375, 414, 768):
            with self.subTest(width=width):
                self.page.set_viewport_size({"width": width, "height": 800})
                dimensions = self.page.evaluate(
                    "({scroll: document.documentElement.scrollWidth, viewport: window.innerWidth})"
                )
                self.assertLessEqual(dimensions["scroll"], dimensions["viewport"])
                for button in self.page.get_by_role("button").all():
                    box = button.bounding_box()
                    self.assertGreaterEqual(box["height"], 44)
                    self.assertLessEqual(button.evaluate("el => el.scrollWidth"), button.evaluate("el => el.clientWidth") + 1)
        self.page.set_viewport_size({"width": 375, "height": 800})
        self.page.evaluate("document.documentElement.style.fontSize = '32px'")
        dimensions = self.page.evaluate(
            "({scroll: document.documentElement.scrollWidth, viewport: window.innerWidth})"
        )
        self.assertLessEqual(dimensions["scroll"], dimensions["viewport"])

    def test_page_does_not_request_external_assets(self):
        requests = []
        self.page.on("request", lambda request: requests.append(request.url))
        self.page.reload()
        self.page.wait_for_timeout(100)
        self.assertTrue(all(url.startswith(self.base_url) for url in requests))


if __name__ == "__main__":
    unittest.main()