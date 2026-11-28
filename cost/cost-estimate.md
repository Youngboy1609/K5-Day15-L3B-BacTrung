# Chi phí khi dùng thật

> Điền ở guide bước 4.2, nộp ở CP4 14:30 Thứ Bảy 28/11. Ôn lại: ngày 13, ngày 1, ngày 14 · lab ngày 13, lab ngày 14. Chấm ở rubric R6.
> Số **không điền tay**: điền `cost/personas.yaml` → `python run.py simulate` → chép bảng trong `cost/simulate-N-summary.md` vào đây.
> Lúc build dùng gói miễn phí vẫn tính theo **giá gói trả phí** — đây là chi phí cho lúc đưa vào dùng thật.

## 1. Đầu vào

- **Persona** (`cost/personas.yaml`): 3 kiểu chia theo Q3 của 42 phản hồi hợp lệ trong `evidence/survey/results.csv` (`mua_sam_it` 26,2% · 1 phiên/tháng · 1 lượt; `mua_sam_vua` 35,7% · 2 phiên/tháng · 1 lượt; `mua_sam_thuong_xuyen` 38,1% · 4 phiên/tháng · 2 lượt). Tần suất dùng app và số lượt/phiên *(tự ước tính)*.
- **Số người dùng thật** 3 kịch bản: thấp `30` · cơ sở `100` · cao `300`. Nguồn: *(tự ước tính)* quy mô đợt dùng thử ốp điện thoại.
- **Giá** (USD / 1 triệu token, Standard, đầu vào không cache): `openai/gpt-4o-mini` qua OpenRouter **0,15 vào / 0,60 ra** (model demo) · `gpt-4o` **2,50 vào / 10,00 ra** (mức mạnh hơn) · `gemini-3.1-flash-lite` **0,25 vào / 1,50 ra** (mức tham chiếu). Nguồn và ngày xem ghi trong `cost/personas.yaml`.
- **Tỉ lệ đạt** dùng để tính là **24/24 (100%)** trên benchmark lượt `run-2@20261128-104603` (`eval/run-2.csv`, `openai/gpt-4o-mini`). Cách chấm tính cả từ chối đúng và các ca ngoài bộ dữ liệu.
- Đo token trên model `openai/gpt-4o-mini` (OpenRouter), tính giá cho cả `openai/gpt-4o-mini`, `gpt-4o` và `gemini-3.1-flash-lite` trên cùng số token đo được *(lưu ý: model khác bộ tách token thì số token thực tế có thể lệch)*.

## 2. Kết quả mô phỏng

Lượt `simulate-1@20261128-104717` chạy **50 phiên** với seed `42`. Cột `error` trong `cost/simulate-1.csv` trống ở cả 50 phiên. Có **35 phiên gọi model** và **15 phiên không gọi model**. Bảng do khung sinh nằm ở `cost/simulate-1-summary.md`.

| Persona | Số phiên mô phỏng | Lượt hỏi / phiên | Token vào / phiên | Token ra / phiên | Gọi model / phiên | Gọi công cụ / phiên |
|---|---:|---:|---:|---:|---:|---:|
| `mua_sam_it` | 14 | 1 | 2189 | 89 | 0.5 | 0.9 |
| `mua_sam_vua` | 18 | 1 | 3317 | 138 | 0.6 | 0.8 |
| `mua_sam_thuong_xuyen` | 18 | 2 | 8361 | 344 | 1.6 | 1.8 |

| Model (giá) | Chi phí / phiên mô phỏng | Ước tính chi phí / task đạt benchmark | Ước tính chi phí / câu hỏi đạt | Chi phí / tháng — thấp (30 người) | Chi phí / tháng — cơ sở (100 người) | Chi phí / tháng — cao (300 người) | Chi phí / người / tháng (cơ sở) |
|---|---:|---:|---:|---:|---:|---:|---:|
| `openai/gpt-4o-mini` (vào 0.15 · ra 0.6 $/1M) | $0.00084 | $0.00084 | $0.00062 | $0.0822 | $0.2740 | $0.8221 | $0.0027 |
| `gpt-4o` (vào 2.5 · ra 10.0 $/1M) | $0.0140 | $0.0140 | $0.0103 | $1.37 | $4.57 | $13.70 | $0.0457 |
| `gemini-3.1-flash-lite` (vào 0.25 · ra 1.5 $/1M) | $0.0015 | $0.0015 | $0.0011 | $0.1467 | $0.4890 | $1.47 | $0.0049 |

**Mẫu số.** Chi phí mỗi phiên là tổng chi phí API chia cho **50 phiên**, kể cả 15 phiên không gọi model. Khung ước tính chi phí mỗi task đạt bằng cách chia chi phí mỗi phiên cho tỉ lệ đạt **theo câu benchmark** (`24/24`). Vì vậy hai cột trùng số ở lượt này. Đây là ước tính theo tiêu chí benchmark, bao gồm từ chối đúng. Riêng **35 phiên có gọi model** có chi phí API bình quân **$0.00120/phiên** với GPT-4o-mini (`$0.0420822 ÷ 35`). Các mức theo tháng dùng cơ cấu phiên mô phỏng và tần suất sử dụng ước tính theo persona.

## 3. So với impact

- Impact / người / tháng (`spec.md` §2): Trung vị thời lượng đọc review ở lần gần nhất là **5 đến dưới 10 phút** (11/42 chọn nhóm này; 13/42 < 5 phút); chưa nhân với tần suất tìm kiếm 30 ngày vì hai câu hỏi đo hai việc khác nhau.
- Chi phí / người / tháng (cơ sở, model `openai/gpt-4o-mini`): **$0.0027** (~$0.2740/tháng cho 100 người; $0.8221/tháng ở kịch bản cao 300 người). Ngay cả khi dùng `gpt-4o`, chi phí cơ sở là **$0.0457**/người/tháng ($4.57/tháng cho 100 người).
- **Kết luận:** Chi phí API ước tính cho thử nghiệm với GPT-4o-mini là **$0.2740/tháng cho 100 người** theo cơ cấu phiên đã mô phỏng. Khi thử với người dùng, cần đo thời gian thực tế họ tiết kiệm được khi đọc review Shopee.

## 4. *(Muốn sâu hơn, không bắt buộc)*

- Bảng độ nhạy: model rẻ hơn · cache · cắt ngữ cảnh · giới hạn bước — mỗi cần gạt đổi chi phí bao nhiêu
- Chi phí ngoài model: hosting, lưu trữ, giờ công người duyệt
- Quy mô nào thì bài toán còn đáng làm

## 5. Đối chứng bằng token đo trên GPT‑4o

[Mô phỏng đối chứng](../evidence/cp4-gpt-4o/README.md) đo token trực tiếp trên `gpt-4o`: **$0.0046/task đạt benchmark**, và **$0.4482 / $1.49 / $4.48 mỗi tháng** cho 30 / 100 / 300 người dùng. Đây là lượt đo riêng; hàng giá GPT‑4o ở §2 áp giá GPT‑4o lên token đo bằng GPT‑4o-mini.
