# Khai báo dùng AI

README của nhóm có mục "Dùng AI vào việc gì" (2–3 dòng, bắt buộc). Ghi chi tiết vào bảng dưới đây.

> Luật của đề: dùng AI để làm bài thoải mái, nhưng **ai không giải thích được phần có tên mình thì phần đó nhận 0 điểm**. Khai thiếu không bị trừ; giấu mới bị.

| Việc | Công cụ AI | AI làm gì | Người kiểm/sửa gì | Ai phụ trách |
|---|---|---|---|---|
| Code bản chạy thử | OpenCode (coding assistant) | Soạn workflow mock, kiểm JSON và tra fixture cục bộ | Nhóm phải rà code, test và giải thích được; chưa ghi nhận xác nhận thủ công | Nghĩa / Quang |
| Prompt / thiết kế lời gọi mô hình | OpenCode | Soạn system instruction và schema output cho bước judge | CP2 đang mock; chưa nối model thật | Quang |
| Đào data / viết script đếm | Không dùng | Chưa đào review thật hoặc chạy script pain-evidence | Chưa có kết quả | Nhật / Minh |
| Rà câu hỏi khảo sát | Chưa thực hiện | Form và câu hỏi chưa được cung cấp cho coding assistant | Nhật tự kiểm trước khi phát | Nhật |
| Viết câu thử (benchmark) | OpenCode | Soạn 10 tình huống kỹ thuật nháp từ fixture/scope đã thống nhất | Hiện cả 10 câu tự viết (`tu_viet`); cần thay/cập nhật một phần bằng tình huống thật sau khảo sát | Minh |
| Sinh data `synthetic` | OpenCode | Soạn 14 review fixture giả lập cho 2 listing | Chưa được thành viên kiểm tay; đây không phải review thật hoặc bằng chứng pain | Minh |
| Chấm cột `pass` bằng LLM | Không dùng | Chưa chạy chấm LLM | Chưa có | Minh |
| Slide, văn bản | OpenCode | Hỗ trợ soạn draft `spec.md`, Data Card và ghi chú CP2 | Nhóm phải kiểm nội dung và số liệu; khảo sát, nguồn ngoài và ngưỡng chưa xác nhận | Nghĩa |

**Không dùng AI để:** tạo người được phỏng vấn, trích dẫn, câu trả lời khảo sát; sửa kết quả các lượt đã chạy (`eval/run-*.csv`, `cost/simulate-*.csv`, `traces/`).
