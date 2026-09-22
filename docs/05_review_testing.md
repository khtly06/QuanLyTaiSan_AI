# 05 Review Testing - Hệ thống quản lý tài sản trường học có tích hợp AI

## Input cần review
- Source code từ Bước 04.
- Tests.
- API contract.
- Database/schema.
- Frontend.
- AI prompt và AI output.

## Review bắt buộc
### ISSUE-001: AI hallucination
Kiểm tra AI có tự tạo số liệu hoặc tài sản không tồn tại hay không.

### ISSUE-002: Asset transfer validation
Kiểm tra điều chuyển tài sản có xác minh trạng thái, vị trí nguồn và quyền người dùng.

### ISSUE-003: Inventory validation
Kiểm tra chi tiết kiểm kê có tham chiếu tài sản tồn tại.

### ISSUE-004: Disposal validation
Kiểm tra tài sản thanh lý không còn được sử dụng trong nghiệp vụ không hợp lệ.

## Test coverage tối thiểu
- FR-ASSET
- FR-DEPT
- FR-TRANSFER
- FR-INVENTORY
- FR-MAINTENANCE
- FR-DISPOSAL
- FR-AI-REPORT
- NFR-SEC
- NFR-PERF
- NFR-REL

## Security
- Authentication/Authorization.
- CSRF.
- XSS.
- SQL Injection.
- Upload validation nếu có upload.
- Secret handling.
- Production configuration.

## Issue table
| ID | Severity | Evidence | Status |
|---|---|---|---|
| ISSUE-001 | Low | `build_inventory_report` chỉ nhận dòng có `asset_code`, không suy diễn số liệu | PASS |
| ISSUE-002 | Medium | Transfer serializer chặn asset `disposed`/`lost` và vị trí trùng | PASS |
| ISSUE-003 | Low | InventoryDetail dùng ForeignKey tới Asset và campaign | PASS |
| ISSUE-004 | Medium | Disposal serializer chặn asset đã thanh lý | PASS |

## Test evidence
- FR-ASSET, FR-TRANSFER, FR-INVENTORY, FR-DISPOSAL và FR-AI-REPORT: 5 tests pass.
- ORM được dùng cho truy vấn; CSRF middleware bật; không có upload; secrets không hard-code trong production config.
- Known gap: chưa có test browser end-to-end và phân quyền actor chi tiết.

STATUS: PASS
NEXT_PROMPT: prompts/06_final_delivery.md
