# Tổng hợp bằng chứng pain — CP3

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

### Trích dẫn nguyên văn đã ẩn danh

Sáu câu trả lời mở dưới đây lấy từ `evidence/survey/results.csv`. Ngành hàng ghi theo lần mua sắm gần nhất trong khảo sát.

| Mã phản hồi | Ngành hàng | Trích dẫn nguyên văn | Điều trích dẫn cho thấy |
|---|---|---|---|
| `S055` | Điện tử và phụ kiện công nghệ | “Trước mua thử cái ốp kính, đọc đánh giá thấy cũng được mà mua về sài được mấy tuần cái viền ốp nhựa nó bị bung phải tìm cách dán lại.” | Viền ốp bung sau vài tuần dù đánh giá đọc trước khi mua có vẻ ổn. |
| `S026` | Thời trang và phụ kiện | “Mình tìm hiểu về quần áo nhưng mà size của shop khá mơ hồ và hình ảnh thực tế không phản ánh đúng chất lượng sản phẩm nên mình đã dừng mua” | Thông tin size mơ hồ và hình ảnh thiếu thuyết phục khiến người mua dừng mua. |
| `S037` | Điện tử và phụ kiện công nghệ | “Mình muốn mua một bàn phím cơ thì khi tìm kiếm trên shoppe, sàn trả về quá nhiều sản phẩm khiến mình không biết nên chọn mẫu nào. Mình nhắn hỏi bạn mình thì được tư vấn vài sản phẩm rồi từ đó mình đọc thông tin và đánh giá của chúng. Sau khi chọn được thì mình đặt mua và nhận về sản phẩm như mình kỳ vọng.” | Người mua nhờ bạn bè thu hẹp lựa chọn, sau đó đọc thông tin và đánh giá để chốt mẫu. |
| `S057` | Điện tử và phụ kiện công nghệ | “Mình đã giành thời gian tham khảo để mua một chiếc màn hình máy tính. Việc mình quan tâm là độ uy tín và dịch vụ hậu mãi của cửa hàng. Mình đã dành nhiều thời gian để chọn mẫu, sau đó lại tiếp tục chọn của hàng để mua. Sau khi tham khảo ý kiến từ bạn bè và các đánh giá trên mạng thì mình đã chọn được của hàng phù hợp với bản thân.” | Người mua dành thời gian chọn cả mẫu lẫn cửa hàng, rồi kết hợp ý kiến bạn bè với đánh giá trên mạng. |
| `S058` | Thời trang và phụ kiện | “Mình mua đồ theo đánh giác trên shoppe nhưng mua về thì không đúng như mô tả thành ra phải mất thời gian để trả hàng và tìm lại sản phẩm khác” | Hàng nhận được khác mô tả, khiến người mua mất thời gian trả hàng và tìm sản phẩm khác. |
| `S050` | Thời trang và phụ kiện | “Không có trải nghiệm đáng nhớ, vì truớc khi mua đã tìm hiểu uy tín cửa hàng qua đánh giá.” | Người trả lời dùng đánh giá để tìm hiểu uy tín cửa hàng và không kể sự cố cụ thể. |

## 4. Kết luận nghiên cứu CP3

Giả thuyết rộng được **ủng hộ bước đầu trong mẫu khảo sát**, không được xác nhận cho toàn bộ người mua Shopee. Demo giữ lát cắt ốp để kiểm tra workflow; cần thêm phản hồi trực tiếp về ốp trước khi nói pain riêng của phân khúc này. Cần xác minh điều kiện người ngoài nhóm trước CP3.

## 5. Kiểm tra khả năng tái lập

### Lệnh kiểm tra

```bash
python -m py_compile evidence/survey/analyze_results.py
python -B evidence/survey/analyze_results.py
python -B -m unittest discover -s tests -p "test_survey_analysis.py" -v
```

### Kết quả kiểm tra

| Hạng mục                            | Kết quả    |
| ----------------------------------- | ---------- |
| Kiểm tra cú pháp Python             | PASS       |
| Tổng số phản hồi                    | 64         |
| Số phản hồi khớp bộ lọc             | 42         |
| Số phản hồi gặp khó khăn            | 41         |
| Số trích dẫn nguyên văn đã ẩn danh  | 6          |
| Kiểm tra tính nhất quán số liệu CP2 | PASS       |
| Kiểm tra mã phản hồi ẩn danh        | PASS       |
| Tổng số Unit Test                   | 2          |
| Số test thành công                  | 2/2        |
| Số test thất bại                    | 0          |
| Thời gian chạy Unit Test            | 0,004 giây |

Sau khi hiệu chỉnh điều kiện lọc, kết quả thống kê vẫn nhất quán với snapshot CP2. Hai Unit Test đều thành công, xác nhận khả năng tái lập các số liệu được kiểm tra và cấu trúc mã phản hồi ẩn danh của dữ liệu khảo sát.
