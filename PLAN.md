# Kế hoạch Hackathon — BacTrung · L3B · Track D

**Bài toán:** Khi chọn mua ốp lưng trên Shopee, người mua mất thời gian đọc review và khó biết nhận xét nào áp dụng cho đúng dòng máy và mẫu ốp mình định mua. Đây là giả thuyết nhóm sẽ kiểm qua khảo sát.

**Lát cắt:** Người mua dán link Shopee và chọn biến thể ốp; AI đánh giá review nào cung cấp bằng chứng cho biến thể đó; app trả khuyến nghị mua kèm dẫn chứng và một lời khuyên cụ thể.

**Phạm vi demo:** Hai link Shopee, gồm một ca thông thường và một ca dễ lẫn biến thể. App tra dữ liệu cục bộ đã chuẩn bị, không gọi Shopee lúc demo. Từ CP3, model thật phân tích chữ, ảnh và các khung hình trích sẵn từ MP4. Phần audio và tải file từ người dùng nằm ngoài phạm vi.

## Phân công

| Thành viên | Đầu việc | File phụ trách |
|---|---|---|
| **Hồ Trọng Nghĩa — đội trưởng** | Canvas, spec, UI/UX, tích hợp, slide và nộp bài | `TEAMS.md`, `canvas.md`, `spec.md`, `codebase/app.py`, `demo-slides.pdf` |
| **Nguyễn Đức Nhật** | Khảo sát, tổng hợp bằng chứng và mô phỏng chi phí | `evidence/`, `cost/personas.yaml`, `cost/cost-estimate.md` |
| **Nguyễn Cao Minh** | Dữ liệu review mẫu, công cụ tra cứu/lấy mẫu, benchmark và hai lượt đánh giá | `data/`, `codebase/tools.py`, `eval/benchmark.csv`, `eval/metric_spec.yaml`, `eval/README.md`, `eval/report.md` |
| **Phạm Đăng Quang** | Workflow, tích hợp model đa phương thức, tổng hợp khuyến nghị và quay demo | `codebase/agent.py`, `codebase/ai.py`, video CP3 và video dự phòng |

Mỗi người làm trên nhánh riêng, chỉ sửa file mình phụ trách; Nghĩa gom vào `main`. **Minh ghi các lượt eval chính thức, Nhật ghi các lượt mô phỏng chính thức.** Dùng lệnh và khung sẵn có trong `run.py`, `codebase/tracing.py`, `eval/run_eval.py` và `cost/simulate.py`.

## Việc phải xong theo mốc

### CP1 — 17:00 Thứ Sáu 27/11

- [ ] **Nghĩa:** Nộp Form 1 trước **16:30**. Điền Canvas 7 dòng và phân công; mô tả vấn đề trong 1–2 câu không dùng chữ AI, tách khỏi câu lát cắt. Phác một màn hình: nhập link → chọn biến thể → phân tích → xem kết quả. Kiểm repo public bằng tab ẩn danh rồi nộp Form 2 → CP1.
- [ ] **Nhật:** Ghi giả thuyết và phát form cho người ngoài nhóm từng cân nhắc hoặc mua ốp trên Shopee. Hỏi về lần gần nhất: đọc gì, mất bao lâu, có gặp review lẫn biến thể không và họ xử lý ra sao. Có câu mở để lấy tình huống và trích dẫn thật.
- [ ] **Minh:** Tạo vài review mẫu theo định dạng bên dưới: đúng mẫu, sai mẫu, ảnh bao bì và không có ảnh. Chọn hai link demo.
- [ ] **Quang:** Dựng luồng bằng dữ liệu giả nhỏ và phản hồi mock. Bắt đầu từ JSON mẫu trong file này, không cần chờ khảo sát hoặc toàn bộ dữ liệu review.

### CP2 — 19:30 Thứ Sáu 27/11

- [ ] **Nghĩa:** Dựng UI mock; cập nhật Canvas với số liệu bước đầu và ghi thay đổi so với CP1. Viết sơ đồ `spec.md` §4, nêu rõ dữ liệu đầu vào, phần AI quyết định và chỗ chặn rủi ro. Chốt **chuẩn đạt bằng số** trong §7 rồi nộp CP2.
- [ ] **Nhật:** Đăng tiến độ khảo sát, số phản hồi hợp lệ và một trích dẫn ẩn danh nếu đã có. Chuyển dần các tình huống cụ thể theo mã phản hồi để Minh viết câu thử.
- [ ] **Minh:** Hoàn thiện bộ review mẫu, tra đúng sản phẩm/biến thể, lấy mẫu theo sao và ghi `data/DATA_CARD.md`. Soạn **≥10 câu thử**, **≥3 metric đo được** và cách chấm. Cùng Nghĩa chấm độc lập 5 đầu ra, cần khớp **≥4/5** theo rubric; ghi kết quả vào `eval/README.md`.
- [ ] **Quang:** Cho `python run.py` chạy hết luồng với AI giả: nhập link và biến thể → tra review mẫu → chấm giả → trả khuyến nghị có dẫn chứng. Xử lý riêng link ngoài bộ demo và trường hợp thiếu căn cứ.

Khóa `spec.md` §7 và `eval/metric_spec.yaml` sau CP2. **Chuẩn đạt của bài** là tỷ lệ câu thử qua và điều kiện bắt buộc; **ngưỡng khuyến nghị mua** là quy tắc của app. Ghi riêng hai phần.

### CP3 — 10:00 Thứ Bảy 28/11

- [ ] **Nhật:** Chốt **≥20 phản hồi hợp lệ** và **≥5 trích dẫn nguyên văn đã ẩn danh**. Lưu câu hỏi, kết quả đã làm sạch và tổng hợp trong `evidence/`. Giữ riêng bản có thông tin nhận dạng; không đưa lên repo.
- [ ] **Minh:** Chốt **20–30 câu thử**, gồm **≥5 câu khó**, **≥2 câu từ chối/tấn công** và **≥1/3 câu từ người dùng hoặc dữ liệu thật**. Nếu dùng 24 câu, cần ít nhất 8 câu có nguồn thật. Ghi mã nguồn cho từng câu; dữ liệu demo giả lập không tự động thành câu có nguồn thật. Chạy `python run.py eval`, chấm theo metric, rồi `python run.py score eval/run-1.csv`; bàn giao **x/N và Run ID**.
- [ ] **Quang:** Nối model thật đọc chữ, ảnh và khung hình video. Kiểm một ca thường và một ca lẫn biến thể. Quay **video 30 giây** thấy thao tác và phản hồi AI thật.
- [ ] **Nghĩa:** Nối UI với `answer(text)`, kiểm đúng review dẫn chứng và mốc video; hoàn tất `spec.md` §0–§7. Mở video bằng tab ẩn danh, kiểm số lượt 1 rồi nộp CP3.

### CP4 — 14:30 Thứ Bảy 28/11

- [ ] **Quang:** Chọn **một nhóm lỗi quan trọng** từ lượt 1 và sửa. Chuẩn bị demo trực tiếp và video demo dự phòng mở được bằng tab ẩn danh.
- [ ] **Minh:** Khi bản sửa sẵn sàng, chạy và chấm lượt 2 trên **cùng bộ câu thử**, giữ nguyên chuẩn và đáp án; cập nhật báo cáo so sánh lượt 1 → lượt 2, phân tích ít nhất 3 lỗi cụ thể của lượt 1.
- [ ] **Nhật:** Chuẩn bị trước ≥3 persona, bảng giá ≥2 mức model và 3 kịch bản thấp/cơ sở/cao. Khi Minh đã chấm lượt 2, chạy `python run.py simulate --rate-from eval/run-2.csv` với **≥50 phiên**, seed cố định. Báo chi phí mỗi task thành công cùng model, chi phí theo tháng và so sánh với impact; ghi rõ nguồn hoặc chỗ tự ước tính.
- [ ] **Nghĩa:** Ráp slide trong lúc chờ số; cập nhật kết quả và chi phí khi có. Đặt `demo-slides.pdf` ở gốc repo, hoàn tất `spec.md` đến §9, kiểm link video dự phòng và nộp CP4. Slide có trang đánh giá và chi phí; demo chuẩn bị cả ca thường và ca khó.

**Thứ tự bàn giao CP4:** Quang đưa bản sửa → Minh chạy và chấm lượt 2 → Nhật tính chi phí → Nghĩa chốt số trên slide. Đưa bản bàn giao trước hạn nộp **20–30 phút** để Nghĩa kiểm file, link và form.

**Khóa repo — 23:59 Thứ Bảy:** Nghĩa tổng hợp `spec.md` §10 và `docs/ai-usage.md`; cả bốn người thêm reflection riêng. Không nộp thêm form. Không sửa chuẩn đạt, bộ câu thử, số bằng chứng hoặc kết quả đã chạy sau CP4; nếu chạy thêm thì ghi lượt mới.

## Định dạng dùng chung

UI và cột `input` của benchmark gửi cùng một chuỗi JSON vào `answer(text)`:

```json
{
  "product_url": "https://shopee.vn/ten-san-pham-i.123456.987654",
  "phone_model": "iPhone 15 Pro",
  "case_variant": "Ốp trong suốt viền đen"
}
```

Một review trong dữ liệu demo:

```json
{
  "review_id": "R012",
  "product_id": "987654",
  "phone_model": "iPhone 15 Pro",
  "case_variant": "Ốp trong suốt viền đen",
  "stars": 2,
  "text": "Ốp cấn vào viền camera nên không ôm sát.",
  "media": [
    {"type": "image", "path": "media/R012-camera.jpg"},
    {
      "type": "video",
      "path": "media/R012.mp4",
      "frames": [
        {"time_s": 2, "path": "media/R012-frame-02.jpg"},
        {"time_s": 6, "path": "media/R012-frame-06.jpg"},
        {"time_s": 9, "path": "media/R012-frame-09.jpg"}
      ]
    }
  ]
}
```

Các đường dẫn tính từ `data/`. Review không có media dùng `"media": []`. Link demo ánh xạ đến sản phẩm đã chuẩn bị; link ngoài bộ hiện **“Chưa có dữ liệu”**. Chỉ review đúng biến thể mới vào mẫu chấm.

1. **Minh:** Lấy tối đa **12 review** theo nhóm sao với seed cố định. Lưu số review từng nhóm trong tập đúng biến thể trước khi lấy mẫu để Quang dùng tỷ lệ gốc khi tổng hợp, kể cả khi lấy dư review ít sao.
2. **Quang:** Model chấm hai trục: hướng nhận xét về sản phẩm và độ mạnh của bằng chứng. Ảnh hoặc khung hình chỉ tăng trọng số khi đúng biến thể và hỗ trợ nhận xét. Review có chữ cụ thể vẫn có giá trị khi thiếu media. Ca video chỉ quay bao bì không được cộng trọng số cho nhận xét về độ vừa; không đủ căn cứ từ khung hình thì nói rõ.
3. **Quang:** Code tổng hợp thành **Đáng mua / Cần xem xét thêm / Không đáng mua**. Tập có review nhưng quá ít bằng chứng hữu ích hoặc có mâu thuẫn quan trọng thì chọn **Cần xem xét thêm** và nêu lý do. Kết quả chỉ dẫn mã review đã phân tích, có mốc thời gian nếu dùng khung hình video, và không gắn nhãn “review thật” dựa vào media.
4. **Nghĩa:** UI giữ hợp đồng `answer(text) -> {"output": str}`. Hiển thị lần lượt **Khuyến nghị → Độ phủ (đã phân tích/tổng review đúng biến thể) → Dẫn chứng → Lời khuyên**; có trạng thái đang phân tích, link ngoài bộ demo và thiếu căn cứ. Cho xem video cục bộ tại mục dẫn chứng nếu có, ghi rõ AI chỉ đọc các khung hình được chọn.

## Kiểm trước khi nộp

- Chạy `python run.py check` để kiểm file nộp; trước CP1 tập trung mục `TEAMS.md`, vì benchmark và metric chưa tới mốc hoàn thiện.
- Ở CP3, Nghĩa thử UI một ca thường và một ca khó; kiểm AI chấm ảnh/khung hình thật, cite đúng review, và video mở được ẩn danh. Ca video nên có một ca thấy rõ lỗi ở đúng mẫu và một ca chỉ quay bao bì.
- Đội trưởng dùng cùng một MSSV cho **Form 2 → CP1, CP2, CP3, CP4**. Trước CP4 kiểm bốn điều kiện xét giải: **AI thật, bằng chứng pain, bộ ≥20 câu có kết quả % đạt, slide PDF và video dự phòng**.
- Chỉ commit dữ liệu mẫu hoặc dữ liệu đã làm sạch; không commit `.env`, API key hoặc dữ liệu cá nhân của người khảo sát/người viết review. Ghi rõ dữ liệu giả lập trong Data Card.
