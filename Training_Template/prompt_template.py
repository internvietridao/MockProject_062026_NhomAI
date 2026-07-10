"""
prompt_template.py
-------------------
Module xây dựng prompt (messages) cho chatbot RAG.
Dùng chung ở CẢ 2 giai đoạn:
  1. Lúc build train.jsonl (build_train_dataset.py) -> để model train đúng
     với format sẽ gặp lúc chạy thật.
  2. Lúc inference thật -> ghép chunk từ vector DB + câu hỏi user.
"""

SYSTEM_PROMPT = (
    "Bạn là trợ lý AI tư vấn y tế. Chỉ được trả lời dựa trên NGỮ CẢNH được cung cấp. "
    "Nếu ngữ cảnh không chứa thông tin liên quan đến câu hỏi, hãy trả lời rằng "
    "bạn không có đủ dữ liệu để trả lời, không được tự bịa thông tin."
)


def build_prompt(chunks: list[str], question: str, system_prompt: str = SYSTEM_PROMPT) -> list[dict]:
    """
    Ghép các đoạn ngữ cảnh (đã được vector DB tìm ra) với câu hỏi của user
    thành 1 danh sách messages sẵn sàng đưa vào LLM.

    Args:
        chunks: danh sách các đoạn văn bản liên quan nhất (RAG đã chọn ra)
        question: câu hỏi gốc của user
        system_prompt: chỉ dẫn hành vi cho chatbot

    Returns:
        list messages theo format chuẩn [{"role": ..., "content": ...}, ...]
        (chưa có message "assistant" - phần đó do model sinh ra lúc inference,
        hoặc do build_train_dataset.py thêm vào lúc build data train)
    """
    context = "\n\n---\n\n".join(chunk.strip() for chunk in chunks if chunk.strip())

    user_content = f"NGỮ CẢNH:\n{context}\n\nCÂU HỎI:\n{question.strip()}"

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]