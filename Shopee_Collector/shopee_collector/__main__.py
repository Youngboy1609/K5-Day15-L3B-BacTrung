from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from .storage import Store
from .parsing import extract_payload


ROOT = Path(__file__).resolve().parent.parent


def load_config(path):
    cfg = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    for k in ("max_pages_per_run", "max_products_per_run", "max_queue_size", "scroll_steps",
              "listing_pages_per_seed", "review_pages_per_product"):
        if not isinstance(cfg[k], int) or cfg[k] < 1:
            raise ValueError(f"{k} must be a positive integer")
    if cfg["delay_ms"] < 3000 or cfg["settle_ms"] < 500:
        raise ValueError("delay_ms >= 3000 and settle_ms >= 500 required")
    if cfg["network_price_divisor"] <= 0:
        raise ValueError("network_price_divisor must be positive")
    if cfg.get("max_idle_scrolls", 2) < 1 or cfg.get("max_attempts", 2) < 1:
        raise ValueError("max_idle_scrolls and max_attempts must be positive")
    if not isinstance(cfg.get("detail_required_fields", []), list):
        raise ValueError("detail_required_fields must be a list")
    return cfg


def main():
    if sys.platform == "win32" and not os.environ.get("PYTHONIOENCODING"):
        for stream in (sys.stdout, sys.stderr):
            if not stream.isatty():
                stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Shopee Collector — thu thập dữ liệu được trình duyệt tải, có lưu tiến độ")
    sub = ap.add_subparsers(dest="command", required=True)
    for name in ("run", "export", "demo"):
        p = sub.add_parser(name)
        p.add_argument("--output", default="output/demo" if name == "demo" else "output/live")
        if name == "run":
            p.add_argument("--config", default=str(ROOT / "config/settings.json"))
            p.add_argument("--auto", action="store_true", help="Chạy hàng chờ rồi thoát; gặp chặn thì dừng")
            p.add_argument("--refresh", action="store_true", help="Thăm lại các sản phẩm trong seeds đã xử lý, giữ dữ liệu cũ")
            p.add_argument("--all-reviews", action="store_true", help="Chuyển trang đánh giá đến khi giao diện hết trang hoặc dừng tiến triển")
            p.add_argument("--remember-session", action="store_true", help="Chủ động lưu phiên vào browser-profile trên máy này")
            p.add_argument("--cdp", metavar="URL",
                           help="Kết nối tường minh tới Chrome remote-debugging, ví dụ http://127.0.0.1:9222")
    args = ap.parse_args()
    store = Store(args.output, recover_queue=False)
    try:
        rules = json.loads((ROOT / "config/taxonomy.json").read_text(encoding="utf-8"))
        if args.command == "demo":
            # Deliberately synthetic; never presented as a live Shopee dataset.
            fixture = json.loads((ROOT / "tests/synthetic_payload.json").read_text(encoding="utf-8"))
            store.ingest(extract_payload(fixture, rules=rules, source_url="synthetic://offline-test",
                                        observed_at="SYNTHETIC_DATA_NOT_LIVE"))
            report = store.export()
            print("DỮ LIỆU GIẢ LẬP, KHÔNG PHẢI KẾT QUẢ CRAWL SHOPEE.")
            print(json.dumps(report, ensure_ascii=False, indent=2))
        elif args.command == "export":
            print(json.dumps(store.export(), ensure_ascii=False, indent=2))
        else:
            from .browser import Collector
            cfg = load_config(args.config)
            cfg["all_review_pages"] = args.all_reviews
            try:
                asyncio.run(Collector(store, cfg, rules).start(
                    auto=args.auto, remember=args.remember_session, cdp=args.cdp, refresh=args.refresh))
            except ConnectionRefusedError as exc:
                ap.exit(1, f"{exc}\n")
    except KeyboardInterrupt:
        print("Đã dừng. Dữ liệu đã ghi vẫn nằm trong SQLite; dùng export để xuất lại.")
        store.export()
    finally:
        store.close()


if __name__ == "__main__":
    main()
