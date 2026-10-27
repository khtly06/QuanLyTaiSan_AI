# Quản lý tài sản trường học

Ứng dụng web Flask/SQLAlchemy để quản lý tài sản trường học. Có luồng ghi nhận kiểm kê, sửa chữa, thanh lý có phê duyệt, điều chuyển, RBAC/CSRF và báo cáo AI theo số liệu được chọn. Đây chưa phải sản phẩm production được chứng nhận: migration vẫn chưa versioned, chưa có audit log tổng quát, login rate limit, E2E hoặc thử nghiệm provider AI live. Xem [bảng đối chiếu](docs/TRACEABILITY_MATRIX.md) và [báo cáo gap](docs/GAP_ANALYSIS.md).

## Công nghệ và cấu trúc

- Backend: Python, Flask, Flask-SQLAlchemy.
- Database mặc định: SQLite tại `database/school_assets.db`; có thể đặt `DATABASE_URL`.
- Giao diện: Jinja templates, CSS, JavaScript trong `app/templates` và `app/static`.
- AI/RAG: tài liệu trong `data/documents`; gọi LLM server-side qua `app/llm/llm_service.py`.
- Test: pytest trong `tests/`.

## Cài đặt và khởi động (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Mở `.env`, tạo `SECRET_KEY` ngẫu nhiên bằng `python -c "import secrets; print(secrets.token_hex(32))"` (ít nhất 32 ký tự khi production) rồi cấu hình thông tin quản trị ban đầu (xem bên dưới). Không commit `.env`.

Khởi chạy:

```powershell
python app.py
```

Mặc định server bind `127.0.0.1:5000`, debug tắt. Chỉ cấu hình `HOST=0.0.0.0` khi chủ động triển khai sau reverse proxy/firewall phù hợp. Có endpoint `/health` kiểm tra kết nối DB; chưa có bằng chứng triển khai production.

### Tạo tài khoản quản trị ban đầu

Không còn tài khoản/mật khẩu demo được tạo tự động. Đặt đủ các biến sau trong `.env` trước lần khởi động đầu tiên:

```dotenv
INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_EMAIL=admin@example.edu.vn
INITIAL_ADMIN_FULL_NAME=Quan tri vien
INITIAL_ADMIN_PASSWORD=thay-bang-mat-khau-dai-ngau-nhien
```

Mật khẩu phải có ít nhất 12 ký tự. Tài khoản chỉ được tạo nếu username chưa tồn tại; khởi động sau không ghi đè mật khẩu. Nên xóa `INITIAL_ADMIN_PASSWORD` khỏi `.env` sau khi tài khoản được tạo.

Tùy chọn `SEED_DEMO_DATA=true` nạp dữ liệu SQL mẫu khi bảng danh mục còn trống. Để mặc định `false` cho dữ liệu thật.

### Vai trò và nghiệp vụ chính

- `admin`: quản trị tài khoản, toàn quyền nghiệp vụ và quyết định duyệt/từ chối thanh lý.
- `manager`: thao tác nghiệp vụ và tạo báo cáo AI.
- `inspector`: thao tác kiểm kê; các luồng khác chỉ đọc.
- `staff`: chỉ đọc, ngoại trừ đổi mật khẩu của mình và AI chat.

CSRF áp dụng cho form và request thay đổi; JSON fetch cần gửi token `X-CSRFToken`. Đợt kiểm kê chụp danh sách tài sản lúc tạo và chỉ hoàn tất sau khi từng tài sản được kiểm đếm tường minh; chỉ ghi nhận “không tìm thấy” sau xác nhận của người kiểm kê. Yêu cầu sửa chữa có vòng đời riêng và đồng bộ trạng thái tài sản. Yêu cầu thanh lý ở trạng thái chờ đến khi admin quyết định; tài sản được duyệt chuyển sang `disposal`.

## Cấu hình AI

```dotenv
LLM_API_KEY=
LLM_MODEL=gpt-3.5-turbo
LLM_API_BASE_URL=https://api.openai.com/v1/chat/completions
LLM_TIMEOUT_SECONDS=30
LLM_MAX_PROMPT_CHARS=12000
```

Chỉ gọi API tương thích OpenAI Chat Completions. API key chỉ được dùng ở backend; không điền key thật vào tài liệu hoặc Git. Nếu thiếu key, báo cáo vẫn trả số liệu database và hiển thị rõ AI chưa được cấu hình. Đầu ra báo cáo AI được yêu cầu ở JSON và kiểm tra cấu trúc trước khi hiển thị. Chưa có xác nhận gọi thành công nhà cung cấp thật trong phiên kiểm tra này.

## Database, backup và khôi phục

Schema ORM được tạo lúc khởi động bằng `db.create_all()` và ứng dụng có nâng cấp SQLite additive/idempotent cho các cột workflow mới; đây không phải migration versioned. Test nâng cấp xác nhận dữ liệu cũ được giữ và foreign keys SQLite bật. Dữ liệu thực tế không nên reset để test.

Có thể tạo bản sao SQLite đã kiểm tra integrity bằng `python -m database.backup backup --output C:\backups\school_assets.db`. Khôi phục sang file mới bằng `python -m database.backup restore --source C:\backups\school_assets.db --destination C:\restore-test\school_assets.db`. Công cụ từ chối ghi đè file có sẵn; test chỉ chạy trên SQLite tạm, chưa có restore drill production hay lịch backup tự động. Giữ backup ngoài thư mục làm việc và xác minh bản khôi phục trước khi dùng.

Endpoint `/health` thực hiện query DB và trả `503` nếu không truy vấn được. Đây là health check cơ bản, không thay thế giám sát/kiểm tra sẵn sàng production.

### Tạo dữ liệu mẫu cho workflow

Sau khi đã có ít nhất 20 tài sản `TEST-ASSET-*` và các phòng ban `TEST-*`, chạy:

```powershell
python -m database.seed_workflow_samples
```

Script thêm 10 kết quả kiểm kê đã ghi, 10 yêu cầu thanh lý (5 chờ duyệt, 5 từ chối), 10 điều chuyển và 10 phiếu sửa chữa. Mọi bản ghi có nhãn `[TEST-SAMPLE]`; script có thể chạy lại mà không tạo bản sao. Dữ liệu được ghi vào SQLite đã cấu hình nên tồn tại sau khi tải lại ứng dụng. Các yêu cầu sửa chữa còn mở sẽ đặt tài sản tương ứng ở trạng thái `repair`; các yêu cầu thanh lý mẫu không tự thanh lý tài sản.

## Kiểm thử

```powershell
python -m pytest -q
```

Test tạo database riêng trong thư mục tạm và không sử dụng database mặc định. Chạy `python -m pytest -q` để kiểm tra toàn suite. Test LLM dùng mock HTTP; không phải bằng chứng API/model thật đã chạy. Để chạy test, các dependencies Python cơ bản phải được cài; `pip install -r requirements.txt` cài đầy đủ thư viện ứng dụng.

## Tài liệu

- [Phân tích nghiệp vụ](docs/ANALYSIS.md)
- [Use Case](docs/USE_CASE.md)
- [Kiến trúc và ERD](docs/ARCHITECTURE.md)
- [Phân tích khoảng trống và ưu tiên](docs/GAP_ANALYSIS.md)
- [Ma trận truy vết 36 nhiệm vụ](docs/TRACEABILITY_MATRIX.md)
- [Nhật ký SDLC AI](docs/AI_SDLC_LOG.md)
- [Thử nghiệm prompt](docs/AI_PROMPT_EXPERIMENTS.md)
- [Báo cáo bàn giao và kịch bản demo](docs/FINAL_DELIVERY.md)
