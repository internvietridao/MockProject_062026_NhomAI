# 🩺 AI Expert Evaluator Prompt: Đánh giá chất lượng mô hình Fine-tuned Chatbot Y khoa

> **Hướng dẫn sử dụng:** 
> 1. Truy cập vào giao diện web của các AI Agent mạnh như **ChatGPT (GPT-4o)**, **Claude 3.5 Sonnet**, hoặc **Gemini 1.5 Pro**.
> 2. Đính kèm (upload) file kết quả kiểm thử `evaluation_results.csv` của bạn.
> 3. Copy toàn bộ nội dung Prompt bên dưới và gửi cho AI Agent.

---

## Nội dung Prompt sao chép (Copy-paste):

```markdown
Chào bạn, tôi vừa thực hiện fine-tune một mô hình ngôn ngữ lớn (Qwen-0.5B) chuyên về lĩnh vực y tế Hoa Kỳ và quản lý viện dưỡng lão (Nursing Home Management). 

Tôi gửi kèm cho bạn file CSV kết quả kiểm thử mang tên `evaluation_results.csv`.
File này chứa dữ liệu chạy thử nghiệm trên tập Test với cấu trúc các cột:
- `question`: Câu hỏi y khoa / nghiệp vụ vận hành viện dưỡng lão.
- `reference`: Câu trả lời chuẩn (do chuyên gia biên soạn hoặc trích xuất từ tài liệu chuẩn).
- `prediction`: Câu trả lời thực tế do mô hình đã fine-tune sinh ra.
- `rouge1`, `rouge2`, `rougeL`, `bleu`: Các điểm số so khớp từ ngữ tự động.

Với vai trò là một **Chuyên gia Y tế cao cấp Hoa Kỳ** kiêm **Chuyên gia Đánh giá Mô hình Ngôn ngữ Lớn (LLM Evaluator)**, bạn hãy phân tích và viết một báo cáo đánh giá chất lượng mô hình theo các yêu cầu sau:

### 1. Phân tích thống kê tổng quan:
- Tính điểm trung bình cộng của các cột `rouge1`, `rougeL` và giải thích ý nghĩa các điểm số này đối với bài toán hỏi đáp y khoa.
- Cho biết tại sao điểm số `bleu` trong file lại hầu hết bằng 0.0 hoặc rất thấp, liệu điều này có đồng nghĩa với việc câu trả lời của mô hình hoàn toàn vô giá trị không? Giải thích về mặt kỹ thuật đo lường văn bản.

### 2. Đánh giá chất lượng nội dung y học (Medical Quality Audit):
Hãy đọc và so sánh ngẫu nhiên hoặc lựa chọn ra **5 cặp mẫu tiêu biểu** trong tệp dữ liệu (đặc biệt là các câu có điểm ROUGE trung bình, hoặc các câu hỏi phức tạp về chăm sóc bệnh nhân / quy định Title 22 / MDS 3.0) để nhận xét chi tiết:
- **Độ chính xác Y khoa (Medical Accuracy & Safety):** Mô hình có bịa đặt (hallucinate) thông tin y tế nguy hiểm nào không? Các thuật ngữ y tế/vận hành sử dụng có chuẩn xác không?
- **Độ đầy đủ (Completeness):** Mô hình đã bao quát được bao nhiêu phần trăm ý cốt lõi từ câu trả lời chuẩn?
- **Giọng điệu và Định dạng (Tone & Formatting):** Mô hình trả lời có trực diện, ngắn gọn, chuyên nghiệp và tránh các câu chào hỏi thừa thãi (conversational fluff) đúng chuẩn ChatML hỗ trợ không?

### 3. Đánh giá điểm mạnh và điểm yếu (Pros & Cons):
- Mô hình này làm tốt nhất ở những dạng câu hỏi nào? (Ví dụ: Định nghĩa, liệt kê quy trình, dịch vụ y khoa...).
- Điểm yếu lớn nhất hiện tại của mô hình là gì? (Ví dụ: Sự lặp từ, trả lời thiếu chi tiết, nhầm lẫn khái niệm phức tạp...).

### 4. Đề xuất cải tiến kỹ thuật (Actionable Recommendations):
Dựa trên các lỗi cụ thể mà bạn tìm thấy trong file CSV, hãy đề xuất các phương án cải tiến thiết thực cho chu kỳ huấn luyện tiếp theo (ví dụ: Thay đổi prompt template, tăng Sequence Length, điều chỉnh dataset, tăng kích thước model nền từ 0.5B lên các bản lớn hơn như Llama 3B hoặc Qwen 7B, hoặc bổ sung hệ thống RAG để bù đắp kiến thức quy chế...).

Hãy viết báo cáo bằng **Tiếng Việt**, trình bày rõ ràng, sử dụng các bảng số liệu, danh sách gạch đầu dòng để dễ theo dõi.
```
