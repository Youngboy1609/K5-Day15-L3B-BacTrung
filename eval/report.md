# Báo cáo đánh giá — lượt 1 → một cải tiến → lượt 2

> Điền ở guide bước 4.1. Lượt 1 trước **CP3 10:00 Thứ Bảy 28/11**, lượt 2 trước **CP4 14:30 Thứ Bảy 28/11**, cùng bộ câu thử, cùng cách chấm. Chấm ở rubric R5.
> Số lấy từ `python run.py score eval/run-1.csv` (và `run-2.csv`) sau khi điền cột `pass`. **Kết quả thấp ghi thật vẫn đủ điểm.**
> Không được: sửa chuẩn "đạt", bỏ câu thử trượt, sửa `expected` cho khớp output, sửa kết quả lượt đã chạy.

## 1. Kết quả

| Lượt | Run ID | Đạt / tổng | % | thuong | kho | tu_choi | So với chuẩn "đạt" |
|---|---|---|---|---|---|---|---|
| 1 | `run-1@20261128-094539` | 23/24 | 96% | 4/5 | 13/13 | 6/6 | đạt |
| 2 | | __/__ | | __/__ | __/__ | __/__ | đạt / chưa |

Kết quả từng câu: `eval/run-1.csv`, `eval/run-2.csv`. Trace: `traces/run-1.jsonl`, `traces/run-2.jsonl`.

## 2. Lỗi lượt 1 — gom thành nhóm có tên

Lượt 1 chỉ có **một câu trượt (B10)**. Ba nhóm còn lại là điểm yếu đọc được trong output của các câu **đã đạt**: không vi phạm `pass_criterion`, không làm đổi kết quả 23/24, nhưng ảnh hưởng người dùng. Số liệu đếm từ `eval/run-1.csv` (11 câu `status=ok`, 13 câu bị chặn trước khi gọi model).

| Nhóm lỗi | Số câu | Câu | Làm câu trượt? |
|---|---|---|---|
| A. Output của model bị bộ kiểm JSON loại, người dùng không nhận được phân tích | 1 | B10 | **Có** |
| B. Cùng input, kết quả dao động giữa các lần gọi | 9 | B01, B02, B03, B15, B16, B18 · B04, B10, B17 | Không (trừ B10) |
| C. Lý do đánh giá viết bằng tiếng Anh trong app tiếng Việt | 11 | Mọi câu `status=ok` | Không |
| D. Không phân biệt được các ca: 11/11 câu `ok` đều ra "Cần xem xét thêm", lời khuyên là một câu cố định | 11 | Mọi câu `status=ok` | Không |

**≥3 lỗi cụ thể:**

| Câu | Input | Output | Vì sao sai |
|---|---|---|---|
| B10 | Listing `rugged-002`, Samsung Galaxy S24, Ốp chống sốc viền nhám | `status=error`, `code=ANALYSIS_UNAVAILABLE`. Trace có lời gọi `gpt-4o` thành công (462 token vào / 250 ra), model trả JSON có mảng `reviews` | Tiêu chí cần `status=ok`. B04 và B17 cùng input đều qua bộ kiểm, nên lỗi nằm ở `_validate_judgements` trong `codebase/agent.py` loại output của lần gọi này. Trace chỉ lưu khoảng 300 ký tự đầu output nên **chưa xác định được trường gây lỗi**. Giả thuyết *(chưa kiểm)*: một `reason` dài quá 240 ký tự, vì B10 có 250 token ra so với 215 ở B04 và 179 ở B17; hoặc `media_assessment` ngoài 4 giá trị hợp lệ. Người dùng chỉ thấy "chưa đưa ra khuyến nghị" mà không biết vì sao. |
| B01 · B02 · B03 · B15 · B16 · B18 | Cùng một input: listing `clear-001`, iPhone 15 Pro, Ốp trong suốt viền đen | `weighted_score` lần lượt 0,193 · 0,032 · 0,237 · 0,078 · 0,032 · 0,078; cả 6 đều "Cần xem xét thêm" | Cùng 8 review, điểm dao động 0,032–0,237. B03 (0,237) chỉ cách ngưỡng "Đáng mua" (0,25) 0,013, nên một lần gọi khác có thể đổi khuyến nghị dù dữ liệu không đổi. Benchmark chấm từng câu riêng nên không bắt được độ lệch này. |
| B01 (đại diện cho 11 câu `ok`) | Như trên | 57/57 `reason` trong `review_assessments` viết bằng tiếng Anh, ví dụ B04: "The review talks about the case fitting well and buttons being responsive…" | Người dùng đọc tiếng Việt và cần lý do để tự quyết. Prompt hệ thống viết bằng tiếng Anh và không yêu cầu ngôn ngữ trả lời. |
| B01 · B04 · B15 (đại diện cho 11 câu `ok`) | Hai listing, 8 review và 3 review đúng biến thể | `recommendation` luôn "Cần xem xét thêm"; `advice` giống hệt nhau ở cả 11 câu: "Đọc thêm review đúng biến thể và kiểm tra điều kiện đổi trả…" | Với B11–B13 (1 review) đây là kết quả đúng chính sách. Với listing 8 review, kết quả có thể vẫn hợp lý vì có R004–R006 chê, nhưng **bộ câu thử không có ca nào kỳ vọng "Đáng mua" hay "Không đáng mua"**, nên chưa kiểm được app có bao giờ đưa khuyến nghị dứt khoát. Lời khuyên cố định không dựa trên dẫn chứng của từng ca. |

**Nhóm đề xuất sửa cho lượt 2: A (B10)**, kèm phần dao động của nhóm B. Đây là lỗi duy nhất làm câu trượt, và người dùng không nhận được gì dù model đã trả lời. Hướng sửa thuộc phạm vi của Quang: ghi lý do bộ kiểm từ chối vào output hoặc log; gọi lại một lần khi JSON không hợp lệ; ép schema đầu ra (structured output, giới hạn độ dài `reason`) để giảm dao động. Nhóm C và D không đổi % đạt; ghi ở §4 nếu không sửa kịp.

Trace đầy đủ ở `traces/run-1.jsonl`.

## 3. Một lần cải tiến

- Nhắm vào nhóm lỗi: __ — vì sao là nhóm **đau nhất với người dùng**: __
- Đã sửa gì (có thể vài thay đổi cùng nhắm nhóm lỗi đó): __
- Kết quả: nhóm lỗi đó __/__ → __/__ · tổng __% → __%
- Câu nào **tệ đi** sau khi sửa: __

## 4. Còn lại

- Lỗi chưa sửa + nguy hiểm thế nào: __
- Nếu có thêm 1 tuần: __
