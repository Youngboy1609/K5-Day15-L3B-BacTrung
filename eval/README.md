# Hồ sơ đánh giá — CP3

## 1. Dataset → xử lý

`data/reviews.json`: 14 review synthetic, hai listing fixture; tra theo URL local + exact dòng máy/biến thể, giới hạn tối đa 100 review ở pipeline hiện tại. Không phải review Shopee thật và không dùng làm pain evidence. Fixture có ảnh synthetic và một frame tĩnh từ video synthetic; chi tiết ở `data/DATA_CARD.md`.

Benchmark dùng 24 tình huống. Mười câu được định hướng bởi phản hồi khảo sát S008, S020, S033, S037, S040, S045, S053, S055. Listing, review và nội dung output vẫn dùng fixture synthetic. Nguồn khảo sát bao quát nhiều ngành hàng; chỉ S055 nhắc trực tiếp ốp, S008 thuộc ngành thời trang và chỉ dùng làm tình huống lệch phiên bản.

## 2. Bộ câu thử

- `eval/benchmark.csv`: 24 câu (thuong 5 · kho 13 · tu_choi 6; 6 câu tấn công B07, B08, B21–B24).
- Nguồn: nguoi_dung 10 · data_that 0 · tu_viet 14 · sinh_seed 0 → 10/24 (≥1/3, cần ≥8) có tình huống từ người khảo sát. Mỗi câu ghi mã phản hồi và ngành hàng; các câu này không biến fixture thành dữ liệu thật và không là bằng chứng pain riêng của ốp.
- Độ phủ: listing có/không (kể cả link dạng thật ngoài bộ demo); host, URL nội bộ, URL chứa credential; JSON/schema, thiếu trường; dòng máy; biến thể, khác hoa/thường; review thuận/nghịch, mâu thuẫn về độ vừa, phản ánh độ bền; không phán review thật/giả; review không có media; prompt injection trong trường ngoài schema, `case_variant` và `phone_model`.
- Bốn lớp khó: lớp 1 B04/B05/B19 · lớp 2 B06/B09/B14/B20 · lớp 3 B07/B08/B21–B24 · lớp 4 B02/B03/B11/B12/B13/B17.
- Trước lượt 1, B01 và B04 đổi tiêu chí từ "chế độ mock" / `media_note` của CP2 sang tiêu chí dùng được khi có model thật. Chưa có lượt nào chạy trên bộ cũ nên đây không phải sửa đáp án cho khớp output.
- Fixture CP3 có ảnh và một frame video synthetic; B01–B03/B15–B18 chạy trên listing có media, còn B04 kiểm tra listing không có media. Frame chỉ là ảnh tĩnh, không dùng để suy luận chuyển động hoặc âm thanh.

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
| 1 | `run-1@20261128-094539` | `gpt-4o` (OpenAI) | Benchmark 24 câu; fixture local synthetic; gọi model thật | 23/24 | 96% | Đạt theo chuẩn khóa; xem lỗi B10 |
| 2 | Chưa chạy | — | Chờ cải tiến CP3 | — | — | — |

Kết quả và trace: `eval/run-1.csv`, `traces/run-1.jsonl`. B10 là câu duy nhất không đạt: output cuối `ANALYSIS_UNAVAILABLE` thay vì status `ok`; không có khuyến nghị sai. Các câu từ chối đạt 6/6, câu khó đạt 13/13, câu thường đạt 4/5. Test unit/workflow không tính vào % benchmark AI.

## 6. Lỗi chính

CP2 dùng mock nên kết quả 10/10 khi đó không đại diện cho chất lượng AI thật. CP3 đã chạy lượt 1 bằng GPT‑4o trên 24 tình huống; kết quả 23/24. B10 trả `ANALYSIS_UNAVAILABLE`, cần điều tra trước lượt 2. Đây là benchmark trên fixture synthetic, không chứng minh chất lượng trên review Shopee thật.
