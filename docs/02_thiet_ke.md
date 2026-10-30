# Thiết kế hệ thống

Thiết kế phải bám sát Flask/SQLAlchemy hiện tại; không phải thiết kế Django. Chi tiết kiến trúc và ERD nằm tại [Kien_truc_he_thong.md](./Kien_truc_he_thong.md), Use Case tại [Truong_hop_su_dung.md](./Truong_hop_su_dung.md).

## Các thực thể đang triển khai

`User`, `Category`, `Department`, `Asset`, `Inventory`, `InventoryDetail`, `Transfer`, `Repair`, `Disposal`.

## Quan hệ hiện có

- Category 1-N Asset; Department 1-N Asset.
- Asset 1-N Transfer/Repair/Disposal/InventoryDetail.
- Inventory 1-N InventoryDetail.
- Department 1-N Transfer ở vai trò nguồn và đích.

Location hiện là chuỗi trên Asset; chưa có Role/Location/AuditLog/AIReport entity riêng. `database/schema.sql` không phải migration được quản lý/versioned.

## Kiến trúc/AI

Browser → Flask routes → SQLAlchemy/DB. RAG đọc tài liệu trong `data/documents`; LLM server-side qua endpoint Chat Completions tương thích OpenAI khi key được cấu hình. Dữ liệu báo cáo được truy vấn từ DB trước khi tạo prompt; JSON do LLM trả về được parse/kiểm tra key bắt buộc.

## Giới hạn

Chưa hoàn tất inventory details, quy trình trạng thái repair/disposal, RBAC/CSRF đầy đủ, phân quyền tóm tắt theo department, report theo inventory campaign, migration versioned và test live provider. Xem [Phan_tich_khoang_trong.md](./Phan_tich_khoang_trong.md).


