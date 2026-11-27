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

## Xác minh đối tượng khảo sát — CP3

- **Người phụ trách:** Nguyễn Đức Nhật.
- **Phương pháp thu thập:** Khảo sát trực tuyến thông qua Google Forms.
- **Kênh phân phối:** Facebook và Gmail.
- **Đối tượng khảo sát hướng đến:** Người từ 18 đến 25 tuổi, có trải nghiệm mua sắm trên sàn thương mại điện tử và không thuộc nhóm BacTrung.
- **Số người ngoài nhóm đã xác nhận tại thời điểm chốt CP1:** 81 người, theo ghi nhận của người phụ trách khảo sát.
- **Tổng số phản hồi trong snapshot phân tích:** 64.
- **Số phản hồi đáp ứng bộ lọc hành vi:** 42.
- **Phương pháp xác minh:** Đối chiếu đối tượng được tiếp cận thông qua các kênh phân phối khảo sát và sàng lọc phản hồi dựa trên nền tảng mua sắm, thời điểm mua sắm gần nhất và thời lượng đọc đánh giá sản phẩm.

Khảo sát được thực hiện dưới hình thức ẩn danh, không thu thập tên, email hoặc thông tin nhận dạng cá nhân.

Do đó, số lượng người ngoài nhóm được ghi nhận tại CP1 cần được phân biệt với số phản hồi đáp ứng bộ lọc hành vi. Chưa thể đối chiếu độc lập danh tính, độ tuổi và tính duy nhất của từng người trong 42 phản hồi thuộc tập phân tích chính.
