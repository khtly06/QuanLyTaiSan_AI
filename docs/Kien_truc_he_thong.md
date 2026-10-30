# Kiến trúc hiện tại

## Thành phần

```mermaid
flowchart TB
    Browser[Trình duyệt: Jinja templates / CSS / JavaScript]
    Flask[Flask app và routes]
    Services[Services / ORM models]
    DB[(SQLite mặc định; URL có thể cấu hình)]
    Docs[data/documents]
    RAG[Loader / chunker / embeddings / retriever]
    LLM[OpenAI-compatible Chat Completions API]

    Browser -->|HTTP form / fetch| Flask
    Flask --> Services
    Services --> DB
    Flask --> RAG
    Docs --> RAG
    RAG -->|prompt giới hạn| LLM
    LLM -->|văn bản| Flask
    Flask -->|JSON / HTML| Browser
```

## Luồng dữ liệu quan trọng

- `app.py` tạo ứng dụng qua `app.create_app`; routes được đăng ký tại `app/routes/__init__.py`.
- SQLAlchemy models ở `app/models/`; cơ sở dữ liệu mặc định đặt tại `database/school_assets.db`.
- RAG đọc tài liệu ở `data/documents/`, chunk và truy xuất trong bộ nhớ; mã hiện không lưu vector DB bền vững.
- AI report truy vấn số liệu thực tế trong `app/routes/ai.py`; LLM được gọi server-side qua `app/llm/llm_service.py`. API key không được gửi tới trình duyệt.
- Cấu hình lấy từ `.env` (không commit); chạy cục bộ mặc định bind `127.0.0.1` và debug tắt.

## Lược đồ dữ liệu đang có

```mermaid
erDiagram
    CATEGORY ||--o{ ASSET : categorizes
    DEPARTMENT ||--o{ ASSET : owns
    ASSET ||--o{ TRANSFER : history
    DEPARTMENT ||--o{ TRANSFER : source
    DEPARTMENT ||--o{ TRANSFER : destination
    ASSET ||--o{ INVENTORY_DETAIL : inspected
    INVENTORY ||--o{ INVENTORY_DETAIL : contains
    ASSET ||--o{ REPAIR : repair_history
    ASSET ||--o{ DISPOSAL : disposal_request
    USER {
        int id PK
        string username UK
        string email UK
        string password_hash
        string role
        boolean is_active
    }
    CATEGORY {
        int id PK
        string name UK
    }
    DEPARTMENT {
        int id PK
        string name UK
        string code UK
    }
    ASSET {
        int id PK
        string asset_code UK
        string name
        int category_id FK
        int department_id FK
        float value
        string status
    }
    INVENTORY {
        int id PK
        string name
        date start_date
        date end_date
        string status
        string created_by
    }
    INVENTORY_DETAIL {
        int id PK
        int inventory_id FK
        int asset_id FK
        string expected_status
        string actual_status
        string variance_note
        string checked_by
        datetime checked_at
    }
    TRANSFER {
        int id PK
        int asset_id FK
        int from_department_id FK
        int to_department_id FK
        date transfer_date
        string performed_by
    }
    REPAIR {
        int id PK
        int asset_id FK
        date request_date
        string status
        float cost
        string requested_by
        string updated_by
    }
    DISPOSAL {
        int id PK
        int asset_id FK
        date disposal_date
        string status
        float liquidation_value
        string requested_by
        string decided_by
    }
```

## Thiết kế so với hệ thống đang chạy

- Hiện có `Category`, `Department`, `Asset`, `Inventory`, `InventoryDetail`, `InventoryObservation`, `Transfer`, `Repair`, `Disposal`, `User`; không có bảng `Location`, `Role`, AI report hoặc audit log riêng.
- `Asset.location` hiện là chuỗi tự do. Phòng ban là quan hệ có khóa ngoại.
- Kiểm kê snapshot tài sản ngoài trạng thái thanh lý; kết quả thực tế gồm tình trạng, người kiểm và thời điểm. `InventoryObservation` chứa tài sản quan sát được nhưng không thuộc snapshot. Campaign chỉ khóa sau khi mọi tài sản kỳ vọng có kết quả.
- Sửa chữa có trạng thái `pending`/`in_progress`/`completed`/`cancelled`; thanh lý có trạng thái yêu cầu và quyết định admin. Các actor được lưu trực tiếp trên workflow, nhưng không có audit log sự kiện đầy đủ.
- Schema ORM do SQLAlchemy `create_all` tạo; startup còn chạy bổ sung cột SQLite additive/idempotent cho các workflow mới. `database/schema.sql` là tài liệu SQL độc lập, không phải migration đang được chạy. Chưa có migration versioned.
- CSRF/RBAC được áp dụng ở backend; report AI cho phép chọn phòng ban/đợt kiểm kê. Chưa có ACL theo phòng ban cho từng user.
- `database/backup.py` hỗ trợ backup/restore SQLite sang file mới và kiểm tra integrity; chưa có lịch backup hoặc production restore drill. `/health` chạy query DB, không thay thế readiness/monitoring production.


