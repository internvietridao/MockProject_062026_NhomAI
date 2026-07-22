"""
prompt_template.py
-------------------
Module xây dựng prompt (messages) cho chatbot.
Dùng chung ở CẢ 2 giai đoạn:
  1. Lúc build train/val/test (pipeline/build_train_dataset.py) -> để model
     train đúng với format sẽ gặp lúc chạy thật.
  2. Lúc inference thật (pipeline/chat.py) -> ghép chunk từ vector DB + câu
     hỏi user.

Hỗ trợ 2 chế độ:
  - CÓ RAG (chunks không rỗng): model chỉ được trả lời dựa trên ngữ cảnh
    được cung cấp.
  - KHÔNG RAG (chunks rỗng/None): model trả lời bằng kiến thức y tế đã học
    lúc fine-tune, không có ngữ cảnh nào được đưa vào. Đây là chế độ mặc
    định hiện tại (xem src/config.py -> USE_RAG) vì chưa nối vector DB thật.
"""

SYSTEM_PROMPT_RAG = (
    "Bạn là trợ lý AI tư vấn y tế. Bạn PHẢI tuân thủ nghiêm ngặt các quy tắc sau:\n"
    "1. CHỈ được dùng thông tin có trong phần NGỮ CẢNH bên dưới để trả lời. "
    "KHÔNG được dùng bất kỳ kiến thức nào khác ngoài ngữ cảnh, kể cả khi bạn "
    "biết thông tin đó từ nơi khác.\n"
    "2. KHÔNG được tự thêm tên tổ chức, con số, tên riêng, hay chi tiết nào "
    "không xuất hiện nguyên văn hoặc gần nguyên văn trong NGỮ CẢNH.\n"
    "3. Khi trả lời, ưu tiên diễn đạt lại (paraphrase) sát nội dung ngữ cảnh, "
    "không suy diễn hay mở rộng thêm.\n"
    "4. Nếu NGỮ CẢNH không chứa đủ thông tin để trả lời câu hỏi, PHẢI trả "
    "lời đúng câu: \"Ngữ cảnh được cung cấp không có đủ thông tin để trả "
    "lời câu hỏi này.\" -- KHÔNG được cố bịa ra câu trả lời."
)

SYSTEM_PROMPT_NO_RAG = (
    "Bạn là trợ lý AI tư vấn y tế. Hãy trả lời câu hỏi bằng kiến thức y tế mà "
    "bạn đã được huấn luyện. Nếu không chắc chắn về thông tin, hãy nói rõ là "
    "bạn không chắc, không được tự bịa thông tin."
)


def build_prompt(chunks, question: str, system_prompt: str = None) -> list:
    """
    Ghép câu hỏi của user thành messages sẵn sàng đưa vào LLM. Nếu có
    `chunks` (đoạn ngữ cảnh do vector DB trả về, chế độ RAG), sẽ ghép thêm
    phần NGỮ CẢNH vào; nếu không (None hoặc []), chỉ có CÂU HỎI (chế độ
    không-RAG, model trả lời bằng kiến thức đã học lúc fine-tune).

    Args:
        chunks: danh sách các đoạn văn bản liên quan nhất (RAG đã chọn ra).
                Truyền None hoặc [] để dùng chế độ không-RAG.
        question: câu hỏi gốc của user
        system_prompt: chỉ dẫn hành vi cho chatbot. Nếu không truyền, tự
                       chọn theo có/không có chunks.

    Returns:
        list messages theo format chuẩn [{"role": ..., "content": ...}, ...]
        (chưa có message "assistant" - phần đó do model sinh ra lúc inference,
        hoặc do pipeline/build_train_dataset.py thêm vào lúc build data train)
    """
    chunks = [c for c in (chunks or []) if c and c.strip()]
    use_rag = len(chunks) > 0

    if system_prompt is None:
        system_prompt = SYSTEM_PROMPT_RAG if use_rag else SYSTEM_PROMPT_NO_RAG

    if use_rag:
        context = "\n\n---\n\n".join(chunk.strip() for chunk in chunks)
        user_content = (
            f"NGỮ CẢNH:\n{context}\n\n"
            f"CÂU HỎI:\n{question.strip()}\n\n"
            f"(Nhắc lại: chỉ dùng đúng nội dung trong NGỮ CẢNH ở trên để trả "
            f"lời, không thêm thông tin ngoài ngữ cảnh.)"
        )
    else:
        user_content = f"CÂU HỎI:\n{question.strip()}"

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]