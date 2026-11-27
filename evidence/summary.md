# Tổng hợp bằng chứng pain — CP2 bước đầu

> Khảo sát bao quát người mua đã đọc review Shopee ở nhiều ngành; demo riêng là ốp điện thoại. Đây là mẫu tự chọn, không đại diện thống kê cho toàn bộ người mua.

## 1. Nguồn và cách lọc

- Nguồn: Google Forms; bản đã merge: `evidence/survey/results.csv` (CSV có 64 dòng phản hồi).
- Tập phân tích chính: đúng nền tảng `Shopee` + lần gần nhất trong 90 ngày (`Trong 7 ngày gần đây` hoặc `Từ 8–30 ngày trước`) + có câu trả lời về thời lượng đọc review.
- Đếm được **42/64** dòng theo điều kiện trên; không xác minh độc lập người ngoài nhóm, người trùng, hoặc việc người trả lời thực sự đã xem review.
- Dữ liệu nhiều lựa chọn được đếm theo nguyên văn từng option; một phản hồi có thể nằm ở nhiều loại pain. Mẫu số từng lựa chọn luôn là 42.
- Có thể tái lập số bằng `python -B evidence/survey/analyze_results.py`; test kiểm tổng số ở `tests/test_survey_analysis.py`.
- **Chốt mẫu số CP2:** `results.csv` hiện có 64 dòng và là nguồn dữ liệu chuẩn cho thống kê đã công bố; 42 dòng đáp ứng điều kiện phân tích chính. Cleaning log ghi snapshot 69, gồm 64 dòng trong CSV và 5 phản hồi tạm chờ duyệt. Con số 65 trong mô tả PR (80 tổng trừ 15 loại) không có dữ liệu theo dòng để đối chiếu, nên chỉ giữ như số lịch sử của PR và không dùng làm mẫu số. Không suy đoán hoặc bổ sung phản hồi thứ 65; chênh lệch còn lại chỉ là nguồn gốc tally PR chưa xác minh.
- Convenience sample và self-report; không xác minh người ngoài nhóm, trùng phản hồi hay đại diện của nhóm ngành hàng. Kết luận chỉ mô tả người trả lời hợp lệ trong file.

## 2. Số chính

- Trong 42 phản hồi Shopee đủ điều kiện, **41/42** chọn ít nhất một tình huống khó khăn ở câu nhiều lựa chọn; 1/42 chọn “Không gặp khó khăn nào”.
- Các khó khăn được chọn (n, có thể trùng):

| Lựa chọn ở câu hỏi | Số người |
|---|---:|
| Review quá ngắn/không đủ thông tin | 28/42 |
| Nghi ngờ đánh giá thiếu khách quan/không đáng tin | 28/42 |
| Ảnh/video chưa thể hiện rõ chất lượng | 20/42 |
| Review không liên quan mẫu/size/phiên bản | 16/42 |
| Review mâu thuẫn | 13/42 |
| Khó so sánh sản phẩm/cửa hàng | 13/42 |
| Khó xác định ưu/nhược điểm | 11/42 |
| Quá nhiều review/mất thời gian tổng hợp | 10/42 |

- Thời lượng đọc review ở lần gần nhất: dưới 5 phút 13/42 · 5–<10 phút 11/42 · 10–<20 phút 10/42 · 20–<30 phút 6/42 · 30–<60 phút 1/42 · ≥60 phút 1/42. Trung vị nằm ở nhóm 5–<10 phút; không suy ra tổng thời gian/tháng từ câu tần suất tìm kiếm.

### Phân bố theo ngành hàng (ngành của lần mua sắm gần nhất)

“Có khó khăn” nghĩa là chọn ít nhất một option khó khăn ở câu hỏi nhiều lựa chọn; số nhỏ và mẫu tự chọn, không dùng để xếp hạng ngành.

| Ngành hàng như ghi trong CSV | n đủ điều kiện | Có khó khăn |
|---|---:|---:|
| Mỹ phẩm và chăm sóc cá nhân | 8 | 8 |
| Thời trang và phụ kiện | 12 | 12 |
| Thực phẩm và đồ uống | 4 | 4 |
| Đồ gia dụng và đời sống | 5 | 5 |
| Điện tử và phụ kiện công nghệ | 11 | 10 |
| Sách và văn phòng phẩm | 1 | 1 |
| “Thập câm” (giữ nguyên câu trả lời chưa chuẩn hóa) | 1 | 1 |
| **Tổng** | **42** | **41** |

### Liên hệ với demo ốp điện thoại

- Có **1** câu trả lời mở trong tập đủ điều kiện, thuộc nhóm điện tử/phụ kiện công nghệ, nhắc rõ ốp kính. Đây là một tình huống đơn lẻ, không phải bằng chứng đủ để suy rộng pain của người mua ốp.
- Trích nguyên văn, ẩn danh: “Trước mua thử cái ốp kính, đọc đánh giá thấy cũng được mà mua về sài được mấy tuần cái viền ốp nhựa nó bị bung phải tìm cách dán lại.” — `results.csv`, mã phản hồi `S055`.
- Tình huống này cho thấy review đã đọc không ngăn được một trải nghiệm sản phẩm không như mong đợi; không đủ căn cứ để kết luận review sai biến thể, hàng kém chất lượng nói chung, hoặc tính năng demo sẽ ngăn được sự cố.

## 3. Các nguồn có khớp nhau không

Survey chọn nhiều khó khăn liên quan độ hữu ích, độ tin cậy, mức liên quan và media; câu trả lời về ốp nêu một ví dụ thực tế riêng. Chúng gợi ý vấn đề review đáng nghiên cứu tiếp, nhưng không xác nhận cùng một pain ở mọi ngành hàng hay toàn bộ phân khúc ốp.

## 4. Kết luận tạm thời

Giả thuyết rộng được **ủng hộ bước đầu trong mẫu khảo sát**, không được xác nhận cho toàn bộ người mua Shopee. Demo giữ lát cắt ốp để kiểm tra workflow; cần thêm phản hồi trực tiếp về ốp trước khi nói pain riêng của phân khúc này. Tiếp tục thu đủ trích dẫn ẩn danh và xác minh tính đủ điều kiện trước CP3.
