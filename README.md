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
