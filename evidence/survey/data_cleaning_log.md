# Nhật ký làm sạch khảo sát — 27/11/2026

Nguồn: Google Forms và bảng tính do Nhật quản lý (link nguồn không lưu trong bản public để tránh vô tình mở quyền xem response gốc).

Bản chụp tại thời điểm đọc được mô tả có 69 phản hồi; lần trước đã xóa 10 phản hồi theo phê duyệt; bản `results.csv` merge có 64 phản hồi và 5 phản hồi được tách khỏi phân tích để chờ duyệt. File public đã bỏ dấu thời gian chính xác, thay bằng mã ẩn danh `S001`–`S064`, và bỏ khoảng trắng cuối ô; nội dung câu trả lời không được viết lại. Không đưa `survey_raw_snapshot.csv` lên repo.

**Chốt số liệu dùng cho CP2:** lấy 64 dòng hiện có trong `results.csv` làm toàn bộ mẫu số công bố; 42 dòng đủ điều kiện là tập phân tích chính. Con số 65 trong mô tả PR là phép tính từ tổng 80 trừ 15 loại, nhưng không có bản dữ liệu theo dòng để xác minh hoặc chỉ ra phản hồi thứ 65. Vì vậy 65 được giữ lại như một con số lịch sử của PR, không dùng làm mẫu số hay tuyên bố số dòng đã kiểm chứng. Snapshot 69 trừ 5 phản hồi chờ duyệt khớp với 64 dòng public; không tự tạo, thêm hoặc suy đoán phản hồi còn thiếu. Phần chưa thể xác minh là nguồn gốc của chênh lệch giữa thống kê PR và snapshot, không phải số dòng của CSV hiện tại.

| Dòng trên Sheets lúc đọc | Nền tảng | Lý do tạm loại |
|---:|---|---|
| 62 | Shopee | Q6 không xem đánh giá, nhưng Q7 và Q8 cho biết đọc/tiếp tục đọc đánh giá. |
| 63 | Shopee | Q6 không xem đánh giá, nhưng Q7 mất thời gian đọc và Q8 tiếp tục đọc. |
| 64 | Shopee | Q3 = 100 lần/30 ngày; ngoại lai theo tiền lệ lọc đã duyệt, chưa chứng minh sai. |
| 65 | Shopee | Q8 đồng thời tìm hiểu thêm, hoãn mua và đã đủ thông tin; cần xác minh, không nhất thiết sai. |
| 70 | Shopee | Q3 = 100 lần/30 ngày; ngoại lai theo tiền lệ lọc đã duyệt, chưa chứng minh sai. |

Dòng 66 có nội dung khác dòng 65 và được giữ lại. Không loại phản hồi vì câu mở ngắn, không gặp pain hoặc kết quả mua tích cực. Các số 100 lần có thể là thật do câu hỏi tính cả lần tìm kiếm, không chỉ số đơn. Nên chạy phân tích độ nhạy có và không có các trường hợp ngoại lai; không kết luận gian lận. Chưa xác minh người trả lời ngoài nhóm, danh tính trùng lặp hoặc tính riêng cho phân khúc ốp lưng. Không ghi nhận các câu trả lời mới phát sinh sau bản chụp.
