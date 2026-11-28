# Dàn slide → lấy số từ file nào

> Làm ở guide bước 5.1. Luật: **không có bằng chứng thì không có slide** — mỗi trang ≥1 con số / trích dẫn có nguồn / kết quả đo.
> Xuất PDF thành `demo-slides.pdf` ở thư mục gốc repo, nộp tại CP4 14:30 Thứ Bảy 28/11. Nộp PDF, không nộp link.

| # | Trang | Có gì | Số lấy từ | Xong |
|---|---|---|---|---|
| 1 | Đọc review ốp lưng đúng mẫu trên Shopee | Lát cắt demo và 41/42 người gặp ít nhất một khó khăn | `evidence/summary.md` | ☑ |
| 2 | Pain point của người mua Shopee | 28/42 cho từng khó khăn phổ biến nhất, 20/42 chọn cả hai. Trung vị thời gian đọc và trích dẫn S055 | `evidence/survey/results.csv`, `evidence/summary.md`, `spec.md` §2 | ☑ |
| 3 | Giải pháp | Sơ đồ lọc đúng biến thể, AI đánh giá và trả dẫn chứng. Ví dụ R004 | `spec.md` §4, `data/reviews.json` | ☑ |
| 4 | Demo trực tiếp | Ca thường B10 và ca khó B03. Ảnh chụp từ video CP3, kèm liên kết video dự phòng | `eval/benchmark.csv`, `eval/run-2.csv`, `docs/quang-demo.md` | ☑ |
| 5 | Đánh giá CP4 | 23/24 và 24/24 trên cùng bộ thử, kèm run ID. B10 trả được phân tích ở lượt 2. B01/B02 cho thấy khuyến nghị còn dao động | `eval/README.md`, `eval/report.md` | ☑ |
| 6 | Chi phí khi dùng thật | Bình quân 50 phiên và 35 phiên có gọi model, cách ước tính mỗi task đạt, ba kịch bản theo tháng | `cost/simulate-1.csv`, `cost/cost-estimate.md` | ☑ |
| 7 | Success metrics | 60/60 lượt đánh giá đúng biến thể, 30/30 dẫn chứng khớp nguyên văn, 12/12 ca cần từ chối được xử lý đúng | `eval/metric_spec.yaml`, `eval/run-2.csv`, `data/reviews.json` | ☑ |
| 8 | Kết luận hackathon | Giá trị cho người mua, kết quả trên dữ liệu demo và chi phí API dự kiến | `spec.md` §1, §7, §8 | ☑ |

Logo Shopee trên trang mở đầu lấy từ [Sea Limited](https://www.sea.com/products/shopee). Ảnh ốp là minh họa tạo bằng AI. Ảnh ở trang demo trích từ video CP3 của nhóm.

**Trước khi lên:** tải repo về một máy khác (hoặc thư mục mới), chạy theo mục "Chạy trong 3 phút" của `README.md` · `.env` có trên máy demo, đã gọi thử 1 câu trong vòng 1 giờ trước giờ demo · video dự phòng mở được bằng cửa sổ ẩn danh · biết bản chạy thử sẽ làm gì với **1 câu thử lạ** của giám khảo.

Ai nói trang nào (mỗi người ≥1 phần — dự kiến theo phân công):

| Trang | Người nói |
|---|---|
| 1–2 | Nguyễn Đức Nhật (bằng chứng pain & khảo sát) |
| 3–4 | Phạm Đăng Quang & Hồ Trọng Nghĩa (giải pháp & demo live) |
| 5–6 | Nguyễn Cao Minh & Nguyễn Đức Nhật (đánh giá lượt 1 → lượt 2 & chi phí) |
| 7–8 | Hồ Trọng Nghĩa (tiêu chí thành công & kết luận) |
