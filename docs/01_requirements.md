# 01 Requirements - Hệ thống quản lý tài sản trường học có tích hợp AI

## 1. Bối cảnh
Trường học cần quản lý máy tính, máy chiếu, bàn ghế, thiết bị mạng, phòng học và lịch kiểm kê. Quản lý thủ công bằng sổ sách dễ thất lạc, khó theo dõi tình trạng, điều chuyển, sửa chữa, thanh lý và giá trị tài sản.

## 2. Actors
- Admin/Quản trị viên
- Cán bộ quản lý tài sản
- Kiểm kê viên
- Người sử dụng/Phòng ban

## 3. Chức năng
### FR-ASSET
- Quản lý danh mục, nhóm và mã tài sản.
- Thêm, sửa, xóa, tra cứu tài sản.
- Cập nhật tình trạng, vị trí, người phụ trách.

### FR-DEPT
- Quản lý phòng ban, phòng học, vị trí.

### FR-TRANSFER
- Lập và xử lý điều chuyển tài sản.
- Kiểm tra trạng thái tài sản trước điều chuyển.

### FR-INVENTORY
- Lập đợt kiểm kê.
- Ghi nhận thiếu, hỏng, cần sửa, bình thường.
- Tổng hợp kết quả.

### FR-MAINTENANCE
- Quản lý yêu cầu và lịch sử sửa chữa.

### FR-DISPOSAL
- Lập và phê duyệt thanh lý.

### FR-AI-REPORT
- Sinh báo cáo kiểm kê.
- Tóm tắt tình trạng theo phòng ban.
- Gợi ý sửa chữa/thay thế.

## 4. Yêu cầu phi chức năng
- Bảo mật và phân quyền theo vai trò.
- Phản hồi nhanh cho CRUD thông thường.
- Sao lưu dữ liệu.
- Giao diện dễ sử dụng.
- AI không tự tạo số liệu ngoài dữ liệu đầu vào.

STATUS: PASS
NEXT_PROMPT: prompts/02_design.md
