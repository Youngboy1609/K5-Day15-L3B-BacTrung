# Shopee Collector

Công cụ thu thập thông tin sản phẩm và đánh giá mà trình duyệt tải khi mở các link Shopee đã chọn. Dữ liệu và tiến độ được lưu vào SQLite, sau đó xuất ra CSV, JSONL và báo cáo.

## 1. Chuẩn bị trên Windows

Cần Python 3.10 trở lên, Google Chrome, PowerShell và kết nối Internet. Chạy từ thư mục gốc của repo nhóm.

```powershell
Set-Location .\Shopee_Collector
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Luồng bên dưới dùng Chrome đã cài trên máy. Nếu muốn dùng trình duyệt Chromium do Playwright tự mở, chạy `SETUP_WINDOWS.bat` rồi `START_WINDOWS.bat`.

## 2. Mở Chrome riêng và đăng nhập bằng QR

Trong PowerShell tại `Shopee_Collector`, chạy lệnh sau. Chrome tạo profile mới ở `chrome_profile/` trong lần đầu. Nếu Chrome được cài ở vị trí khác, thay đường dẫn tới `chrome.exe`.

```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" `
  --remote-debugging-port=9222 `
  --user-data-dir="$PWD\chrome_profile" `
  "https://shopee.vn/"
```

1. Trong cửa sổ Chrome vừa mở, bấm **Đăng nhập** trên Shopee và chọn đăng nhập bằng **mã QR**.
2. Mở ứng dụng Shopee trên điện thoại, quét mã QR trên màn hình và xác nhận đăng nhập.
3. Kiểm tra trang Shopee đã đăng nhập trên máy tính, rồi giữ cửa sổ này mở.

Kiểm tra Chrome đang nghe cổng CDP bằng lệnh sau. Kết quả có dạng `Chrome/...`. Chrome cần thư mục profile riêng để bật cổng gỡ lỗi. Giữ kết nối trên máy cục bộ và đóng cửa sổ Chrome này sau khi chạy xong. [Tài liệu Chrome](https://developer.chrome.com/blog/remote-debugging-port)

```powershell
(Invoke-RestMethod 'http://127.0.0.1:9222/json/version').Browser
```

## 3. Chạy với ba sản phẩm

Tại PowerShell, vẫn trong `Shopee_Collector`, chạy:

```powershell
.\.venv\Scripts\python.exe -m shopee_collector run --cdp http://127.0.0.1:9222 --output output/testsp_500
```

Khi thấy `shopee>`, nhập `run`. Với mỗi sản phẩm, collector lấy tối đa 500 đánh giá, chia đều 100 cho mỗi mức từ 1 đến 5 sao. Collector giữ các mã đánh giá hợp lệ gặp đầu tiên trong từng nhóm. Nếu nhóm 1 sao chỉ có 24 đánh giá và bốn nhóm còn lại đều có ít nhất 100, mẫu có tối đa 424 đánh giá.

Khi còn thiếu mẫu, collector dùng bộ lọc sao và nút phân trang đang hiển thị. Xem `review_sample_by_star` trong `stats` hoặc `coverage_report.json` để đối chiếu tổng gốc (`total`), chỉ tiêu (`target`) và số đã lưu (`saved`). Khi chưa đọc được tổng chính xác, `total` là `null` và chỉ tiêu vẫn là 100. Nếu hết dữ liệu trước khi đủ chỉ tiêu, tiến độ ghi `star_sample_incomplete`. Khi gặp yêu cầu xác minh, collector dừng và lưu phần đã thu được.

Cờ `--all-reviews` là tùy chọn chủ động bỏ qua giới hạn review và đọc tiếp các trang đang hiển thị. Chỉ dùng khi có lý do phù hợp; nó vẫn không đảm bảo lấy được toàn bộ review và không được dùng trong demo CP3, vốn chạy trên fixture cục bộ.

| Lệnh tại `shopee>` | Dùng khi |
|---|---|
| `run` | Chạy hàng chờ các link sản phẩm |
| `capture` | Lưu nội dung đang hiển thị ở tab đã kết nối, gồm các đánh giá đọc được mã. Trên trang danh mục, lệnh ghi nhận các liên kết hiển thị |
| `stats` | Xem số bản ghi, tiến độ và các trường còn thiếu |
| `export` | Xuất lại dữ liệu đã lưu |
| `retry` | Đưa mục bị tạm dừng hoặc lỗi về hàng chờ sau khi bạn đã kiểm tra trang trong Chrome và truy cập được bình thường. Sau đó nhập `run` |
| `quit` | Lưu và thoát collector. Chrome do bạn mở vẫn chạy |

Nếu thấy `ECONNREFUSED`, kiểm tra cửa sổ Chrome còn mở và lệnh kiểm tra cổng ở bước 2 trả về `Chrome/...`. Nếu Shopee tiếp tục yêu cầu xác minh hoặc trả lỗi 401, 403, 429, dừng lần chạy và kiểm tra trên trình duyệt trước khi tiếp tục.

### Lưu đánh giá khi tự thao tác trong Chrome

1. Khởi động collector bằng lệnh ở bước 3. Tại dấu nhắc `shopee>`, để nguyên hàng chờ và mở sản phẩm trong **cùng tab Chrome đã kết nối**.
2. Tự cuộn tới đánh giá. Khi các đánh giá đã hiện, nhập `capture` trong terminal. Con số in ra là số đánh giá có mã đọc được trên trang đó. SQLite gộp các lần lưu trùng mã cho cùng một sản phẩm.
3. Với mẫu 500 đánh giá, chọn nhóm sao còn thiếu trong `review_sample_by_star`, chờ nội dung hiện rồi nhập `capture`. Khi dùng `--all-reviews`, bắt đầu từ trang 1 với bộ lọc **Tất cả** và đi theo thứ tự. Xem mốc phân trang trong `review_pagination`.
4. Nếu collector báo tạm dừng, kiểm tra trực tiếp trong Chrome. Khi đã xem được trang bình thường, nhập `retry`, rồi tiếp tục bằng `capture`. Nhập `quit` để xuất dữ liệu và kết thúc.

Với lệnh `run`, `stats` và `coverage_report.json` có mục `last_interruption` ghi lần dừng do lỗi gần nhất, gồm thời điểm UTC, mã sản phẩm nếu có, bước đang chạy và lý do. Ví dụ, `scroll_product` cho biết collector phát hiện lỗi lúc cuộn sản phẩm. Với dữ liệu cũ chưa có bản ghi chẩn đoán, mục này có giá trị `null`.

### Chọn link khác hoặc chạy tiếp

- Để thử link khác, sao chép `config/settings.json` thành `config/settings.local.json`. Thay danh sách `seeds` bằng các link sản phẩm Shopee đầy đủ, để `keywords` là `[]` và giữ các mục cấu hình còn lại. Thêm `--config config/settings.local.json` vào lệnh.
- Để tiếp tục một lần chạy dở, chạy lại với cùng `--output`. SQLite giữ hàng chờ, review theo ID và mốc phân trang đã ghi. Dùng thư mục đầu ra mới cho một lần chạy độc lập.
- Thêm `--refresh` khi muốn đưa các sản phẩm trong `seeds` đã xử lý về hàng chờ để quan sát lại. Dữ liệu đã ghi vẫn được giữ.
- Thêm `--all-reviews` nếu muốn quay lại chế độ thu tất cả đánh giá có thể quan sát. Lệnh `export` dùng chế độ của lần chạy gần nhất trong thư mục đầu ra đó.

## 4. Kiểm tra kết quả

Lệnh ở bước 3 ghi vào `output/testsp_500/`. Mở `coverage_report.json` trước để xem trạng thái từng sản phẩm và số review hoặc media đã thu được. Các file CSV dùng UTF-8 BOM để Excel đọc được tiếng Việt.

| File hoặc thư mục | Nội dung |
|---|---|
| `coverage_report.json` | Hàng chờ, trường chi tiết còn thiếu, tiến độ phân trang review và số media đã lưu |
| `products.csv`, `variants.csv` | Sản phẩm và các phân loại đã quan sát, gồm giá và tồn kho nếu có |
| `reviews.csv` | Mã review, sản phẩm, điểm, nội dung và phân loại đã mua nếu có |
| `images.csv`, `videos.csv` | URL, vai trò, trạng thái tải và đường dẫn tới file trong `images/` hoặc `videos/` |
| `shops.csv`, `categories.csv` | Thông tin shop và danh mục đã quan sát |
| `products.jsonl`, `catalog.sqlite3` | Dữ liệu sản phẩm lồng nhau, kho dữ liệu và tiến độ để chạy tiếp |

Có thể xuất lại các file từ SQLite khi collector đã dừng.

```powershell
.\.venv\Scripts\python.exe -m shopee_collector export --output output/testsp_500
```

Đối chiếu giá, biến thể và vài review với trang sản phẩm trước khi dùng dữ liệu. Các trường thiếu hoặc giá cần xác minh được ghi trong báo cáo hoặc metadata. Profile Chrome, cấu hình cục bộ và dữ liệu thu thập dùng trên máy cá nhân. Hãy rà thông tin nhận dạng trong nội dung review trước khi chia sẻ dữ liệu.

## 5. Chạy kiểm tra offline

```powershell
.\.venv\Scripts\python.exe -X utf8 -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -m shopee_collector demo --output output/demo
```

Chế độ `demo` dùng dữ liệu giả lập từ `tests/synthetic_payload.json` để kiểm tra luồng đọc, lưu và xuất dữ liệu. Xem [nhật ký kiểm thử](VALIDATION.md) để biết phạm vi của lần kiểm tra trước.
