# Hồ sơ đánh giá — một trang

> Điền ở guide bước 2.4 (mục 1–4, trước CP2) và 4.1 (mục 5–6, trước CP4). Ôn lại: ngày 9, ngày 14 · lab ngày 9. Chấm ở rubric R4, R5.
> Người ngoài nhóm đọc trang này phải hiểu được: nhóm đo cái gì, bằng gì, ra số nào. Trang slide "Đánh giá thế nào" lấy từ đây.

## 1. Dataset → xử lý

`data/reviews.json` có 14 review synthetic trên hai listing fixture, lọc theo đúng listing + dòng máy + biến thể rồi lấy mẫu tối đa 12 theo nhóm sao, seed 42. Không phải review Shopee thật hoặc bằng chứng pain; chưa có media. Chi tiết/giới hạn ở `data/DATA_CARD.md`.

## 2. Bộ câu thử dựng ra sao

- `eval/benchmark.csv`: 10 câu (thuong 2 · kho 6 · tu_choi 2, trong đó 2 câu tấn công)
- Nguồn (checker): nguoi_dung 0 · data_that 0 · tu_viet 10 · sinh_seed 0 → từ người dùng / data thật 0/10 (**chưa đạt ≥1/3; chờ tình huống khảo sát thật**)
- Độ phủ — lưới input: listing có/không trong fixture · dòng máy · biến thể · JSON hợp lệ/không hợp lệ · phản ánh lỗi cụ thể · chỉ dẫn/hostname tấn công.
- Câu `kho` trỏ về 4 lớp chỗ khó (`spec.md` §5): lớp 1: B03 · lớp 2: B04/B08 · lớp 3: B05/B06 · lớp 4: B02/B07/B09.

## 3. Metric và cách chấm

| Metric (`eval/metric_spec.yaml`) | Cách chấm | Ngưỡng |
|---|---|---|
| `dung_bien_the` | code | 100% review được trích dẫn |
| `dan_chung_ton_tai` | code | 100% mã và trích dẫn đúng nguồn |
| `tu_choi_khi_thieu_can_cu` | code | 100% link/biến thể không hợp lệ không khuyến nghị |

- **Người thứ hai chấm thử:** Chưa thực hiện; cần người không viết spec chấm độc lập 5 output và ghi khớp x/5 (cần ≥4/5). Không tự điền kết quả.
- LLM chấm (nếu có): đã kiểm tay __ câu, khớp __/__
- **Chuẩn "đạt"** (bản nháp, chưa khóa): ≥80% câu thử qua, đồng thời 100% câu link/biến thể không hợp lệ không đưa khuyến nghị và 100% dẫn chứng khớp review/biến thể. Chờ nhóm duyệt sau khi có khảo sát và chấm thử.

## 4. Lệnh

`python run.py eval` → `eval/run-N.csv` + `traces/run-N.jsonl` · điền cột `pass` · `python run.py score eval/run-N.csv`

## 5. Đã chạy gì

| Lượt | Run ID | Model | Cấu hình (prompt / công cụ / thay đổi) | Đạt / tổng | % | Đạt chuẩn? |
|---|---|---|---|---|---|---|
| 1 | | | | __/__ | | |
| 2 | | | | __/__ | | |

Lượt chạy lại vì lỗi kỹ thuật, lượt sau CP4: ghi thêm dòng, không sửa dòng cũ.

## 6. Lỗi chính

Tóm 2–3 dòng từ `eval/report.md`: nhóm lỗi lớn nhất · đã sửa gì · còn lại gì.
