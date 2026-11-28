# CP4 — Lượt đối chứng GPT‑4o

Hồ sơ này bổ sung cho bộ kết quả CP4 đã nộp, vốn dùng GPT‑4o-mini qua OpenRouter ở lượt 2. Các file dưới đây giữ nguyên tên, mã lượt và nội dung do khung tạo, kể cả tên trùng với artefact chính trong `eval/`, `cost/` và `traces/` ở thư mục gốc.

- **Eval:** [`run-2@20261128-141058`](eval/run-2.csv), [trace](traces/run-2.jsonl). GPT‑4o qua OpenAI, cùng 24 câu và chuẩn chấm với lượt 1: **24/24**, thường 5/5, khó 13/13, từ chối 6/6.
- **Mô phỏng:** [`simulate-1@20261128-141638`](cost/simulate-1.csv), [tóm tắt](cost/simulate-1-summary.md), [trace](traces/simulate-1.jsonl). 50 phiên, seed 42, 0 phiên lỗi; tỉ lệ đạt lấy từ lượt đối chứng trên. Theo cách tính của khung, **$0.0046/task đạt benchmark**, gồm cả từ chối đúng.
- **Bản chạy:** UI và workflow dựa trên `12eefd70`, thêm tối đa một lần gọi lại khi phản hồi không qua bộ kiểm tra cấu trúc. B10 qua ngay lần gọi đầu; không có câu nào phải gọi lại trong lượt eval này. B01 và B02 cùng đầu vào nhưng vẫn cho hai khuyến nghị khác nhau. Lượt đo dùng fixture tổng hợp và chưa cho biết impact khi dùng thật.
