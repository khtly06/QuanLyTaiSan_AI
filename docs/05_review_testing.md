# Review và kiểm thử

## Kết quả xác minh

Chạy bằng Python 3.12 trên workspace; test dùng SQLite tạm, không truy cập database mặc định.

- `python -m pytest -q`: **63 passed**.
- Phạm vi test gồm bootstrap/config, login và role/CSRF, asset validation, CRUD danh mục/phòng ban, điều chuyển, kiểm kê, repair/disposal state transitions, AI report/data validation, LLM HTTP mock, RAG, SQLite upgrade, backup/restore và health endpoint.
- Test LLM/RAG mock request; không chứng minh provider/model bên ngoài hoạt động hoặc chất lượng prompt.
- Chưa chạy browser E2E, lint/type-check, coverage, load test, production deployment hoặc production restore drill.

## Review findings

| Hạng mục | Tình trạng |
|---|---|
| Cấu hình khởi động | Đã bỏ user demo auto-reset và secret mặc định tĩnh; test bootstrap/config. Cần cấu hình HTTPS/reverse proxy thật. |
| Kiểm kê | Có snapshot, kết quả thực tế, người/thời điểm kiểm, missing chỉ khi xác nhận, observation ngoài snapshot và khóa campaign; test workflow. |
| Repair/disposal | Có state transitions, đồng bộ asset, quyền admin cho quyết định disposal và kiểm tra xung đột; test workflow. |
| Quyền và CSRF | Có role enforcement backend và CSRF; test quyền/CSRF. Chưa có rate limiting hoặc audit trail tổng quát. |
| AI report | Có department/campaign scope, giới hạn payload và schema validation; test bằng dữ liệu cục bộ/mock. Provider live và 3 vòng prompt chưa chạy. |
| Database và vận hành | Có SQLite additive upgrade, FK enforcement, backup/restore file mới và `/health`; chưa có migrations versioned, automation hoặc production drill. |

Đây là review theo source và test, không phải chứng nhận bảo mật. Xem [TRACEABILITY_MATRIX.md](./TRACEABILITY_MATRIX.md) cho trạng thái từng tiêu chí và [GAP_ANALYSIS.md](./GAP_ANALYSIS.md) cho việc còn mở.
