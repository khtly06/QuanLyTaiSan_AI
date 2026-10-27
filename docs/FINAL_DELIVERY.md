# Báo cáo bàn giao kỹ thuật

## Kết quả

Đã hoàn thiện một số luồng nghiệp vụ và kiểm soát nền tảng, nhưng chưa thể kết luận toàn bộ yêu cầu 36 nhiệm vụ hoặc triển khai production đã hoàn tất. Chi tiết theo tiêu chí: [TRACEABILITY_MATRIX.md](./TRACEABILITY_MATRIX.md). Các giới hạn và ưu tiên còn lại: [GAP_ANALYSIS.md](./GAP_ANALYSIS.md).

## Thay đổi chính

- Hoàn thiện kiểm kê campaign snapshot: ghi kết quả thực tế, người/thời điểm kiểm, ghi chú sai lệch, tài sản quan sát ngoài snapshot; không tự kết luận thiếu; chỉ khóa khi đã kiểm đếm đủ.
- Hoàn thiện vòng đời repair/disposal; đồng bộ trạng thái tài sản, chặn trạng thái xung đột và chỉ admin được duyệt/từ chối thanh lý.
- Bổ sung/hoàn thiện RBAC, CSRF, quản lý tài khoản an toàn, xác thực đầu vào asset và CRUD danh mục/phòng ban.
- Điều chuyển cập nhật asset và lịch sử cùng transaction, ghi người thực hiện và ngày.
- Báo cáo AI chọn được phòng ban hoặc inventory campaign; prompt RAG tách system và coi tài liệu truy xuất là dữ liệu không đáng tin cậy.
- Bổ sung SQLite additive schema upgrade, FK enforcement, backup/restore integrity-checked sang file mới và `/health`.
- Cập nhật README, phân tích nghiệp vụ, kiến trúc, review, gap report và ma trận truy vết theo bằng chứng hiện tại.

## Kiểm thử có bằng chứng

Lệnh: `python -m pytest -q`  
Kết quả: **63 passed**. Test suite sử dụng SQLite tạm; database mặc định không được tạo hoặc sửa trong quá trình test. Test LLM dùng HTTP mock; không có provider live call.

Đã chạy test upgrade SQLite và backup/restore trên file tạm. Chưa chạy browser E2E, lint/type-check, coverage, load test, production deployment, production restore drill hoặc ba vòng prompt experiment với provider thật.

## Hạn chế cần xử lý trước production

- Chưa có Alembic/versioned migrations; nâng cấp schema hiện tại chỉ additive trong startup.
- Chưa có audit log bất biến tổng quát, login rate limiting, hoặc phân quyền dữ liệu theo phòng ban cho từng user.
- `Asset.location` vẫn là free text; chưa có entity vị trí.
- Cần kiểm thử đồng thời/rollback trên database production phù hợp và kiểm tra cấu hình HTTPS/session/reverse proxy.
- Chưa xác minh provider AI thật, chất lượng đề xuất, chi phí, giới hạn lưu trữ dữ liệu hoặc prompt injection trên tập tài liệu thực.
- Chưa xác minh responsive/accessibility và quy trình backup tự động/restore drill.

## Kịch bản demo trung thực

1. Bootstrap admin từ biến môi trường; thử login hợp lệ và sai.
2. Tạo/tìm/sửa tài sản và kiểm tra các input không hợp lệ.
3. Ghi nhận điều chuyển; xác minh phòng ban và người thực hiện trong lịch sử.
4. Tạo inventory campaign, nhập kết quả quan sát, xác nhận tài sản thiếu chỉ khi kiểm kê viên chọn rõ ràng, rồi hoàn tất campaign.
5. Tạo repair request và cập nhật trạng thái; gửi disposal request, xác nhận staff/manager không thể quyết định, rồi dùng admin để duyệt/từ chối.
6. Kiểm tra report DB-scoped và endpoint `/health`; khi chưa cấu hình API key, chỉ trình bày thống kê database và thông báo AI chưa được cấu hình.
7. Demo backup/restore chỉ trên database tạm, không dùng dữ liệu thật.

## Việc tiếp theo

1. Chuyển schema upgrades sang versioned migrations và kiểm thử nâng cấp/rollback.
2. Bổ sung rate limiting, audit log và ACL theo department nếu yêu cầu tổ chức cần.
3. Với API key và phê duyệt phù hợp, chạy ba vòng prompt trên fixture tổng hợp cố định; không dùng dữ liệu nhạy cảm.
4. Chạy browser E2E, security review độc lập, deployment rehearsal và restore drill trên bản sao.
