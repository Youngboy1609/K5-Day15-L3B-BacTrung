# Tóm tắt mô phỏng simulate-1@20261128-104717

Do `python run.py simulate` sinh ra — không sửa tay. Chép bảng sang `cost/cost-estimate.md`.

| Persona | Số phiên mô phỏng | Lượt hỏi / phiên | Token vào / phiên | Token ra / phiên | Gọi model / phiên | Gọi công cụ / phiên |
|---|---:|---:|---:|---:|---:|---:|
| mua_sam_it | 14 | 1 | 2189 | 89 | 0.5 | 0.9 |
| mua_sam_vua | 18 | 1 | 3317 | 138 | 0.6 | 0.8 |
| mua_sam_thuong_xuyen | 18 | 2 | 8361 | 344 | 1.6 | 1.8 |

Tỉ lệ đạt dùng để tính: 24/24 (100%) — lượt run-2@20261128-104603

- Tỉ lệ đạt lấy từ lượt nhóm chọn: eval/run-2.csv (--rate-from).

| Model (giá) | Chi phí / phiên | Chi phí / task thành công | Chi phí / câu hỏi đạt | Chi phí / tháng — thấp (30 người) | Chi phí / tháng — cơ sở (100 người) | Chi phí / tháng — cao (300 người) | Chi phí / người / tháng (cơ sở) |
|---|---:|---:|---:|---:|---:|---:|---:|
| openai/gpt-4o-mini (vào 0.15 · ra 0.6 $/1M) | $0.00084 | $0.00084 | $0.00062 | $0.0822 | $0.2740 | $0.8221 | $0.0027 |
| gpt-4o (vào 2.5 · ra 10.0 $/1M) | $0.0140 | $0.0140 | $0.0103 | $1.37 | $4.57 | $13.70 | $0.0457 |
| gemini-3.1-flash-lite (vào 0.25 · ra 1.5 $/1M) | $0.0015 | $0.0015 | $0.0011 | $0.1467 | $0.4890 | $1.47 | $0.0049 |

- Chi phí / task thành công = chi phí / phiên ÷ tỉ lệ đạt. Chi phí / câu hỏi đạt = chi phí / phiên ÷ số lượt hỏi trung bình mỗi phiên (1.4) ÷ tỉ lệ đạt — tỉ lệ đạt đo theo từng câu thử.
- Token đo trên model: openai/gpt-4o-mini. Giá tính theo từng model trong bảng — model khác bộ tách token thì số token thật có thể lệch; ghi rõ "đo trên model X, tính giá model Y" trong cost/cost-estimate.md.
- Phiên lỗi (không tính vào trung bình): 0/50.
