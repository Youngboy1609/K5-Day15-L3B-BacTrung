# Shopee Collector (Windows)

Hướng dẫn chạy collector với Chrome riêng qua Chrome DevTools Protocol (CDP). Collector đọc dữ liệu mà trang Shopee tải trong trình duyệt và lưu tiến độ cùng các file xuất vào thư mục `output`.

## Yêu cầu

- Windows 10/11 và PowerShell.
- Python 3.10 trở lên; lệnh `py -3` có sẵn.
- Google Chrome tại `C:\Program Files\Google\Chrome\Application\chrome.exe`.
- Kết nối Internet.

## Cài đặt lần đầu

Mở PowerShell tại thư mục `Shopee_Collector`, rồi chạy:

```powershell
.\SETUP_WINDOWS.bat
```

Script tạo `.venv`, cài các gói trong `requirements.txt` và cài Chromium cho Playwright. Nếu muốn cài thủ công:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
```

## Chạy với tài khoản Shopee của bạn

### 1. Mở một Chrome profile riêng

Đóng Chrome đang dùng `chrome_profile` trước khi mở phiên mới. Nếu thư mục profile đã có dữ liệu cũ và bạn cần một profile hoàn toàn mới, hãy tự sao lưu hoặc xóa riêng `chrome_profile` sau khi xác nhận không cần phiên cũ. Profile này tách biệt với Chrome cá nhân thông thường.

Trong PowerShell tại thư mục `Shopee_Collector`, mở trang Shopee bằng Chrome:

```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" `
  --remote-debugging-port=9222 `
  --user-data-dir="$PWD\chrome_profile" `
  "https://shopee.vn/"
```

Giữ cửa sổ Chrome mở. Nếu Chrome được cài ở vị trí khác, thay đường dẫn đến `chrome.exe`.

### 2. Đăng nhập thủ công bằng QR

Trong cửa sổ Chrome vừa mở, tự đăng nhập Shopee bằng QR code trên điện thoại. Chờ trang hoàn tất đăng nhập; không đưa mật khẩu, OTP, cookie hoặc QR đăng nhập vào chat hay file cấu hình. Không đóng Chrome trong lúc collector đang chạy.

Có thể kiểm tra cổng CDP từ một cửa sổ PowerShell khác:

```powershell
(Invoke-RestMethod "http://127.0.0.1:9222/json/version").Browser
```

Kết quả cần có dạng `Chrome/...`. Nếu kết nối thất bại, kiểm tra Chrome còn mở và đang dùng đúng cổng `9222`.

### 3. Chạy collector cho 3 sản phẩm

Mở PowerShell tại thư mục `Shopee_Collector` và chạy:

```powershell
.\.venv\Scripts\python.exe -m shopee_collector run --cdp http://127.0.0.1:9222 --output output/test_3_san_pham --all-reviews
```

Lệnh dùng các URL sản phẩm trong `config/settings.json` (mặc định là ba sản phẩm đã cấu hình), kết nối tới Chrome đang đăng nhập và cố gắng chuyển các trang đánh giá cho đến khi hết trang hoặc không còn tiến triển. Khi hiện dấu nhắc `shopee>`, nhập:

```text
run
```

Để thoát sau khi hoàn tất, nhập `quit`. Tiến độ được ghi vào SQLite và các file xuất được cập nhật tự động; nếu dừng giữa chừng, chạy lại cùng lệnh và cùng `--output` để tiếp tục. Muốn một lượt hoàn toàn mới, chọn một thư mục `--output` mới. `--all-reviews` không bảo đảm lấy được mọi đánh giá: dữ liệu phụ thuộc trang thực tế tải, phân trang và giới hạn truy cập.

## Kết quả

Trong `output/test_3_san_pham/`:

- `products.csv`, `reviews.csv`, `variants.csv`, `shops.csv`, `categories.csv`: dữ liệu đã chuẩn hóa.
- `products.jsonl`: dữ liệu sản phẩm dạng JSONL.
- `catalog.sqlite3`: dữ liệu và tiến độ để chạy tiếp.
- `coverage_report.json`: thống kê kết quả, trường thiếu và phạm vi đã quan sát.
- `images.csv`, `videos.csv` nếu có media được quan sát.

Media tải về được lưu trong `output_media/`. Kiểm tra báo cáo và dữ liệu trước khi sử dụng hoặc chia sẻ; không xem kết quả là bao phủ toàn bộ Shopee. CSV dùng UTF-8 BOM để thuận tiện mở bằng Excel.

## Lệnh kiểm tra offline

Các lệnh sau chạy trên dữ liệu giả lập/kiểm thử, không đăng nhập Shopee:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m shopee_collector demo --output output/demo
```

## Lưu ý về quyền riêng tư và giới hạn

- Chỉ dùng tài khoản của bạn và dữ liệu bạn có quyền truy cập; tuân thủ điều khoản Shopee và quy định áp dụng. Dừng nếu gặp yêu cầu xác minh hoặc giới hạn truy cập; không tìm cách vượt chặn.
- Profile `chrome_profile` có thể chứa phiên đăng nhập. Không chia sẻ hoặc commit profile, dữ liệu crawl, SQLite, ảnh/video hay file output.
- Review công khai có thể chứa thông tin cá nhân do người viết tự đưa vào. Rà soát và loại bỏ thông tin nhạy cảm trước khi chia sẻ dữ liệu.
- Collector chỉ lưu các trường được chọn từ dữ liệu mà trang tải; cấu trúc trang có thể thay đổi, giá/đơn vị và mức độ đầy đủ cần được kiểm tra độc lập.
