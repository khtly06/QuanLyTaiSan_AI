# Nhật ký AI trong SDLC

## Ghi nhận phiên hoàn thiện

- **Phạm vi:** đối chiếu yêu cầu 36 nhiệm vụ; kiểm tra Flask app, routes/models, config, templates, tests và tài liệu; triển khai các luồng còn thiếu có thể xác minh cục bộ; không reset hoặc sửa database mặc định.
- **Phát hiện ban đầu:** tài liệu trước có claim không khớp source Flask; startup có hành vi tài khoản mặc định không an toàn; chuyển phòng ban không đồng bộ asset; LLM service chưa gọi API; kiểm kê/repair/disposal chỉ mới có một phần.
- **Đã triển khai:** inventory snapshot và kết quả kiểm đếm rõ ràng; repair/disposal state transitions; category/department CRUD; vai trò/CSRF và user management; report theo department/campaign; prompt RAG tách biệt; SQLite additive upgrade, backup/restore file mới, health endpoint; validation đầu vào và cập nhật tài liệu.
- **Xác minh:** `python -m pytest -q` — **63 passed** trên SQLite tạm. Có test mock HTTP cho LLM, không có API provider live. Test backup/restore chạy trên dữ liệu tạm; không có production restore drill.
- **Chưa xác minh:** ba vòng prompt experiment live, browser E2E, lint/type-check/coverage, load test, production deploy, login rate limit, migration versioned và security certification độc lập.
- **Kết luận:** workflow và test được bổ sung đáng kể nhưng dự án chưa đủ cơ sở để tuyên bố hoàn tất production. Xem [TRACEABILITY_MATRIX.md](./TRACEABILITY_MATRIX.md) và [GAP_ANALYSIS.md](./GAP_ANALYSIS.md).

## Ranh giới bằng chứng

Không ghi output AI giả hoặc suy diễn chất lượng model từ mock. Không đưa dữ liệu sản xuất tới provider. Các test chứng minh nhánh ứng dụng đã chạy trong fixture, không thay thế xác minh provider, deployment, bảo mật độc lập hoặc khôi phục production.
