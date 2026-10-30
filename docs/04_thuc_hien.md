# Báo cáo triển khai thực tế

## Nền tảng

Repository triển khai Flask + Flask-SQLAlchemy + SQLAlchemy models, Jinja templates và SQLite mặc định. Không có Django project, DRF serializer hoặc migration Django.

## Các luồng đã triển khai

- Cấu hình secret/session an toàn hơn; bootstrap admin tùy chọn, không tự tạo hoặc reset tài khoản demo.
- CRUD tài sản với validation; CRUD danh mục/phòng ban; điều chuyển có nguồn khớp và cập nhật asset/history cùng transaction.
- Kiểm kê campaign snapshot, kết quả thực tế có checker/time, ghi nhận tài sản quan sát ngoài snapshot, không tự đánh dấu thiếu và khóa sau khi đủ kết quả.
- Repair lifecycle có đồng bộ trạng thái tài sản; disposal request/decision tách biệt và giới hạn phê duyệt admin.
- Backend RBAC/CSRF, AI report theo phòng ban hoặc inventory campaign, system prompt riêng cho RAG.
- SQLite additive schema upgrade, backup/restore sang file mới với integrity check, `/health` query DB.

## Bằng chứng test

`python -m pytest -q` — **63 passed**. Suite dùng SQLite tạm. HTTP LLM được mock; đây không phải test gọi model/provider thật. Chưa chạy versioned migration, lint, type-check, browser E2E, deploy production, load test hoặc restore drill production.

## Known limitations

Chưa có migration versioned, audit log tổng quát, rate limiting, ACL theo department cho từng user hoặc Location entity. Provider AI live và ba vòng prompt experiment chưa chạy. Xem [Phan_tich_khoang_trong.md](./Phan_tich_khoang_trong.md) và [Ma_tran_theo_doi_yeu_cau.md](./Ma_tran_theo_doi_yeu_cau.md).


