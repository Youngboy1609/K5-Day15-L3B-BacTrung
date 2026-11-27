# Bàn giao workflow và demo của Quang

## Chạy mock

Chạy `python run.py` với `MODEL_PROVIDER=fake` hoặc khi chưa có `.env`. Mỗi đầu vào là một dòng JSON. Các mã dưới đây thuộc fixture tạm trong `agent.py`.

- **Ca thường:** `{"product_url":"https://shopee.vn/ten-san-pham-i.123456.987654","phone_model":"iPhone 15","case_variant":"Ốp trong suốt viền đen"}`. Kết quả mock dùng `R014`, `R015` và báo độ phủ `2/2`.
- **Ca lẫn dòng máy:** dùng cùng link, đổi `phone_model` thành `iPhone 15 Pro`. Kết quả mock dùng `R012`, `R013` và trả **Cần xem xét thêm**. Kiểm các mã của iPhone 15 không xuất hiện.
- **Ca thiếu căn cứ:** chọn `iPhone 15 Pro` và `Ốp trong suốt viền trắng`. Kết quả báo độ phủ `1/1` và **Cần xem xét thêm** vì review chỉ khen chung chung.
- **Link ngoài bộ:** đổi link thành `https://shopee.vn/product/123456/987655`. Kết quả báo **Chưa có dữ liệu**.

## Tích hợp dữ liệu của Minh

Luồng gọi `codebase/tools.py` nếu có `lookup_reviews(product_url, phone_model, case_variant)` được gắn `@tool`. Tên và giá trị trả về đề xuất cho việc tích hợp:

- Trả `None` với link ngoài bộ demo.
- Trả `{"reviews": [...], "counts_by_stars": {1: 2, 2: 4, 3: 0, 4: 11, 5: 35}}` với link có trong bộ. `reviews` là mẫu tối đa 12 dòng đúng sản phẩm, dòng máy và biến thể, theo JSON trong `PLAN.md`. `counts_by_stars` là số review trước lấy mẫu của đúng dòng máy và biến thể. Ví dụ trên dùng số minh họa.
- Trả danh sách rỗng và các tổng bằng 0 nếu biến thể chưa có review. Các đường dẫn ảnh và khung hình tính từ `data/`. Workflow nhận JPEG, PNG và WebP, với tối đa 5 MiB mỗi ảnh và 32 MiB dữ liệu ảnh đã mã hóa mỗi yêu cầu.

Quy tắc đề xuất cho khuyến nghị mua yêu cầu ít nhất 2 review hữu ích và tổng trọng số bằng chứng ít nhất 40% trọng số gốc. Chữ cụ thể có hệ số 0,75 và bằng chứng ảnh hoặc khung hình hợp lệ có hệ số 1. Nếu một hướng đạt 75% trọng số bằng chứng, app có thể khuyến nghị theo hướng đó. Khi có nhận xét trái chiều về độ vừa hoặc bảo vệ, app trả **Cần xem xét thêm**. Các ngưỡng này là lựa chọn triển khai của app.

## Kiểm model thật và quay CP3

1. Với OpenRouter, đặt `MODEL_PROVIDER=openrouter`, `MODEL_NAME=openai/gpt-4o-mini` và `API_KEY` của nhóm trong `.env`. Với OpenAI trực tiếp, dùng `MODEL_PROVIDER=openai`, `MODEL_NAME=gpt-5.4-nano` và khóa của OpenAI. Chạy `python run.py` và nhập ca thường với link, dòng máy và biến thể của bộ demo do Minh bàn giao.
2. Chạy ca khó có review khác dòng máy hoặc màu ốp. Đối chiếu mã nguồn ở mục **Dẫn chứng**, mốc của khung hình hỗ trợ lỗi độ vừa và trường hợp video chỉ quay bao bì. Dòng thống kê phải có model và token từ API.
3. Quay khoảng 30 giây. Giây 0–8 nhập link và chọn biến thể hoặc dán JSON đã chuẩn bị. Giây 8–20 bấm phân tích và hiện kết quả AI thật. Giây 20–30 chỉ vào độ phủ, mã review và mốc khung hình. Chuẩn bị ca khó cho phần demo trực tiếp và ghi lại một bản dự phòng với kết quả kiểm được.

### Kết quả kiểm CP3 cục bộ

[Video CP3, 30 giây](../demo/cp3-quang.mp4) dựng lại thao tác nhập JSON và phản hồi thực tế của `openai/gpt-4o-mini` qua OpenRouter. Hai ca dùng review và ảnh minh họa. Hai khung hình ở ca iPhone 15 Pro được trích ở giây 2 và giây 6 từ MP4 minh họa.

| Ca | Kết quả | Token vào / ra từ API |
|---|---|---:|
| iPhone 15 | Đáng mua, độ phủ 2/2, dùng ảnh của `R014` | 26.067 / 93 |
| iPhone 15 Pro | Cần xem xét thêm, độ phủ 2/2, trích riêng cảnh cấn camera `R012` ở `00:06` | 51.590 / 82 |

## Bàn giao CP4

Sau khi Minh ghi và chấm lượt 1, dùng `eval/report.md` và trace để chọn một nhóm lỗi cần sửa. Bàn giao bản sửa cho Minh để chạy lượt 2 trên cùng bộ câu thử. Thử lại ca thường và ca khó trên bản sửa trước khi quay bản dự phòng. Khi video có link chia sẻ, kiểm cả hai link qua cửa sổ ẩn danh trước khi gửi Nghĩa.

Tham chiếu kết nối [OpenRouter Chat Completions](https://openrouter.ai/docs/api/api-reference/chat/send-chat-completion-request) · [OpenAI Vision](https://developers.openai.com/api/docs/guides/images-vision?api-mode=chat) · [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=chat).
