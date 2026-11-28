# Báo cáo đánh giá — lượt 1 → một cải tiến → lượt 2

> Điền ở guide bước 4.1. Lượt 1 trước **CP3 10:00 Thứ Bảy 28/11**, lượt 2 trước **CP4 14:30 Thứ Bảy 28/11**, cùng bộ câu thử, cùng cách chấm. Chấm ở rubric R5.
> Số lấy từ `python run.py score eval/run-1.csv` (và `run-2.csv`) sau khi điền cột `pass`. **Kết quả thấp ghi thật vẫn đủ điểm.**
> Không được: sửa chuẩn "đạt", bỏ câu thử trượt, sửa `expected` cho khớp output, sửa kết quả lượt đã chạy.

## 1. Kết quả

| Lượt | Run ID | Đạt / tổng | % | thuong | kho | tu_choi | So với chuẩn "đạt" |
|---|---|---|---|---|---|---|---|
| 1 | `run-1@20261128-094539` | 23/24 | 96% | 4/5 | 13/13 | 6/6 | đạt |
| 2 | `run-2@20261128-104603` | 24/24 | 100% | 5/5 | 13/13 | 6/6 | đạt |

Kết quả từng câu: `eval/run-1.csv`, `eval/run-2.csv`. Trace: `traces/run-1.jsonl`, `traces/run-2.jsonl`.

## 2. Lỗi lượt 1 — gom thành nhóm có tên

| Nhóm lỗi | Số câu | Câu |
|---|---|---|
| Output an toàn nhưng không hoàn thành phân tích | 1 | B10 |

**Chi tiết lỗi và quan sát lượt 1:**

| Câu | Input | Output | Vì sao sai / cần cải tiến |
|---|---|---|---|
| B10 | Samsung Galaxy S24, ốp chống sốc viền nhám | `ANALYSIS_UNAVAILABLE` sau khi model trả phản hồi | Người mua nhập đúng biến thể nhưng không nhận được phân tích. Trace chỉ lưu trích đoạn phản hồi, nên chưa xác định được trường khiến bộ kiểm tra từ chối. |
| B01–B03, B15, B16, B18 *(đạt tiêu chí từng câu)* | Cùng một đầu vào iPhone 15 Pro, ốp trong suốt viền đen | Điểm có trọng số dao động từ `0,032` đến `0,237` trên cùng 8 review | Cả sáu lần đều trả “Cần xem xét thêm”. Điểm cao nhất chỉ cách ngưỡng “Đáng mua” `0,013`. |
| B04 *(đạt tiêu chí từng câu)* | Samsung Galaxy S24, ốp chống sốc viền nhám | Lý do đánh giá viết bằng tiếng Anh | Giao diện dùng tiếng Việt. Người mua phải đọc phần giải thích bằng ngôn ngữ khác trước khi tự quyết. |

Lượt 1 trượt một câu (`B10`). Hai dòng tiếp theo ghi nhận vấn đề chất lượng quan sát được ở các câu đã đạt. B04 và B17 dùng cùng đầu vào với B10 và đều trả `status=ok` ở lượt 1.

## 3. Một lần cải tiến

- Nhóm lỗi ưu tiên là **không hoàn thành phân tích (`ANALYSIS_UNAVAILABLE`)**. Với B10, người mua nhập một link và biến thể có dữ liệu nhưng không nhận được dẫn chứng để quyết định.
- Đã sửa gì (cùng nhắm nhóm lỗi độ ổn định output và tương thích OpenRouter):
  1. Trong `codebase/ai.py`: hỗ trợ thêm `MODEL_PROVIDER=openrouter` (bên cạnh `openai`, `fake`) và bật `response_format` dạng `json_schema` (`strict: true`) khóa cứng các trường bắt buộc và tập giá trị enum (`sentiment`, `evidence_strength`, `media_assessment`), kèm fallback `json_object` nếu gặp HTTP 400.
  2. Trong `codebase/agent.py`: chuẩn hóa markdown fence, các biến thể chuỗi `media_assessment`/`evidence_strength`, cắt gọn `reason` vượt 240 ký tự thay vì đánh sập cả phiên, và retry tối đa 1 lần nếu validator gặp JSON lỗi tạm thời.
  3. Bổ sung unit test cho normalization và cơ chế retry trong `tests/test_agent.py`.
- `ANALYSIS_UNAVAILABLE` giảm từ **1/24 xuống 0/24**. B10 trả `status=ok` ở lượt 2 và tổng số câu đạt tăng từ **23/24 (96%) lên 24/24 (100%)**. Lượt 2 đổi cả model/nhà cung cấp (GPT-4o qua OpenAI sang GPT-4o-mini qua OpenRouter) và cách xử lý JSON, nên chưa tách được đóng góp của từng thay đổi.
- Theo tiêu chí pass/fail, không có câu nào chuyển từ đạt sang trượt. Ở lượt 2, B01 và B02 vẫn cùng đạt dù dùng cùng đầu vào và trả hai khuyến nghị khác nhau: “Cần xem xét thêm” (`0,191`) và “Đáng mua” (`0,316`). Các tiêu chí hiện tại chấm từng câu độc lập.

## 4. Còn lại

- Khuyến nghị còn dao động giữa các lần gọi cùng đầu vào. Bộ câu thử dùng 14 review `synthetic` và một khung hình tĩnh (`R004`). Lý do đánh giá còn xuất hiện bằng tiếng Anh, và nhóm chưa đo chất lượng trên review Shopee thật.
- Nếu có thêm một tuần: (1) Giữ nguyên model/nhà cung cấp và lặp các ca trùng đầu vào để đo độ ổn định của parser và khuyến nghị. (2) Đánh giá trên ít nhất 50 review ốp đã làm sạch. (3) Thử với 3–5 người ngoài nhóm, đo thời gian thực hiện và kiểm cách họ hiểu lý do đánh giá.
