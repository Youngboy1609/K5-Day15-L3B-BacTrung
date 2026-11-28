# Bàn giao demo CP3 — Quang

## Video

- [Bản MP4, khoảng 30 giây](../evidence/cp3-quang-demo-frame-30s.mp4)
- [Bản WebM nguồn](../evidence/cp3-quang-demo-frame-30s.webm)

Demo chạy trên fixture cục bộ: 10 review tổng cộng, trong đó 8 review khớp chính xác `iPhone 15 Pro × Ốp trong suốt viền đen`; 2 review khác biến thể không được đưa vào phân tích. Không crawl Shopee trong demo. Review, ảnh và video đều synthetic.

Video synthetic dài 2 giây chỉ dùng để trích một frame tĩnh cho review R004. Một frame không chứng minh chuyển động hay âm thanh; UI và output ghi rõ giới hạn này.

## Kiểm tra đã thực hiện

- B01 chạy một lượt GPT‑4o thật qua `python -B run.py eval --try 1`: 1 lần gọi model, 1 lần gọi công cụ, 1.437 token vào và 437 token ra. Kết quả chỉ là smoke test, không phải lượt benchmark được chấm.
- B01 phân tích 8/8 review đúng biến thể và nêu dẫn chứng R004, R002, R010.
- Cặp dòng máy/biến thể không khớp đã được kiểm qua API và trả `VARIANT_NOT_FOUND`, không tạo khuyến nghị.
- Test offline: 40 app tests (1 skipped) và 50 collector tests.

Toàn bộ bằng chứng này chỉ xác nhận workflow trên fixture synthetic; chưa chứng minh chất lượng trên review Shopee thật.
