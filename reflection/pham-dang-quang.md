# Reflection — Phạm Đăng Quang

*Bản nháp để Quang rà lại sau lượt đánh giá chính thức đầu tiên.*

1. **Vai trò và phần việc**\
   Phụ trách workflow đọc review và phần kết nối model của BacTrung.\
   `codebase/agent.py` lọc đúng biến thể, tổng hợp review theo phân bố sao gốc và kiểm mã dẫn chứng.\
   `codebase/ai.py` gửi chữ, ảnh và khung hình đã trích cho model rồi lấy số token từ phản hồi API.

2. **AI hỗ trợ và chỗ cần soát**\
   Codex hỗ trợ viết workflow, kết nối OpenRouter và chuẩn bị các ca kiểm tra.\
   Khi kiểm bản đầu, quy tắc mock dựa vào số từ có thể cho điểm câu dài chỉ nói về giao hàng. Quy tắc đã đổi sang nhận diện chi tiết về ốp trong fixture.\
   Lần kiểm bằng model thật cho thấy ca iPhone 15 Pro dẫn đúng `R012` ở `00:06`, là cảnh thấy khe hở cạnh camera.\
   Video CP3 giữ nguyên phản hồi thực tế từ API và ghi rõ nguồn hình minh họa.

3. **Một câu thử trượt và bài học**\
   Chờ lượt 1 đã chấm của nhóm để lấy mã câu và phản hồi thực tế.\
   Điền chi tiết dẫn chứng hoặc quyết định sai, sau đó ghi bài học và cách kiểm lại sau sửa.
