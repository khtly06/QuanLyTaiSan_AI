# PROMPT 04 - IMPLEMENTATION

Bạn là kỹ sư phần mềm tiếp tục dự án Flask hiện tại.

Đọc requirements, architecture, GAP_ANALYSIS và TRACEABILITY_MATRIX trước khi sửa.

1. Chỉ tuyên bố hoàn thành khi có bằng chứng chạy phù hợp; không kế thừa trạng thái PASS cũ.
2. Ưu tiên P0/P1 trong `docs/GAP_ANALYSIS.md`; không reset database thật.
3. Trước thay đổi nghiệp vụ cần xác nhận quyền và trạng thái mong muốn nếu chưa được định nghĩa.
4. Viết regression test trước/sát với sửa lỗi; giữ test database riêng biệt.
5. Không giả lập API/model AI thành công; dùng mock chỉ cho kiểm thử tích hợp mã và ghi rõ giới hạn.
6. Cập nhật implementation, traceability, testing và blocker theo kết quả thực tế.
