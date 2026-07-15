"""
evaluate.py
-----------
Đánh giá chất lượng chatbot RAG bằng RAGAs.

QUAN TRỌNG - GIÁM KHẢO PHẢI TÁCH RỜI MODEL ĐANG ĐƯỢC ĐÁNH GIÁ:
Trước đây file này dùng chính model vừa fine-tune (base + adapter LoRA) làm
luôn LLM Judge -- giống 1 học sinh tự chấm bài thi của mình: model có xu
hướng tự đánh giá cao câu trả lời của chính nó (self-preference bias), kết
quả không đáng tin.

THAY ĐỔI SO VỚI BẢN CŨ:
  - KHÔNG tự load model bị đánh giá + tự generate câu trả lời nữa. Bước sinh
    câu trả lời (+ ROUGE/BLEU) đã làm ở CUỐI pipeline/train.py rồi, kết quả
    lưu sẵn ở src.config.PREDICTIONS_CSV (question, reference, prediction,
    rouge1/2/L, bleu). File này chỉ ĐỌC csv đó lên, tránh generate 2 lần.
  - Giám khảo ƯU TIÊN gọi qua API (nhanh, không tốn VRAM) thay vì load
    Prometheus 2 (7B) cục bộ. Đặt MEDQUAD_JUDGE_API_KEY để dùng API; nếu
    không set, tự động fallback về load Prometheus cục bộ (code cũ).

Cài đặt cần thiết:
    pip install -r requirements.txt

Cách chạy:
    python -m pipeline.evaluate
"""

import os

import pandas as pd
import torch

from datasets import Dataset
from langchain_community.embeddings import HuggingFaceEmbeddings
from ragas import evaluate
from ragas.metrics import (
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)
from ragas.run_config import RunConfig

from src.config import (
    EMBEDDING_MODEL_NAME,
    JUDGE_API_BASE,
    JUDGE_API_KEY,
    JUDGE_API_MODEL,
    JUDGE_LOAD_IN_4BIT,
    JUDGE_MODEL_NAME,
    PREDICTIONS_CSV,
    USE_RAG,
)

USE_GPU = torch.cuda.is_available()


# ============================================================
# 1. LOAD MODEL GIÁM KHẢO
#    - Có JUDGE_API_KEY -> gọi qua API (ưu tiên, nhanh, không tốn VRAM)
#    - Không có -> fallback load Prometheus 2 cục bộ (code cũ)
#    Cả 2 đường đều KHÔNG liên quan gì tới model vừa fine-tune ở train.py.
# ============================================================

def load_judge_llm():
    if JUDGE_API_KEY:
        from langchain_openai import ChatOpenAI

        print(f"Gọi model giám khảo qua API: {JUDGE_API_MODEL} ({JUDGE_API_BASE})")
        return ChatOpenAI(
            model=JUDGE_API_MODEL,
            base_url=JUDGE_API_BASE,
            api_key=JUDGE_API_KEY,
            temperature=0,
            max_tokens=600,
        )

    print(
        "Không có MEDQUAD_JUDGE_API_KEY -> fallback load Prometheus 2 cục bộ "
        f"({JUDGE_MODEL_NAME}). Đặt biến môi trường này để gọi giám khảo qua "
        "API thay thế (nhanh hơn nhiều, không cần load model 7B)."
    )
    from langchain_community.llms import HuggingFacePipeline
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        pipeline,
    )

    tokenizer = AutoTokenizer.from_pretrained(JUDGE_MODEL_NAME)

    if USE_GPU and JUDGE_LOAD_IN_4BIT:
        print(f"Load {JUDGE_MODEL_NAME} ở chế độ 4-bit (giám khảo, tách biệt model đang train)")
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        model = AutoModelForCausalLM.from_pretrained(
            JUDGE_MODEL_NAME,
            quantization_config=bnb_config,
            device_map="auto",
        )
    elif USE_GPU:
        model = AutoModelForCausalLM.from_pretrained(
            JUDGE_MODEL_NAME,
            torch_dtype=torch.float16,
            device_map="auto",
        )
    else:
        print(
            "CẢNH BÁO: không có GPU -> chạy Prometheus 2 (7B) trên CPU sẽ RẤT chậm. "
            "Cân nhắc đặt MEDQUAD_JUDGE_API_KEY để gọi qua API thay vì load cục bộ."
        )
        model = AutoModelForCausalLM.from_pretrained(
            JUDGE_MODEL_NAME,
            torch_dtype=torch.float32,
            device_map={"": "cpu"},
        )

    gen_pipeline = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=256,
        do_sample=False,  # tắt random để LLM Judge chấm điểm ổn định hơn
    )
    return HuggingFacePipeline(pipeline=gen_pipeline)


# ============================================================
# 2. ĐỌC DỰ ĐOÁN TỪ CSV (đã sinh sẵn ở pipeline/train.py)
# ============================================================

def load_predictions():
    """
    Đọc PREDICTIONS_CSV (sinh bởi save_predictions_csv() cuối train.py).
    Cột: question, reference, prediction, rouge1, rouge2, rougeL, bleu.
    """
    if not os.path.exists(PREDICTIONS_CSV):
        raise FileNotFoundError(
            f"Không tìm thấy {PREDICTIONS_CSV}. "
            f"Hãy chạy `python -m pipeline.train` trước để sinh CSV dự đoán "
            f"(bước cuối của train.py: inference + ROUGE/BLEU trên tập test)."
        )

    df = pd.read_csv(PREDICTIONS_CSV)

    samples = []
    for _, row in df.iterrows():
        samples.append({
            "question": row["question"],
            "answer": row["prediction"],
            "ground_truth": row["reference"],
            # CSV hiện chưa lưu contexts -- chỉ cần khi USE_RAG=True.
            # Nếu muốn dùng đủ faithfulness/context_precision/context_recall,
            # sửa save_predictions_csv() để lưu thêm cột "contexts" (JSON list).
            "contexts": [],
        })

    return samples


# ============================================================
# 3. CHẠY RAGAs
# ============================================================

def select_metrics():
    """
    context_precision/context_recall/faithfulness cần "contexts" thật (đo
    độ bám ngữ cảnh) -- vô nghĩa khi USE_RAG=False (không có contexts nào).
    Chỉ answer_relevancy (so khớp câu hỏi <-> câu trả lời, không cần context)
    dùng được trong cả 2 chế độ.
    """
    if USE_RAG:
        print(
            "USE_RAG=True nhưng CSV dự đoán hiện KHÔNG có cột contexts thật -> "
            "faithfulness/context_precision/context_recall sẽ không đáng tin. "
            "Cần bổ sung contexts vào save_predictions_csv() nếu muốn dùng đủ 4 metrics."
        )
        return [faithfulness, answer_relevancy, context_precision, context_recall]

    print(
        "USE_RAG=False -> bỏ qua faithfulness/context_precision/context_recall "
        "(cần contexts thật, hiện không có). Chỉ chấm answer_relevancy."
    )
    return [answer_relevancy]


def main():
    print("Đang đọc CSV dự đoán (đã sinh sẵn từ bước train, gồm ROUGE/BLEU)...")
    samples = load_predictions()
    print(f"Số mẫu: {len(samples)}")

    dataset = Dataset.from_list(samples)

    print("Đang khởi tạo model giám khảo (tách biệt model vừa train)...")
    llm_judge = load_judge_llm()

    print("Đang load embedding model (cho Answer Relevance)...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

    print("Đang chấm điểm bằng RAGAs...")
    result = evaluate(
        dataset,
        metrics=select_metrics(),
        llm=llm_judge,
        embeddings=embeddings,
        run_config=RunConfig(
            timeout=7200,
            max_workers=1,
        ),
    )

    print("=" * 50)
    print("KẾT QUẢ ĐÁNH GIÁ (RAGAs + LLM Judge)")
    print("=" * 50)
    print(result)


if __name__ == "__main__":
    main()