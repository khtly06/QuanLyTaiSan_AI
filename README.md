# Quản lý tài sản trường học AI

Dự án demo xây dựng hệ thống **quản lý tài sản trường học tích hợp AI theo mô hình RAG (Retrieval-Augmented Generation)**.

Hệ thống hỗ trợ quản lý tập trung tài sản, danh mục, phòng ban, kiểm kê, điều chuyển, sửa chữa, thanh lý và báo cáo. AI được tích hợp trực tiếp vào hệ thống để hỗ trợ tra cứu quy định, quy trình và tài liệu nghiệp vụ.
## Cấu trúc project 
- app/: mã nguồn chính của ứng dụng 
- database/: schema và dữ liệu mẫu
- data/documents/: tài liệu tham khảo cho RAG 
- vector_db/: lưu trữ vector database 
- tests/: kiểm thử chức năng 
## Bước khởi tạo
powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
---

## 1. Mục tiêu

* Số hóa quy trình quản lý tài sản trong trường học.
* Quản lý tập trung thông tin tài sản và lịch sử xử lý.
* Hỗ trợ tìm kiếm, lọc và thống kê tài sản.
* Theo dõi kiểm kê, sửa chữa, điều chuyển và thanh lý.
* Tích hợp AI để hỗ trợ tra cứu thông tin nghiệp vụ.
* Áp dụng mô hình RAG để AI sử dụng dữ liệu từ tài liệu được cung cấp.

---

## 2. Chức năng chính

### 2.1. Quản lý tài sản

* Thêm tài sản.
* Xem danh sách tài sản.
* Xem chi tiết tài sản.
* Cập nhật thông tin tài sản.
* Xóa tài sản.
* Kiểm tra mã tài sản trùng.
* Kiểm tra dữ liệu bắt buộc.
* Kiểm tra giá trị tài sản không hợp lệ.
* Tìm kiếm theo mã, tên hoặc người sử dụng.
* Lọc theo danh mục, phòng ban và trạng thái.

### 2.2. Quản lý danh mục

* Thêm và quản lý danh mục tài sản.
* Phân loại tài sản theo nhóm.
* Theo dõi số lượng tài sản theo danh mục.

### 2.3. Quản lý phòng ban

* Quản lý các phòng ban sử dụng tài sản.
* Theo dõi tài sản được phân bổ cho từng phòng ban.
* Thống kê tài sản theo phòng ban.

### 2.4. Kiểm kê

* Tạo đợt kiểm kê.
* Quản lý thời gian kiểm kê.
* Ghi nhận tình trạng thực tế của tài sản.
* So sánh trạng thái dự kiến và thực tế.
* Ghi nhận chênh lệch kiểm kê.

### 2.5. Điều chuyển tài sản

* Tạo phiếu điều chuyển.
* Xác định phòng ban chuyển đi.
* Xác định phòng ban tiếp nhận.
* Ghi nhận ngày điều chuyển.
* Lưu lý do và ghi chú.

### 2.6. Sửa chữa

* Tạo yêu cầu sửa chữa.
* Theo dõi trạng thái sửa chữa.
* Ghi nhận ngày yêu cầu và ngày sửa chữa.
* Quản lý chi phí sửa chữa.
* Theo dõi lịch sử sửa chữa.

### 2.7. Thanh lý

* Tạo yêu cầu thanh lý.
* Ghi nhận ngày thanh lý.
* Ghi nhận lý do thanh lý.
* Quản lý giá trị thanh lý.
* Theo dõi trạng thái xử lý.

### 2.8. Báo cáo

Hệ thống cung cấp các số liệu:

* Tổng số tài sản.
* Tài sản đang sử dụng.
* Tài sản đang sửa chữa.
* Tài sản thanh lý.
* Tổng giá trị tài sản.
* Thống kê theo phòng ban.
* Thống kê theo danh mục.
* Thống kê sửa chữa.
* Thống kê điều chuyển.
* Thống kê thanh lý.
* Thống kê kiểm kê.

---

## 3. Chức năng AI và RAG

Hệ thống tích hợp AI trực tiếp vào ứng dụng thông qua module AI.

### 3.1. AI Chatbot

Người dùng có thể đặt câu hỏi liên quan đến:

* Quy định quản lý tài sản.
* Quy trình kiểm kê.
* Quy trình thanh lý.
* Chính sách quản lý tài sản.
* Tài liệu nghiệp vụ của nhà trường.

### 3.2. Quy trình RAG

Hệ thống thực hiện các bước:

```text
Tài liệu nghiệp vụ
       ↓
Document Loader
       ↓
Document Chunker
       ↓
Embedding
       ↓
Vector Store
       ↓
Retriever
       ↓
Prompt Builder
       ↓
LLM / AI Model
       ↓
Câu trả lời cho người dùng
```

Các tài liệu phục vụ RAG được lưu tại:

```text
data/documents/
```

---

## 4. Công nghệ sử dụng

### Backend

* Python
* Flask
* SQLAlchemy
* SQLite

### Frontend

* HTML5
* CSS3
* JavaScript
* Bootstrap Icons

### AI

* RAG
* Sentence Transformers
* Embedding
* Vector Store
* LLM API

### Testing

* Pytest

---

## 5. Cấu trúc project

```text
QuanLyTaiSan_AI/
│
├── app.py
├── config.py
├── requirements.txt
├── README.md
│
├── app/
│   ├── llm/
│   ├── models/
│   ├── rag/
│   ├── routes/
│   ├── services/
│   ├── static/
│   └── templates/
│
├── data/
│   └── documents/
│
├── database/
│   ├── schema.sql
│   └── seed.sql
│
├── docs/
├── prompts/
├── tests/
└── vector_db/
```

---

## 6. Cài đặt

### Bước 1: Clone project

```powershell
git clone git@github.com:khtly06/QuanLyTaiSan_AI.git
cd QuanLyTaiSan_AI
```

### Bước 2: Tạo môi trường ảo

```powershell
python -m venv .venv
```

Kích hoạt:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Bước 3: Cài đặt thư viện

```powershell
pip install -r requirements.txt
```

### Bước 4: Cấu hình môi trường

Tạo file `.env` và cấu hình các biến môi trường cần thiết cho ứng dụng và AI.

Không đưa API key hoặc thông tin bí mật lên GitHub.

### Bước 5: Chạy ứng dụng

```powershell
python app.py
```

Mở trình duyệt:

```text
http://127.0.0.1:5000
```

---

## 7. Tài khoản demo

### Administrator

```text
Username: admin
Password: admin123
```

### Nhân viên

```text
Username: staff01
Password: staff123
```

---

## 8. Kiểm thử

Chạy toàn bộ test:

```powershell
pytest
```

Một số nhóm test:

```powershell
pytest tests/test_assets.py
pytest tests/test_rag.py
pytest tests/test_llm.py
pytest tests/test_rag_integration.py
pytest tests/test_ui_routes.py
```

---

## 9. Bảo mật

Các thông tin nhạy cảm phải được lưu trong file `.env`.

Không commit các dữ liệu như:

```text
.env
.venv/
__pycache__/
.pytest_cache/
```

API key không được đưa trực tiếp vào source code hoặc repository công khai.

---

## 10. Cập nhật project

Sau khi chỉnh sửa code:

```powershell
git add .
git commit -m "Cập nhật hệ thống"
git push
```

---

## 11. Định hướng phát triển

Trong các phiên bản tiếp theo có thể mở rộng:

* Phân quyền chi tiết theo vai trò.
* Xuất báo cáo Excel/PDF.
* Biểu đồ thống kê trực quan.
* Thông báo tài sản cần sửa chữa.
* Cảnh báo tài sản quá hạn kiểm kê.
* Cải thiện khả năng trả lời của AI.
* Bổ sung thêm tài liệu nghiệp vụ cho hệ thống RAG.
* Theo dõi lịch sử thay đổi dữ liệu.
