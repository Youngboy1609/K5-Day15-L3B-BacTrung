# Khai báo dùng AI

| Việc | Công cụ AI | AI làm gì | Người kiểm/sửa gì | Ai phụ trách |
|---|---|---|---|---|
| Code prototype CP2 | OpenCode coding assistant | Hỗ trợ soạn local workflow, input validation, fixture lookup và test | Chạy unit tests, kiểm output/citation; nhóm cần tự giải thích code | Quang/Nghĩa |
| Mock judge | OpenCode coding assistant | Soạn heuristic phân loại review synthetic | Được gắn nhãn mock; chưa xem là chất lượng AI thật | Quang |
| Phân tích survey | Python standard library, script `evidence/survey/analyze_results.py` | Đếm 64 dòng, lọc 42 eligible, tổng hợp multi-select/industry/time và mã quote | Test tái lập số chính; Nhật cần xác nhận eligibility và nguồn totals chưa khớp | Nhật/Nghĩa |
| Soạn benchmark | OpenCode coding assistant | Draft 6 ca tự viết và đóng khuôn 4 tình huống có nguồn survey (rows 20, 37, 55) | `source` ghi rõ; input fixture vẫn synthetic; không tạo respondent/quote | Minh |
| Fixture synthetic | OpenCode coding assistant | Soạn 14 review giả lập và các helpful_count minh họa để kiểm công thức | Chưa được thành viên kiểm tay; count không phải vote thật, không coi là review thật/pain evidence | Minh |
| Chấm độc lập output CP2 | Minh và Quang | Chấm thủ công 5 output đại diện theo metric/benchmark | Đồng thuận 5/5; Quang kiểm tra chéo benchmark 10/10 đạt; ghi tại `eval/README.md` và comment PR #4 | Minh/Quang |
| Model thật CP3 | OpenAI GPT-4o | Phân tích text và ảnh synthetic cục bộ; trả JSON nhãn (lượt 1: 23/24) | Token lấy từ `usage`; ảnh/media là synthetic; không gọi Shopee | Quang/Nghĩa |
| Cải tiến CP4 & mô phỏng | Antigravity + OpenRouter (`openai/gpt-4o-mini`) | Sửa lỗi `ANALYSIS_UNAVAILABLE` (`json_schema` strict, validator, retry), chạy lượt 2 (24/24) và mô phỏng chi phí 50 phiên, dựng slide PDF | Chạy unit tests, chấm tay từng câu `eval/run-2.csv`, đối chiếu số `simulate-1-summary.md` và `spec.md` | Quang/Minh/Nhật/Nghĩa |
| Hiệu chỉnh báo cáo và thiết kế slide CP4 | Codex, ImageGen | Đối chiếu mẫu số chi phí và kết quả eval. Thiết kế lại PDF và tạo ảnh minh họa ốp cho trang mở đầu | Duyệt số liệu, cách diễn giải và nội dung slide trước khi nộp | Nghĩa |
| Viết spec, Data Card, summary | OpenCode coding assistant | Hỗ trợ draft và tính bảng mô tả từ CSV | Đối chiếu với CSV/log merge; ghi rõ giới hạn và số nguồn chưa khớp | Nghĩa/Nhật |

Không dùng AI để tạo người khảo sát, quote hoặc câu trả lời survey. Không sửa kết quả lượt đã chạy. Cần cập nhật dòng nếu nhóm dùng model/AI khác ở CP3.
