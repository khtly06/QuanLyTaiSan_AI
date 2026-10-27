# Phân tích khoảng trống và ưu tiên

Ngày cập nhật: 2026-10-26. Ma trận theo 36 nhiệm vụ: [TRACEABILITY_MATRIX.md](./TRACEABILITY_MATRIX.md). Chỉ đánh dấu hoàn tất khi source và test có bằng chứng; test mock không xác nhận dịch vụ ngoài hoạt động.

## Tóm tắt

Các luồng cốt lõi đã được bổ sung gồm kiểm kê có snapshot/đối chiếu, sửa chữa theo trạng thái, thanh lý có quyết định admin, CRUD danh mục/phòng ban, RBAC/CSRF, báo cáo AI theo phạm vi lựa chọn, backup/restore SQLite sang file mới và health check DB. Cần đọc các giới hạn bên dưới trước khi dùng production.

## Đã triển khai và kiểm tra bằng test

| Hạng mục | Hành vi hiện có | Bằng chứng / giới hạn |
|---|---|---|
| Khởi động và tài khoản | Không tạo/reset user demo; bootstrap admin tùy chọn một lần; secret không mặc định tĩnh; debug/bind loopback theo mặc định | Test khởi tạo và quản lý user; chưa xác minh triển khai thật |
| Điều chuyển | Kiểm tra nguồn khớp phòng ban hiện tại, đích hợp lệ, status cho phép; cập nhật asset và history cùng transaction; ghi người thực hiện | Test transfer; chưa có audit log bất biến cho toàn hệ thống |
| Kiểm kê | Snapshot tài sản chưa thanh lý; ghi tình trạng thực tế, checker/thời gian, ghi chú; quan sát asset ngoài snapshot; không tự đánh dấu thiếu; khóa khi hoàn tất | Test snapshot, chênh lệch, thiếu xác nhận và khóa campaign |
| Sửa chữa | Yêu cầu mới luôn pending; ngăn phiếu mở trùng; cập nhật trạng thái/chi phí/ngày; đồng bộ trạng thái tài sản | Test vòng đời và invalid transitions; không có event log lịch sử bất biến |
| Thanh lý | Yêu cầu chờ quyết định; chỉ admin duyệt/từ chối; duyệt đặt tài sản `disposal`; chặn xung đột repair/transfer | Test quyền và trạng thái; không phải quy trình phê duyệt nhiều cấp |
| Danh mục/phòng ban | Tạo/sửa/xóa; xử lý trùng; từ chối xóa khi đang được tham chiếu | Test CRUD/error cases; vị trí vẫn là text tự do |
| Quyền và CSRF | Admin/manager/inspector/staff có quyền backend khác nhau; form/fetch mutation cần CSRF | Test role và CSRF; chưa có login rate limit hoặc review bảo mật độc lập |
| AI report | Hỗ trợ overview, department, repair, disposal và inventory campaign; inventory phân biệt thiếu thực tế với chưa kiểm đếm; giới hạn dữ liệu gửi | Test dữ liệu/scoping/validation; chưa gọi provider thật; chưa có ACL department-per-user |
| Database/health | SQLite FK bật; nâng cấp schema cũ theo hướng additive; `/health` query DB; backup/restore integrity-checked và không ghi đè file đích | Test DB tạm; schema upgrade chưa được version hóa; chưa restore drill production |

## Còn mở — cần xử lý trước production

1. **Migration và vận hành dữ liệu:** chuyển từ startup additive SQL sang Alembic/versioned migrations; xác minh rollout, rollback và tương thích DB production.
2. **Bảo mật tài khoản:** thêm login rate limiting, chính sách session/HTTPS trong reverse proxy, logging/monitoring và đánh giá bảo mật độc lập.
3. **Auditability:** thêm audit log bất biến cho thay đổi tài sản, quyết định, dữ liệu người thao tác và thời điểm; hiện các workflow chỉ lưu một số trường actor.
4. **Phạm vi truy cập:** nếu tổ chức cần cách ly dữ liệu, bổ sung quan hệ user-phòng-ban và enforce ACL xuyên suốt dashboard, route, report và AI.
5. **Danh mục vị trí:** thay `Asset.location` text bằng entity/quan hệ nếu cần quản lý chuẩn hóa, phân quyền hoặc báo cáo location.
6. **Chống cạnh tranh trạng thái:** cân nhắc transaction/row locking hoặc optimistic concurrency cho thao tác đồng thời trên cùng asset; test rollback DB hiện tại chưa bao phủ mọi trường hợp production.

## Còn mở — kiểm chứng và sản phẩm

- Chưa có gọi LLM provider thật, ba vòng prompt experiment trên cùng fixture, đánh giá chất lượng/model hoặc xác minh chi phí/retention dữ liệu ngoài.
- Chưa có browser E2E, kiểm tra responsive/khả năng truy cập, load test, coverage hoặc lint/type-check trong lần xác minh này.
- Chưa có production deployment, HTTPS/reverse proxy verification, monitoring, backup automation hoặc restore drill.
- RAG có prompt phân tách system/user, nhưng cần kiểm chứng nguồn tài liệu, nội dung thực tế và behavior với provider trước khi tuyên bố chất lượng.
- Dashboard/AI recommendations cần người có thẩm quyền đối chiếu dữ liệu; AI không tự phê duyệt hay ghi dữ liệu nghiệp vụ.

## Demo trung thực

Có thể demo kiểm kê với xác nhận người dùng, workflow repair/disposal, các quyền backend, CRUD danh mục/phòng ban, điều chuyển, health check và báo cáo DB/AI. Khi thiếu API key, report vẫn cung cấp metrics thực tế và thông báo không có phân tích model. Không tuyên bố provider live, migration versioned, audit log đầy đủ, deployment production hoặc restore production đã được kiểm chứng.
