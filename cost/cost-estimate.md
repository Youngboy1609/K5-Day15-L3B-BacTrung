# Chi phí khi dùng thật

> Điền ở guide bước 4.2, nộp ở CP4 14:30 Thứ Bảy 28/11. Ôn lại: ngày 13, ngày 1, ngày 14 · lab ngày 13, lab ngày 14. Chấm ở rubric R6.
> Số **không điền tay**: điền `cost/personas.yaml` → `python run.py simulate` → chép bảng trong `cost/simulate-N-summary.md` vào đây.
> Lúc build dùng gói miễn phí vẫn tính theo **giá gói trả phí** — đây là chi phí cho lúc đưa vào dùng thật.

## 1. Đầu vào

- **Persona** (`cost/personas.yaml`): 3 kiểu — `mua_sam_it` 26,2% (1 phiên/tháng, 1 lượt/phiên) · `mua_sam_vua` 35,7% (2 phiên, 1 lượt) · `mua_sam_thuong_xuyen` 38,1% (4 phiên, 2 lượt). Nguồn: tỷ trọng chia theo Q3 (số lần cân nhắc mua trong 30 ngày) của 42 phản hồi hợp lệ trong `evidence/survey/results.csv` (11/15/16 người); số phiên và số lượt mỗi phiên *(tự ước tính)*.
- **Số người dùng thật** 3 kịch bản: thấp 30 · cơ sở 100 · cao 300 người/tháng. Nguồn: *(tự ước tính)* cho đợt dùng thử ốp điện thoại, chưa có kênh tuyển người dùng xác nhận.
- **Giá** (USD / 1 triệu token, Standard, đầu vào không cache): GPT-4o **2,50 vào / 10,00 ra** (model demo) · `openai/gpt-4o-mini` qua OpenRouter **0,15 vào / 0,60 ra** (mức rẻ để so sánh; OpenAI đã đánh dấu model này là Deprecated) · Gemini 3.1 Flash-Lite **0,25 vào / 1,50 ra** (mức tham chiếu). Nguồn và ngày xem ghi trong `cost/personas.yaml`.
- **Tỉ lệ đạt** dùng để tính: __/__ (__%) — lượt `run-__` (lượt 2)
- Model demo dùng để đo token: `gpt-4o` (OpenAI), đúng model của lượt eval 1 `run-1@20261128-094539`. Lượt 2 và lượt mô phỏng phải chạy cùng `gpt-4o` thì `simulate` mới lấy được tỉ lệ đạt. Tính chi phí chính theo giá GPT-4o, so sánh với gpt-4o-mini và Gemini 3.1 Flash-Lite trên cùng số token đo được. Model khác dùng bộ tách token khác, nên số so sánh chỉ là gần đúng.

## 2. Kết quả mô phỏng

Lượt mô phỏng: `cost/simulate-__.csv` · run ID __ · __ phiên · seed __

*(dán bảng từ `cost/simulate-N-summary.md`)*

| Model | Chi phí / phiên | Chi phí / task thành công | / tháng — thấp | / tháng — cơ sở | / tháng — cao | / người / tháng (cơ sở) |
|---|---|---|---|---|---|---|
| | | | | | | |
| | | | | | | |

Chi phí / task thành công = chi phí trung bình mỗi phiên ÷ tỉ lệ đạt — **không coi như đạt 100%**.

## 3. So với impact

- Impact / người / tháng (`spec.md` §2): __
- Chi phí / người / tháng (cơ sở, model __): __
- **Kết luận một dòng — đáng làm không:** __

## 4. *(Muốn sâu hơn, không bắt buộc)*

- Bảng độ nhạy: model rẻ hơn · cache · cắt ngữ cảnh · giới hạn bước — mỗi cần gạt đổi chi phí bao nhiêu
- Chi phí ngoài model: hosting, lưu trữ, giờ công người duyệt
- Quy mô nào thì bài toán còn đáng làm
