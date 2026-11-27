# Hồ sơ đánh giá — CP2

## 1. Dataset → xử lý

`data/reviews.json`: 14 review synthetic, hai listing fixture; tra theo URL local + exact dòng máy/biến thể, lấy mẫu tối đa 12 theo nhóm sao (seed 42). Không phải review Shopee thật, không dùng làm pain evidence, không có media. Data Card ở `data/DATA_CARD.md`.

Benchmark dùng 10 tình huống. Bốn được định hướng bởi survey rows 20, 37 và 55; listing, review và nội dung output vẫn dùng fixture synthetic. Nguồn survey bao quát nhiều ngành hàng, chỉ một trích dẫn có nhắc trực tiếp ốp.

## 2. Bộ câu thử

- `eval/benchmark.csv`: 10 câu (thuong 2 · kho 6 · tu_choi 2; 2 câu tấn công).
- Nguồn: nguoi_dung 4 · data_that 0 · tu_viet 6 · sinh_seed 0 → 4/10 (≥1/3) có tình huống từ người khảo sát. Các câu này không biến fixture thành dữ liệu thật.
- Độ phủ: listing có/không; host; JSON/schema; dòng máy; biến thể; review thuận/nghịch; media không có.
- Bốn lớp khó: lớp 1 B05 · lớp 2 B06/B09 · lớp 3 B07/B08 · lớp 4 B02/B03/B04.

## 3. Metric và cách chấm

| Metric | Cách chấm | Ngưỡng |
|---|---|---|
| `dung_listing_bien_the` | Code đối chiếu IDs với fixture và request | 100% |
| `truy_vet_dan_chung` | Code đối chiếu mã và nguyên văn trích dẫn | 100% |
| `tu_choi_khi_thieu_can_cu` | Code kiểm response invalid/unknown không có recommendation | 100% |

- **Người thứ hai chấm thử:** Chưa thực hiện. Nghĩa/Minh cần chọn 5 output và chấm độc lập; ghi khớp thực tế x/5 (rubric yêu cầu ≥4/5), không điền trước kết quả.
- **Trạng thái CP2:** Artifact và chuẩn đánh giá đã chốt; mẫu khảo sát dùng thống nhất 64 dòng CSV (42 eligible), không dùng con số 65 trong PR vì không có dữ liệu theo dòng để xác minh. Chỉ còn lượt chấm độc lập 5 output; chưa ghi kết quả hoặc tuyên bố sign-off trước khi người chấm thực hiện.
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

Chưa có lượt model thật nên chưa có lỗi eval hay tỷ lệ đạt. Cần người thứ hai kiểm 5 output và cập nhật 20–30 câu trước CP3.
