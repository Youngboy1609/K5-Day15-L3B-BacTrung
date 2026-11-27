# Data card — CP2 review fixture

> **Draft:** dùng cho prototype mock, không phải bằng chứng pain và không phải review thật từ Shopee. Nhóm cần duyệt nội dung synthetic trước khi demo.

## Dataset 1 · Local phone-case review fixtures

| | |
|---|---|
| Dùng để làm gì | Chạy tool tra listing/biến thể và prototype CP2; tạo đầu vào cho benchmark kỹ thuật |
| Từ đâu | `data/reviews.json`; dữ liệu synthetic do coding assistant soạn từ mô tả sản phẩm của nhóm |
| Xử lý những bước gì | Metadata listing giả; phân tách theo `product_id`, `phone_model`, `case_variant`; tool lọc exact match; lấy mẫu tối đa 12 review theo nhóm sao, seed mặc định 42 |
| Số dòng / số đoạn | 14 review synthetic trên 2 listing; 11 review thuộc đúng biến thể demo tương ứng; các review còn lại dùng kiểm tra không trộn biến thể |
| Phiên bản / ngày lấy | `cp2-fixture-1`; tạo trong quá trình chuẩn bị CP2 |
| Nhãn | `synthetic` |
| Giới hạn | Không lấy từ Shopee, không đại diện cho người mua thật; chưa được thành viên xác minh; không có ảnh/MP4; câu chữ dựng để kiểm tra workflow, không dùng làm pain evidence hoặc trích dẫn khảo sát |

**Cách sinh/kiểm:** nội dung được viết thủ công bởi coding assistant từ lát cắt đã thống nhất; không dùng random seed để sinh văn bản. Seed `42` chỉ điều khiển việc lấy mẫu review khi số review vượt giới hạn. Số review được người trong nhóm kiểm tay: **chưa kiểm, cần Minh xác nhận trước khi dùng demo**.

**Media:** mọi `media` hiện là danh sách rỗng. CP2 mock không đọc ảnh/video và không được hiển thị như đã kiểm media. Khi thêm dữ liệu ở CP3, tạo mục Data Card riêng, ghi nguồn/quyền sử dụng hoặc cách dựng, frame timestamps, xử lý/ẩn danh và người kiểm.

## Dataset 2 · Pain evidence

Chưa có dữ liệu khảo sát. Nhật phụ trách thu phản hồi ngoài nhóm và lưu bản đã ẩn danh trong `evidence/survey/`; khảo sát thật tách riêng khỏi review fixture synthetic.
