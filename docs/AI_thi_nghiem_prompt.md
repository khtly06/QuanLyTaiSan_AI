# Thử nghiệm prompt AI

## Tình trạng

Chưa có lần gọi LLM thật nào được xác nhận trong phiên rà soát. Không ghi đầu ra giả hoặc suy diễn chất lượng model từ test mock. Vì vậy ba vòng thử nghiệm live đang ở trạng thái **CHƯA XÁC MINH**; cần API key hợp lệ và phê duyệt gửi dữ liệu tới nhà cung cấp trước khi chạy.

## Bộ dữ liệu cố định đề xuất

Dùng fixture test tổng hợp cố định, không dùng dữ liệu thật:

```json
{
  "report_type": "overview",
  "stats": {
    "total_assets": 1,
    "active_assets": 1,
    "repair_assets": 0,
    "disposal_assets": 0,
    "total_value": 1000
  }
}
```

Đây là fixture test của suite, không phải số liệu trường học. Cả ba vòng phải dùng đúng dữ liệu trên; lưu model, timestamp, prompt hash, HTTP status, output nguyên bản đã loại dữ liệu nhạy cảm và đánh giá trước khi ghi PASS.

## Vòng thử nghiệm

| Vòng | Prompt | Đầu vào | Đầu ra thực tế | Đánh giá/lỗi | Trạng thái |
|---|---|---|---|---|---|
| 1 — baseline | `prompts/ai_report_user.md` cùng chỉ dẫn system hiện hành | Fixture cố định ở trên | Chưa chạy | Cần kiểm tra số liệu không bị thay đổi và JSON hợp lệ | CHƯA XÁC MINH |
| 2 — ràng buộc | Giữ fixture; kiểm tra system prompt nhấn mạnh phân biệt dữ kiện/suy luận và không tạo số | Fixture cố định ở trên | Chưa chạy | Chỉ ghi thay đổi nếu có output live và đánh giá so sánh | CHƯA XÁC MINH |
| 3 — biên | Dùng cùng fixture về tài sản nhưng kiểm tra phản hồi thiếu dữ liệu cho trường lịch sử/kiểm kê không được cung cấp | Fixture cố định ở trên | Chưa chạy | Không được tự bịa lịch sử, tài sản thiếu hoặc chênh lệch | CHƯA XÁC MINH |

Test hiện chạy bằng mock HTTP xác minh request timeout, giới hạn prompt, xử lý response sai và API key thiếu; đó là test tích hợp mã, không phải thử nghiệm model/prompt live.


