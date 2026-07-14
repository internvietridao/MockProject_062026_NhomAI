# AI Chatbot - Nursing Home Management Assistant

Hệ thống AI Chatbot chuyên biệt hỗ trợ quản lý viện dưỡng lão tại Mỹ (Skilled Nursing Facility). Dự án tích hợp công nghệ Fine-tuning LLM và hệ thống RAG (Retrieval-Augmented Generation) để trả lời các câu hỏi về y tế, quy trình chăm sóc điều dưỡng, và quy định pháp lý (California Title 22, OSHA, MDS 3.0 RAI).

---

## 📂 Tổng quan cấu trúc thư mục dự án

```
├── analysis_preprocessing/ # Thư mục xử lý và chuẩn hóa dữ liệu từ XML sang JSON
├── data_clean/             # Chứa dữ liệu sạch cuối cùng đã chuẩn hóa (Fine-tune JSON & RAG Markdown)
├── train/                  # Component cấu hình, mã nguồn huấn luyện model LLM (QLoRA)
├── LLM-as-Judge/           # Chứa các báo cáo đánh giá chất lượng mô hình bằng LLM-as-a-judge (như Qwen-0.5B.md...)
└── README.md               
```

*Lưu ý: Bên trong mỗi thư mục con ở trên đều có file `README.md` riêng biệt mô tả chi tiết cấu trúc file, script vận hành và hướng dẫn chạy cho module đó.*
