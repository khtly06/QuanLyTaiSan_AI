# 04 Implementation - Hệ thống quản lý tài sản trường học có tích hợp AI

## Mục tiêu triển khai
Triển khai source code theo `docs/01_requirements.md`, `docs/02_design.md` và `docs/03_implementation_plan.md`.

## Module cần triển khai
- Authentication và phân quyền.
- CRUD tài sản.
- CRUD nhóm tài sản.
- CRUD phòng ban/vị trí.
- Điều chuyển tài sản.
- Kiểm kê.
- Sửa chữa.
- Thanh lý.
- Thống kê.
- AI báo cáo kiểm kê.

## Kiểm thử bắt buộc
- Mã tài sản không trùng.
- Điều chuyển chỉ áp dụng cho tài sản hợp lệ.
- Kiểm kê không chấp nhận tài sản không tồn tại.
- Thanh lý kiểm tra trạng thái.
- AI không tự tạo số liệu.
- AI xử lý dữ liệu thiếu/sai.

## Verification tối thiểu
- Chạy kiểm tra framework.
- Kiểm tra migration/schema.
- Chạy test backend.
- Build frontend.
- Kiểm tra secret, validation, phân quyền.

## Source code đã thay đổi
- `backend/school_assets`: cấu hình Django, URL, dashboard view.
- `backend/assets`: AssetGroup, Asset, serializer và CRUD API.
- `backend/departments`: Department, Location và CRUD API.
- `backend/inventory`, `transfers`, `maintenance`, `disposals`: models, serializers và API nghiệp vụ.
- `backend/ai_reports`: report model, deterministic report service và endpoint kiểm kê.
- `frontend/templates`, `frontend/static`: dashboard Bootstrap 5.
- `tests/test_workflows.py`: test nghiệp vụ và AI.

## Traceability
- FR-ASSET/FR-DEPT: models và ModelViewSet CRUD.
- FR-TRANSFER: chặn tài sản mất/đã thanh lý và vị trí nguồn đích trùng.
- FR-INVENTORY: khóa ngoại asset/campaign và ràng buộc duy nhất.
- FR-MAINTENANCE/FR-DISPOSAL: request models và API; thanh lý chặn tài sản đã thanh lý.
- FR-AI-REPORT: report chỉ tổng hợp input hợp lệ, không tạo tài sản hoặc số liệu ngoài input.

## Verification
- `manage.py check`: PASS.
- `manage.py makemigrations`: PASS, migration initial cho 7 module.
- `manage.py migrate`: PASS trên SQLite.
- `python -m pytest`: PASS, 5 tests.
- Security: CSRF middleware, ORM chống SQL injection, secret lấy từ environment; production cần thay secret và đặt `DEBUG=False`.

## Blocker / limitation
- AI hiện là deterministic local service, chưa gọi LLM bên ngoài.
- Phân quyền chi tiết theo actor và các màn hình CRUD mở rộng cần tiếp tục hoàn thiện.

STATUS: PASS
NEXT_PROMPT: prompts/05_review_testing.md
