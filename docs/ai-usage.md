# Khai báo dùng AI

| Việc | Công cụ AI | AI làm gì | Người kiểm/sửa gì | Ai phụ trách |
|---|---|---|---|---|
| Code prototype CP2 | OpenCode coding assistant | Hỗ trợ soạn local workflow, input validation, fixture lookup và test | Chạy unit tests, kiểm output/citation; nhóm cần tự giải thích code | Quang/Nghĩa |
| Mock judge | OpenCode coding assistant | Soạn heuristic phân loại review synthetic | Được gắn nhãn mock; chưa xem là chất lượng AI thật | Quang |
| Phân tích survey | Python standard library, script `evidence/survey/analyze_results.py` | Đếm 64 dòng, lọc 42 eligible, tổng hợp multi-select/industry/time và mã quote | Test tái lập số chính; Nhật cần xác nhận eligibility và nguồn totals chưa khớp | Nhật/Nghĩa |
| Soạn benchmark | OpenCode coding assistant | Draft 6 ca tự viết và đóng khuôn 4 tình huống có nguồn survey (rows 20, 37, 55) | `source` ghi rõ; input fixture vẫn synthetic; không tạo respondent/quote | Minh |
| Fixture synthetic | OpenCode coding assistant | Soạn 14 review giả lập và các helpful_count minh họa để kiểm công thức | Chưa được thành viên kiểm tay; count không phải vote thật, không coi là review thật/pain evidence | Minh |
| Chấm LLM | Không dùng | Chưa dùng LLM chấm output | Cần người thứ hai chấm 5 output trước CP2 sign-off | Nghĩa/Minh |
| Viết spec, Data Card, summary | OpenCode coding assistant | Hỗ trợ draft và tính bảng mô tả từ CSV | Đối chiếu với CSV/log merge; ghi rõ giới hạn và số nguồn chưa khớp | Nghĩa/Nhật |

Không dùng AI để tạo người khảo sát, quote hoặc câu trả lời survey. Không sửa kết quả lượt đã chạy. Cần cập nhật dòng nếu nhóm dùng model/AI khác ở CP3.
