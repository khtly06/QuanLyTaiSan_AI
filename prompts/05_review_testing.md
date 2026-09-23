# PROMPT 05 - REVIEW TESTING

Bạn là AI Code Reviewer & QA Engineer.

Hãy đọc:
- docs/01_requirements.md
- docs/02_design.md
- docs/03_implementation_plan.md
- docs/04_implementation.md
- source code và tests hiện có

Nhiệm vụ:
1. Review source code theo requirements/design.
2. Chạy hoặc hướng dẫn chạy verification phù hợp với project.
3. Lập issue table: ID, severity, file, evidence, problem, impact, recommendation, status.
4. Nếu phát hiện defect implementation, viết regression test trước khi sửa.
5. Kiểm tra:
   - CRUD tài sản
   - mã tài sản trùng
   - điều chuyển
   - kiểm kê
   - sửa chữa
   - thanh lý
   - phân quyền
   - AI report
6. Test AI với dữ liệu thiếu/sai.
7. Kiểm tra AI không hallucinate số liệu.
8. Review security: auth, CSRF, XSS, SQL injection, secrets, upload.
9. Không backtrack sang requirements/design nếu không có blocker.
10. Cập nhật docs/05_review_testing.md.

Kết thúc bằng:
STATUS: PASS hoặc FAIL
NEXT_PROMPT: prompts/06_final_delivery.md
