# Phân tích nghiệp vụ

## Bối cảnh và vấn đề

Trường học cần theo dõi thiết bị, đồ dùng, giá trị, phòng ban sử dụng và các thay đổi trong suốt vòng đời tài sản. Quản lý bằng bảng tính hoặc sổ rời làm tăng nguy cơ trùng mã, thất lạc lịch sử, chậm phát hiện hư hỏng và khó đối chiếu khi kiểm kê. Ứng dụng hiện tại là một web app Flask dùng SQLAlchemy và SQLite mặc định; các nội dung dưới đây phân biệt khả năng đã có với quy trình còn thiếu.

## Actor và trách nhiệm

| Actor | Trách nhiệm nghiệp vụ |
|---|---|
| Quản trị viên | Quản lý tài khoản; có toàn quyền nghiệp vụ và quyết định duyệt/từ chối thanh lý. |
| Cán bộ quản lý tài sản | Ghi nhận tài sản, danh mục, phòng ban, điều chuyển, sửa chữa, thanh lý và báo cáo. |
| Kiểm kê viên | Thực hiện kiểm đếm, ghi tình trạng thực tế và sai lệch; không có quyền sửa các luồng khác. |
| Nhân viên | Đọc dữ liệu, đổi mật khẩu của mình và sử dụng AI chat. |
| Dịch vụ AI | Thành phần hỗ trợ phân tích văn bản; không phải người dùng và không được tự cập nhật dữ liệu nghiệp vụ. |

## Quy trình nghiệp vụ đích

1. **Tiếp nhận:** nhập mã duy nhất, tên, nhóm, ngày mua, giá trị, phòng ban/vị trí, người phụ trách và tình trạng; kiểm tra bắt buộc, mã trùng, giá trị và khóa ngoại.
2. **Phân bổ/sử dụng:** tra cứu và cập nhật thông tin tài sản; điều chuyển ghi phòng ban nguồn/đích, ngày và người thực hiện. Chưa có audit log tổng quát cho mọi thay đổi.
3. **Điều chuyển:** chọn tài sản, xác nhận phòng ban nguồn khớp dữ liệu hiện tại, chọn đích và ngày/lý do; ghi lịch sử và cập nhật phòng ban trong cùng giao dịch. Luồng này hiện có tại `/transfers`.
4. **Kiểm kê:** mở đợt, chụp danh sách kỳ vọng, kiểm đếm từng tài sản, lưu tình trạng thực tế/người/thời gian/ghi chú, ghi nhận tài sản quan sát ngoài danh sách, rồi đối chiếu. Chỉ hoàn tất khi mọi tài sản kỳ vọng đã được kiểm đếm; không tự động đánh dấu thiếu.
5. **Sửa chữa:** lập yêu cầu, chuyển qua chờ/đang sửa/hoàn thành/hủy; hoàn thành cần ngày sửa, không cho yêu cầu mở trùng, trạng thái tài sản được đồng bộ. Chưa có nhật ký sự kiện bất biến.
6. **Thanh lý:** lập đề xuất; tài khoản admin mới được duyệt/từ chối. Duyệt cập nhật trạng thái tài sản, ngăn xung đột với sửa chữa và điều chuyển.
7. **Báo cáo:** tổng hợp chỉ số từ DB; báo cáo AI có thể giới hạn theo phòng ban hoặc đợt kiểm kê. Dữ liệu báo cáo bị giới hạn kích thước, LLM chỉ được gọi khi cấu hình API key và không tự ghi dữ liệu.

## Dữ liệu, xử lý và đầu ra

- **Đầu vào:** biểu mẫu người dùng; bảng tài sản, danh mục, phòng ban, kiểm kê, điều chuyển, sửa chữa, thanh lý; tài liệu chính sách cho RAG; câu hỏi và loại báo cáo.
- **Xử lý:** xác thực phiên và dữ liệu, truy vấn ORM, giao dịch cập nhật nghiệp vụ, tổng hợp chỉ số, truy xuất tài liệu RAG và (nếu cấu hình) gọi API LLM.
- **Đầu ra:** danh sách/chi tiết tài sản, lịch sử điều chuyển, chỉ số dashboard, kết quả báo cáo, câu trả lời AI kèm nguồn RAG; lỗi đầu vào phải trả thông báo an toàn.
- **Ngoại lệ:** mã trùng/khóa ngoại sai, ngày/số âm/ID không hợp lệ, DB không khả dụng, không có dữ liệu, thiếu API key, timeout/rate limit/JSON AI sai.

## Yêu cầu phi chức năng

- **Bảo mật:** không có mật khẩu mặc định, hash mật khẩu, secret qua môi trường, cookie HttpOnly/SameSite, kiểm tra quyền backend và chống CSRF. Chưa có login rate limit hoặc kiểm thử pentest.
- **Khả dụng/hiệu năng:** CRUD thường dùng phản hồi phù hợp; giới hạn kích thước payload/prompt, timeout AI; không tuyên bố SLA khi chưa đo tải.
- **Nhất quán:** khóa ngoại và cập nhật tài sản/lịch sử cùng transaction; không ghi nhận thiếu nếu chưa có kiểm đếm xác nhận.
- **Sao lưu/khôi phục:** có tiện ích SQLite kiểm tra integrity và sao chép/khôi phục sang file mới, từ chối ghi đè; chưa có lịch backup hoặc restore drill production.
- **Bảo trì/mở rộng:** tách routes/models/services, kiểm thử DB tạm và nâng cấp SQLite additive; vẫn cần migration versioned thay cho ALTER khi khởi động.
- **UX:** tiếng Việt, phản hồi rõ, trạng thái chờ/lỗi, responsive; responsive chưa được xác minh bằng browser.
- **AI/riêng tư:** gửi lượng dữ liệu tối thiểu, không gửi dữ liệu định danh không cần thiết, hiển thị nội dung AI là tham khảo, kiểm chứng số liệu và đề xuất trước khi hành động.

## Giới hạn đã biết

Tài liệu này phân biệt quy trình đã được triển khai với yêu cầu đích. Chưa xác minh provider AI live, 3 vòng thử nghiệm prompt, browser E2E, production deployment/restore drill, phân quyền theo phòng ban, audit log tổng quát, login rate limiting hoặc CRUD vị trí dạng entity. Trạng thái bằng chứng chi tiết nằm tại [TRACEABILITY_MATRIX.md](./TRACEABILITY_MATRIX.md) và [GAP_ANALYSIS.md](./GAP_ANALYSIS.md).
