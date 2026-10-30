# Kế hoạch triển khai theo ưu tiên

Kế hoạch này mô tả các bước còn lại cho repository Flask hiện tại. Không phải tuyên bố các bước đã được thực hiện.

## P0 — Bảo vệ dữ liệu và cấu hình

- Bỏ tài khoản/password mặc định và reset credential khi khởi động.
- Tắt debug và bind loopback theo mặc định; bắt buộc secret trong production.
- Đảm bảo test không sử dụng DB mặc định.
- Đảm bảo transaction cho thao tác điều chuyển.

## P1 — Hoàn thiện nghiệp vụ

- Xác nhận ma trận quyền trước khi triển khai RBAC/CSRF.
- Hoàn thiện inventory details, repair/disposal state machine và danh mục/vị trí.
- Đồng bộ trạng thái dashboard, asset và phiếu nghiệp vụ.
- Thêm AI inventory report và department summary theo phạm vi quyền.

## P2 — Kiểm thử và vận hành

- Bổ sung test quyền, validation, DB rollback, API errors, inventory, repair/disposal.
- Tạo migrations có phiên bản; xác minh foreign keys và backup/restore trên bản sao.
- Thêm browser E2E, lint/type checks và kiểm thử production configuration.

## P3 — UX và tối ưu

- Xác minh responsive, cải thiện thông báo/empty states, theo dõi hiệu năng.
- Thêm health/readiness và hướng dẫn triển khai có kiểm chứng.

Trạng thái hiện tại và ưu tiên cụ thể: [Phan_tich_khoang_trong.md](./Phan_tich_khoang_trong.md).


