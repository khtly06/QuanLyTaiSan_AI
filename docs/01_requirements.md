# Yêu cầu hệ thống

Đây là danh mục yêu cầu tổng quan. Đặc tả quy trình, actor, đầu vào/đầu ra và giới hạn hiện tại được ghi tại [ANALYSIS.md](./ANALYSIS.md); trạng thái có bằng chứng tại [TRACEABILITY_MATRIX.md](./TRACEABILITY_MATRIX.md).

## Actor

- Quản trị viên.
- Cán bộ quản lý tài sản.
- Nhân viên/kiểm kê viên.
- Dịch vụ AI phía backend (thành phần hỗ trợ, không phải người dùng trực tiếp).

## Yêu cầu chức năng

- Đăng nhập, đăng xuất, đổi mật khẩu và phân quyền backend.
- CRUD tài sản; mã duy nhất; nhóm, phòng ban/vị trí, người phụ trách, giá trị, ngày mua, trạng thái và lịch sử.
- Quản lý danh mục/phòng ban/vị trí có kiểm tra quan hệ đang được sử dụng.
- Điều chuyển có xác thực nguồn/đích và lưu lịch sử.
- Kiểm kê theo đợt với từng tài sản, thực tế, thiếu/hỏng/sai lệch, người và thời gian.
- Sửa chữa/bảo trì và thanh lý có trạng thái, lịch sử, phê duyệt thích hợp.
- Tìm kiếm/lọc, dashboard và báo cáo từ dữ liệu database thật.
- AI báo cáo một đợt kiểm kê, tóm tắt phòng ban theo quyền và đề xuất có căn cứ; kết quả phải được người dùng kiểm chứng.

## Yêu cầu phi chức năng

- Không có mật khẩu mặc định; mật khẩu được hash; secret/API key chỉ lấy từ môi trường.
- Kiểm soát quyền tại backend, session an toàn, chống CSRF/XSS/SQL injection phù hợp.
- Transaction và ràng buộc dữ liệu; backup/restore có kiểm chứng.
- Phản hồi lỗi thân thiện, không tiết lộ thông tin bí mật; giao diện tiếng Việt và responsive.
- AI có timeout/giới hạn, tối thiểu hóa dữ liệu gửi đi, phân biệt dữ kiện/suy luận/đề xuất và không tự ghi thay đổi.
- Chất lượng được xác nhận bằng test tự động, browser test và kiểm thử vận hành phù hợp.
