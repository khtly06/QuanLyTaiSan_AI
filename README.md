# Quản lý tài sản trường học

Ứng dụng web Flask/SQLAlchemy để quản lý tài sản trường học. Có luồng ghi nhận kiểm kê, sửa chữa, thanh lý có phê duyệt, điều chuyển, RBAC/CSRF và báo cáo AI theo số liệu được chọn. Đây chưa phải sản phẩm production được chứng nhận: migration vẫn chưa versioned, chưa có audit log tổng quát, login rate limit, E2E hoặc thử nghiệm provider AI live. Xem [bảng đối chiếu](docs/Ma_tran_theo_doi_yeu_cau.md) và [báo cáo gap](docs/Phan_tich_khoang_trong.md).

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

Mở `.env`, tạo `SECRET_KEY` ngẫu nhiên bằng `python -c "import secrets; print(secrets.token_hex(32))"` (ít nhất 32 ký tự khi production), rồi cấu hình tài khoản quản trị ban đầu bên dưới. `SEED_DEMO_DATA=true` được bật sẵn trong `.env.example`: lần chạy đầu trên database mới sẽ tự tạo dữ liệu mẫu tổng hợp, không cần Ollama/API AI. Không commit `.env`.

Khởi chạy:

```powershell
python app.py
```

Mặc định server bind `127.0.0.1:5000`, debug tắt. Chỉ cấu hình `HOST=0.0.0.0` khi chủ động triển khai sau reverse proxy/firewall phù hợp. Có endpoint `/health` kiểm tra kết nối DB; chưa có bằng chứng triển khai production.

### Chạy Docker để dùng chung dữ liệu trên nhiều máy

Docker chạy một bản ứng dụng trung tâm; database SQLite, tài liệu tải lên và vector database được lưu ở các thư mục trên máy chạy Docker nên vẫn còn sau khi container khởi động lại hoặc được tạo lại. Database mới sẽ tự có dữ liệu mẫu; nếu đã có schema database, hệ thống giữ nguyên dữ liệu và không nạp lại mẫu.

1. Cài Docker Desktop, sao chép `.env.example` thành `.env`, rồi đặt `SECRET_KEY` ngẫu nhiên (ít nhất 32 ký tự). Điền thông tin tài khoản quản trị ban đầu theo hướng dẫn bên dưới; không dùng mật khẩu ví dụ hoặc đưa `.env` lên Git.
2. Từ thư mục dự án, khởi động ứng dụng:

   ```powershell
   docker compose up -d --build
   docker compose logs -f app
   ```

3. Trên máy chủ, mở `http://localhost:5000`. Trên laptop khác cùng mạng LAN, mở `http://<địa-chỉ-IP-máy-chủ>:5000`; cấu hình firewall của máy chủ để cho phép kết nối đến cổng này trên mạng riêng.

Mọi người phải truy cập cùng máy chủ/container để dùng chung dữ liệu. Chạy Compose riêng trên từng laptop tạo ra các database riêng, không tự đồng bộ. Docker cũng không tự đưa ứng dụng lên Internet; muốn truy cập ngoài LAN cần một máy chủ có thể truy cập, cùng VPN hoặc reverse proxy HTTPS đã cấu hình an toàn. Không dùng HTTP/cổng này để công khai ứng dụng trên Internet.

Nếu Ollama chạy trực tiếp trên máy chủ Windows, đổi `LLM_API_BASE_URL` trong `.env` thành `http://host.docker.internal:11434/v1/chat/completions`; bên trong container, `localhost` trỏ về container chứ không phải máy chủ.

Dữ liệu bền vững nằm trong `database`, `data/documents` và `vector_db` trên máy chủ. Sao lưu database từ container trước khi di chuyển/nâng cấp:

```powershell
docker compose exec app python -m database.backup backup --output /app/database/backups/school_assets.db
```

Giữ `.env` và bản sao lưu ở nơi an toàn khi chuyển máy; tuyệt đối không chạy `docker compose down -v` nếu muốn giữ dữ liệu. Container dùng SQLite trên một máy chủ; không khởi chạy nhiều bản ứng dụng cùng dùng file database này.

### Tạo tài khoản quản trị ban đầu

Không còn tài khoản/mật khẩu demo được tạo tự động. Đặt đủ các biến sau trong `.env` trước lần khởi động đầu tiên:

```dotenv
INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_EMAIL=admin@example.edu.vn
INITIAL_ADMIN_FULL_NAME=Quan tri vien
INITIAL_ADMIN_PASSWORD=thay-bang-mat-khau-dai-ngau-nhien
```

Mật khẩu phải có ít nhất 12 ký tự. Tài khoản chỉ được tạo nếu username chưa tồn tại; khởi động sau không ghi đè mật khẩu. Nên xóa `INITIAL_ADMIN_PASSWORD` khỏi `.env` sau khi tài khoản được tạo.

### Tạo tài khoản không phải quản lý

Có thể tạo một tài khoản kiểm kê viên (`inspector`), nhân viên (`staff`), hoặc cả hai bằng cách điền đủ nhóm biến tương ứng trong `.env` trước lần khởi động đầu tiên:

```dotenv
INITIAL_INSPECTOR_USERNAME=kiemke
INITIAL_INSPECTOR_EMAIL=kiemke@example.edu.vn
INITIAL_INSPECTOR_FULL_NAME=Nhan vien kiem ke
INITIAL_INSPECTOR_PASSWORD=thay-bang-mat-khau-dai-ngau-nhien

INITIAL_STAFF_USERNAME=nhanvien
INITIAL_STAFF_EMAIL=nhanvien@example.edu.vn
INITIAL_STAFF_FULL_NAME=Nhan vien
INITIAL_STAFF_PASSWORD=thay-bang-mat-khau-dai-ngau-nhien
```

Chỉ cần cấu hình nhóm tài khoản muốn tạo; mật khẩu mỗi tài khoản phải có ít nhất 12 ký tự. Cách tạo và bảo vệ mật khẩu áp dụng như tài khoản quản trị ban đầu. Xóa biến mật khẩu khỏi `.env` sau khi các tài khoản đã được tạo.

`SEED_DEMO_DATA=true` tự tạo dữ liệu mẫu tổng hợp chỉ khi database chưa có bảng của ứng dụng. Quá trình tạo dùng các model ORM hiện tại và tạo liên kết giữa tài sản, danh mục, phòng ban, nhân viên mẫu, kiểm kê, điều chuyển, sửa chữa và thanh lý. Các tài khoản nhân viên mẫu bị khóa và không có mật khẩu đăng nhập; hãy dùng tài khoản quản trị đã cấu hình để thao tác. Không gọi dịch vụ AI bên ngoài và không lấy dữ liệu từ database thật. Hệ thống không thêm, sửa hoặc xóa dữ liệu khi phát hiện schema ứng dụng đã tồn tại; nếu muốn chủ động nạp mẫu, chỉ làm trên database mới.

### Vai trò và nghiệp vụ chính

- `admin`: quản trị tài khoản, toàn quyền nghiệp vụ và quyết định duyệt/từ chối thanh lý.
- `manager`: thao tác nghiệp vụ và tạo báo cáo AI.
- `inspector`: thao tác kiểm kê; các luồng khác chỉ đọc.
- `staff`: chỉ đọc, ngoại trừ đổi mật khẩu của mình và AI chat.

CSRF áp dụng cho form và request thay đổi; JSON fetch cần gửi token `X-CSRFToken`. Đợt kiểm kê chụp danh sách tài sản lúc tạo và chỉ hoàn tất sau khi từng tài sản được kiểm đếm tường minh; chỉ ghi nhận “không tìm thấy” sau xác nhận của người kiểm kê. Yêu cầu sửa chữa có vòng đời riêng và đồng bộ trạng thái tài sản. Yêu cầu thanh lý ở trạng thái chờ đến khi admin quyết định; tài sản được duyệt chuyển sang `disposal`.

## Cấu hình AI

```dotenv
LLM_API_KEY=
LLM_MODEL=llama3.2
LLM_API_BASE_URL=http://localhost:11434/v1/chat/completions
LLM_TIMEOUT_SECONDS=30
LLM_MAX_PROMPT_CHARS=12000
```

Ứng dụng mặc định gọi Ollama cục bộ qua API tương thích OpenAI Chat Completions; không cần API key. Cài Ollama, tải model đã chọn (ví dụ `ollama pull llama3.2`) và đảm bảo Ollama đang chạy trước khi dùng tính năng AI. Có thể đặt `LLM_MODEL` và `LLM_API_BASE_URL` trong `.env` để dùng model hoặc endpoint tương thích khác. Đầu ra báo cáo AI được yêu cầu ở JSON và kiểm tra cấu trúc trước khi hiển thị. Chưa có xác nhận gọi thành công Ollama/model thật trong phiên kiểm tra này.

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

- [Phân tích nghiệp vụ](docs/Phan_tich.md)
- [Use Case](docs/Truong_hop_su_dung.md)
- [Kiến trúc và ERD](docs/Kien_truc_he_thong.md)
- [Phân tích khoảng trống và ưu tiên](docs/Phan_tich_khoang_trong.md)
- [Ma trận truy vết 36 nhiệm vụ](docs/Ma_tran_theo_doi_yeu_cau.md)
- [Nhật ký SDLC AI](docs/AI_nhat_ky_sdlc.md)
- [Thử nghiệm prompt](docs/AI_thi_nghiem_prompt.md)
- [Báo cáo bàn giao và kịch bản demo](docs/Bao_cao_giao_hang_cuoi.md)


