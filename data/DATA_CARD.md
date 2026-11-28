# Data card — CP2

## Dataset 1 · Khảo sát review Shopee

| | |
|---|---|
| Dùng để làm gì | Bằng chứng pain bước đầu; tạo tình huống benchmark có nguồn người dùng |
| Từ đâu | `evidence/survey/results.csv`, xuất từ Google Forms; câu hỏi và quy tắc lọc ở `evidence/survey/` |
| Xử lý | Bỏ timestamp chính xác, gán ID `S001`–`S064`, trim whitespace cuối ô; phân tích chọn đúng platform Shopee, lần gần nhất ≤90 ngày, có thời lượng đọc review; multiple choice đếm theo option, mẫu số 42 (`evidence/survey/analyze_results.py`) |
| Số dòng / số đoạn | 64 dòng trong CSV; 42 thuộc tập phân tích chính |
| Phiên bản / ngày lấy | Snapshot 27/11/2026; PR #3 |
| Nhãn | Dữ liệu khảo sát thật, ẩn danh theo mô tả form |
| Giới hạn | Chưa xác minh độc lập người ngoài nhóm/trùng người; convenience sample và self-report; 64 dòng CSV là mẫu số CP2; số 65 trong PR không có dữ liệu theo dòng để kiểm chứng và không dùng trong phân tích; không đại diện dân số; ngành khác không chứng minh pain riêng của ốp |

Không dùng dữ liệu khảo sát làm đầu vào cho mock hoặc model. Trích dẫn xuất hiện trong spec/canvas đã bỏ thông tin nhận diện trực tiếp; vẫn cần Nhật rà privacy trước khi nộp bản cuối.

## Dataset 2 · Local phone-case review fixtures

| | |
|---|---|
| Dùng để làm gì | Prototype local-only, benchmark luồng lọc đúng listing/dòng máy/biến thể |
| Từ đâu | `data/reviews.json`; synthetic do coding assistant viết theo scope sản phẩm |
| Xử lý | 2 listing fixture, lọc exact `product_id` + `phone_model` + `case_variant`; lấy mẫu tối đa 12 review theo nhóm sao, seed 42 |
| Số dòng / số đoạn | 14 review synthetic trên 2 listing; trong đó có review cố tình thuộc dòng máy/biến thể khác để kiểm tra không trộn |
| Phiên bản / ngày lấy | `cp2-fixture-1`; tạo cho CP2 |
| Nhãn | `synthetic` |
| Giới hạn | Không lấy từ Shopee, chưa được thành viên kiểm tay, không đại diện người mua; không phải bằng chứng pain; `helpful_count` cũng là số synthetic, không phải lượt vote thu thập được |

**Media CP3:** R004 và R101 có ảnh PNG synthetic cục bộ trong `data/media/`; R004 có thêm một frame trích từ video synthetic 2 giây được tạo từ ảnh fixture (file nguồn `R004-synthetic-video.mp4`). Các media này không phải ảnh/video Shopee và frame chỉ đại diện cho một hình tĩnh, không cho biết chuyển động hay âm thanh. Nếu collector gặp CAPTCHA, người dùng tự xác nhận rồi chạy `retry`; nếu media bị chặn, workflow dùng text đã có và ghi rõ media chưa được đánh giá.

**Cách sinh/kiểm:** nội dung review và `helpful_count` do coding assistant soạn thủ công để minh họa công thức, không lấy review/vote thật và không dùng seed để sinh. Seed 42 chỉ điều khiển lấy mẫu nếu số review vượt giới hạn. Minh cần xác nhận/kiểm tay fixture trước khi demo. Khi tích hợp dữ liệu thật, chỉ điền count nếu nguồn Shopee cung cấp; thiếu thì để null/không có.

## Dataset 3 · Benchmark

`eval/benchmark.csv` có 10 tình huống. Bốn tình huống được chọn dựa trên khảo sát (gồm một phản hồi mở về ốp và ba lựa chọn pain có mã dòng); phản hồi survey chỉ định hướng tình huống, còn listing/reviews đầu vào và output kỳ vọng kỹ thuật vẫn dùng fixture synthetic. Sáu câu còn lại do nhóm/coding assistant tự viết.
