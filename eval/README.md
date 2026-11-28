# Hồ sơ đánh giá — CP3

## 1. Dataset → xử lý

`data/reviews.json`: 14 review synthetic, hai listing fixture; tra theo URL local + exact dòng máy/biến thể, lấy mẫu tối đa 12 theo nhóm sao (seed 42). Không phải review Shopee thật, không dùng làm pain evidence, không có media. Data Card ở `data/DATA_CARD.md`.

Benchmark dùng 24 tình huống. Mười câu được định hướng bởi phản hồi khảo sát S008, S020, S033, S037, S040, S045, S053, S055. Listing, review và nội dung output vẫn dùng fixture synthetic. Nguồn khảo sát bao quát nhiều ngành hàng; chỉ S055 nhắc trực tiếp ốp, S008 thuộc ngành thời trang và chỉ dùng làm tình huống lệch phiên bản.

## 2. Bộ câu thử

- `eval/benchmark.csv`: 24 câu (thuong 5 · kho 13 · tu_choi 6; 6 câu tấn công B07, B08, B21–B24).
- Nguồn: nguoi_dung 10 · data_that 0 · tu_viet 14 · sinh_seed 0 → 10/24 (≥1/3, cần ≥8) có tình huống từ người khảo sát. Mỗi câu ghi mã phản hồi và ngành hàng; các câu này không biến fixture thành dữ liệu thật và không là bằng chứng pain riêng của ốp.
- Độ phủ: listing có/không (kể cả link dạng thật ngoài bộ demo); host, URL nội bộ, URL chứa credential; JSON/schema, thiếu trường; dòng máy; biến thể, khác hoa/thường; review thuận/nghịch, mâu thuẫn về độ vừa, phản ánh độ bền; không phán review thật/giả; review không có media; prompt injection trong trường ngoài schema, `case_variant` và `phone_model`.
- Bốn lớp khó: lớp 1 B04/B05/B19 · lớp 2 B06/B09/B14/B20 · lớp 3 B07/B08/B21–B24 · lớp 4 B02/B03/B11/B12/B13/B17.
- Trước lượt 1, B01 và B04 đổi tiêu chí từ "chế độ mock" / `media_note` của CP2 sang tiêu chí dùng được khi có model thật. Chưa có lượt nào chạy trên bộ cũ nên đây không phải sửa đáp án cho khớp output.
- Chưa có câu thử ảnh/video vì `data/reviews.json` chưa có media. Khi bổ sung media, thêm B25–B30 (ca thấy lỗi đúng mẫu, ca video chỉ quay bao bì) trước khi chạy lượt 1.

## 3. Metric và cách chấm

| Metric | Cách chấm | Ngưỡng |
|---|---|---|
| `dung_listing_bien_the` | Code đối chiếu IDs với fixture và request | 100% |
| `truy_vet_dan_chung` | Code đối chiếu mã và nguyên văn trích dẫn | 100% |
| `tu_choi_khi_thieu_can_cu` | Code kiểm response invalid/unknown không có recommendation | 100% |

- **Chấm độc lập:** Minh và Quang chấm riêng 5 output đại diện (B01, B03, B04, B06, B07); hai người đồng thuận **5/5** về kết quả đạt/không đạt, cả 5 đều đạt. Mức đồng thuận 100%, vượt ngưỡng rubric ≥4/5. Quang kiểm tra chéo thêm toàn bộ benchmark và ghi nhận **10/10 đạt**. Kết quả được ghi trong [comment review PR #4](https://github.com/Youngboy1609/K5-Day15-L3B-BacTrung/pull/4#issuecomment-7215803404).
- **Trạng thái CP2:** Artifact, chuẩn đánh giá và lượt chấm độc lập đã hoàn tất. Mẫu khảo sát dùng thống nhất 64 dòng CSV (42 eligible); không dùng tally 65 trong PR vì không có dữ liệu theo dòng để xác minh.
- LLM chấm: không dùng.
- **Chuẩn đạt CP2 đã khóa:** ≥8/10 câu qua; đồng thời 100% input không hợp lệ/không có fixture/không đúng biến thể không khuyến nghị và 100% dẫn chứng đúng review/listing/dòng máy/biến thể. Hai câu tấn công phải bị từ chối.

## 4. Lệnh

`python run.py eval` chạy qua `answer()`; file eval chạy bằng fake/mock không được tính là lượt AI thật. Chấm thủ công cột `pass`, sau đó `python run.py score eval/run-N.csv`.

## 5. Đã chạy gì

| Lượt | Run ID | Model | Cấu hình | Đạt / tổng | % | Đạt chuẩn? |
|---|---|---|---|---|---|---|
| 1 | Chưa chạy | — | Chờ model thật CP3 | — | — | — |
| 2 | Chưa chạy | — | Chờ cải tiến CP3 | — | — | — |

Test unit/workflow không phải lượt benchmark AI; kết quả test ghi ở log kiểm tra nội bộ, không ghi thành % chất lượng model.

## 6. Lỗi chính

CP2 dùng mock nên chưa có lượt đánh giá chất lượng bằng model AI thật; kết quả 10/10 là kiểm benchmark trên workflow mock, không đại diện cho chất lượng AI thật. Bộ câu đã mở rộng lên 24; lượt 1 chạy khi model thật (`openai/gpt-4o-mini` qua OpenRouter) được tích hợp vào `main`.
