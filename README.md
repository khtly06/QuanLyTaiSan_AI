# Quản lý tài sản trường học AI

Dự án demo Flask quản lý tài sản trường học tích hợp AI theo mô hình RAG.

## Cấu trúc project

- `app/`: mã nguồn chính của ứng dụng
- `database/`: schema và dữ liệu mẫu
- `data/documents/`: tài liệu tham khảo cho RAG
- `vector_db/`: lưu trữ vector database
- `tests/`: kiểm thử chức năng

## Bước khởi tạo

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Chạy ứng dụng

```powershell
python app.py
```

Mở trình duyệt tại: http://127.0.0.1:5000


## Cập nhật giao diện & CRUD tài sản

Phiên bản này đã nâng cấp module **Quản lý tài sản** theo hướng giao diện quản trị chuyên nghiệp và thao tác dữ liệu thực:

- Dashboard chỉ số tài sản lấy trực tiếp từ database.
- Thêm tài sản và lưu trực tiếp vào SQLite.
- Sửa tài sản bằng cửa sổ modal, không còn nút tĩnh.
- Xóa tài sản có hộp thoại xác nhận và thông báo kết quả.
- Kiểm tra mã tài sản trùng, dữ liệu bắt buộc và giá trị âm.
- Tìm kiếm theo mã, tên hoặc người sử dụng.
- Lọc theo danh mục, phòng ban và trạng thái.
- Hiển thị trạng thái bằng badge tiếng Việt và số liệu tổng hợp.
- Sidebar đã liên kết đúng đến form thêm và khu vực tra cứu.
- Responsive cho màn hình nhỏ.

### Chạy dự án

```powershell
cd QuanLyTaiSan_AI
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Sau đó mở `http://127.0.0.1:5000`.
