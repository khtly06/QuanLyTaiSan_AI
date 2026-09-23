INSERT INTO users (username, email, password_hash, role, full_name)
VALUES
    ('admin', 'admin@school.edu.vn', 'hashed_admin_password', 'admin', 'Quản trị viên'),
    ('staff01', 'staff01@school.edu.vn', 'hashed_staff_password', 'staff', 'Nhân viên quản lý');

INSERT INTO categories (name, description)
VALUES
    ('Máy tính', 'Thiết bị tin học cho công tác quản lý và giảng dạy'),
    ('Phòng học', 'Mặt bằng và thiết bị trong phòng học'),
    ('Thiết bị văn phòng', 'Máy in, máy scan, nội thất văn phòng');

INSERT INTO departments (name, code, description)
VALUES
    ('Ban Giám hiệu', 'BGH', 'Ban lãnh đạo trường học'),
    ('Khoa Công nghệ', 'CNTT', 'Khoa tin học và công nghệ'),
    ('Phòng Kế toán', 'KT', 'Phòng tài chính và kế toán');

INSERT INTO assets (asset_code, name, category_id, department_id, user_name, purchase_date, value, status, location, notes)
VALUES
    ('TS-001', 'Laptop Dell Latitude', 1, 2, 'Nguyễn Văn A', '2024-01-15', 24000000, 'active', 'Phòng máy 2', 'Laptop chính thức của phòng khoa'),
    ('TS-002', 'Máy in Canon', 3, 3, 'Trần Thị B', '2023-10-20', 8500000, 'active', 'Phòng kế toán', 'Máy in cho văn phòng'),
    ('TS-003', 'Bàn ghế giáo viên', 3, 1, 'Lê Văn C', '2022-08-05', 12000000, 'repair', 'Phòng hiệu trưởng', 'Cần thay mới ghế');

INSERT INTO inventory (name, start_date, end_date, status)
VALUES
    ('Kiểm kê đầu năm 2025', '2025-01-10', '2025-01-25', 'completed');

INSERT INTO inventory_details (inventory_id, asset_id, expected_status, actual_status, variance_note)
VALUES
    (1, 1, 'active', 'active', 'Không có chênh lệch'),
    (1, 2, 'active', 'active', 'Không có chênh lệch'),
    (1, 3, 'active', 'repair', 'Thiếu một chân ghế');

INSERT INTO transfers (asset_id, from_department_id, to_department_id, transfer_date, reason, notes)
VALUES
    (2, 3, 2, '2025-02-01', 'Chuyển theo phân công mới', 'Lưu vị trí mới tại khoa CNTT');

INSERT INTO repairs (asset_id, request_date, repair_date, status, description, cost)
VALUES
    (3, '2025-02-10', '2025-02-15', 'completed', 'Sửa chân ghế và bọc da', 2500000);

INSERT INTO disposals (asset_id, disposal_date, reason, liquidation_value, status)
VALUES
    (3, '2025-03-01', 'Hết tuổi thọ và hư hỏng nặng', 2000000, 'approved');
