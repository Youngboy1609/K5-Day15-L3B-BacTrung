# Tóm tắt mô phỏng simulate-1@20261128-141638

Do `python run.py simulate` sinh ra — không sửa tay. Chép bảng sang `cost/cost-estimate.md`.

| Persona | Số phiên mô phỏng | Lượt hỏi / phiên | Token vào / phiên | Token ra / phiên | Gọi model / phiên | Gọi công cụ / phiên |
|---|---:|---:|---:|---:|---:|---:|
| mua_sam_it | 14 | 1 | 343 | 121 | 0.5 | 0.9 |
| mua_sam_vua | 18 | 1 | 481 | 188 | 0.6 | 0.8 |
| mua_sam_thuong_xuyen | 18 | 2 | 1310 | 473 | 1.6 | 1.8 |

Tỉ lệ đạt dùng để tính: 24/24 (100%) — lượt run-2@20261128-141058

- Tỉ lệ đạt lấy từ lượt nhóm chọn: eval/run-2.csv (--rate-from).

| Model (giá) | Chi phí / phiên | Chi phí / task thành công | Chi phí / câu hỏi đạt | Chi phí / tháng — thấp (30 người) | Chi phí / tháng — cơ sở (100 người) | Chi phí / tháng — cao (300 người) | Chi phí / người / tháng (cơ sở) |
|---|---:|---:|---:|---:|---:|---:|---:|
| openai/gpt-4o-mini (vào 0.15 · ra 0.6 $/1M) | $0.00027 | $0.00027 | $0.00020 | $0.0269 | $0.0896 | $0.2689 | $0.00090 |
| gpt-4o (vào 2.5 · ra 10.0 $/1M) | $0.0046 | $0.0046 | $0.0034 | $0.4482 | $1.49 | $4.48 | $0.0149 |
| gemini-3.1-flash-lite (vào 0.25 · ra 1.5 $/1M) | $0.00059 | $0.00059 | $0.00044 | $0.0581 | $0.1937 | $0.5812 | $0.0019 |

- Chi phí / task thành công = chi phí / phiên ÷ tỉ lệ đạt. Chi phí / câu hỏi đạt = chi phí / phiên ÷ số lượt hỏi trung bình mỗi phiên (1.4) ÷ tỉ lệ đạt — tỉ lệ đạt đo theo từng câu thử.
- Token đo trên model: gpt-4o. Giá tính theo từng model trong bảng — model khác bộ tách token thì số token thật có thể lệch; ghi rõ "đo trên model X, tính giá model Y" trong cost/cost-estimate.md.
- Phiên lỗi (không tính vào trung bình): 0/50.
