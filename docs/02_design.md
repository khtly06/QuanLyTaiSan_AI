# 02 Design - Hệ thống quản lý tài sản trường học có tích hợp AI

## 1. Kiến trúc tổng thể
Client/Frontend -> Backend/API -> Database
                         |
                         v
                      AI Service

## 2. Các thực thể chính
- User
- Role
- Department
- Location
- AssetGroup
- Asset
- AssetTransfer
- InventoryCampaign
- InventoryDetail
- MaintenanceRequest
- DisposalRequest
- AIReport

## 3. Quan hệ chính
- Department 1-N Location
- AssetGroup 1-N Asset
- Location 1-N Asset
- Asset 1-N AssetTransfer
- InventoryCampaign 1-N InventoryDetail
- Asset 1-N InventoryDetail
- Asset 1-N MaintenanceRequest
- Asset 1-N DisposalRequest

## 4. Use case chính
- Đăng nhập
- Quản lý tài sản
- Điều chuyển
- Kiểm kê
- Sửa chữa
- Thanh lý
- Thống kê
- Sinh báo cáo AI

## 5. Prompt AI
System:
Bạn là trợ lý quản lý tài sản trường học. Chỉ nhận xét dựa trên dữ liệu được cung cấp. Không tự tạo số liệu hoặc tài sản không tồn tại.

User:
Dữ liệu kiểm kê: {{asset_inventory}}
Hãy trả về:
1. Tóm tắt số liệu.
2. Danh sách tài sản thiếu.
3. Danh sách tài sản hỏng.
4. Danh sách cần sửa chữa.
5. Đề xuất xử lý.

## 6. Output format AI
JSON hoặc Markdown có cấu trúc rõ ràng.
Kết quả phải có nhãn: "sinh bởi AI - tham khảo".

STATUS: PASS
NEXT_PROMPT: prompts/03_implementation_plan.md
