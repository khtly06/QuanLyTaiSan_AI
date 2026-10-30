# PROMPT 05 - REVIEW / TESTING

Review đúng source Flask/SQLAlchemy hiện tại và đọc `docs/Ma_tran_theo_doi_yeu_cau.md`, `docs/Phan_tich_khoang_trong.md`.

1. Không dựa trên tên route/template; xác minh đường chạy và dữ liệu.
2. Tập trung xác minh test chưa bao phủ: quyền/CSRF, inventory details, repair/disposal, filter và AI scope.
3. Với defect xác định được, tạo regression test rồi sửa trong phạm vi an toàn.
4. Không gọi dịch vụ thật khi chưa có credentials/approval; không bịa output.
5. Chạy test và ghi lệnh/kết quả thực tế, giới hạn và trạng thái yêu cầu trong docs.
6. Không tuyên bố security certification, PASS tổng thể hoặc coverage chưa đo.

