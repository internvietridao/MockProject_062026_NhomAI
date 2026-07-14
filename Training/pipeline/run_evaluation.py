"""
run_evaluation.py
------------------
Chạy RIÊNG bước ROUGE/BLEU trên model ĐÃ TRAIN SẴN (output/output_model),
KHÔNG train lại. Dùng khi bạn đã có checkpoint từ trước và chỉ muốn:
  - đổi max_samples (vd: test full thay vì 100 mẫu),
  - hoặc chạy lại evaluation vì lần trước bị ngắt giữa chừng,
mà không muốn tốn thời gian train lại.

Cách chạy:
    python -m pipeline.run_evaluation
    python -m pipeline.run_evaluation --max_samples 500
"""

import argparse
import json
import os

import pandas as pd
import torch
from datasets import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

from src.config import (
    ADAPTER_DIR,
    BASE_MODEL_NAME,
    MAX_NEW_TOKENS_TRAIN_GEN,
    PREDICTIONS_CSV,
    PROMPT_STYLE,
    SYSTEM_PROMPT,
    TEST_FILE,
)
from src.evaluation import save_predictions_csv

USE_GPU = torch.cuda.is_available()


def load_trained_model():
    """Load base model + adapter LoRA đã train sẵn từ ADAPTER_DIR (giống
    cách pipeline/chat.py load, KHÔNG gắn LoRA mới / KHÔNG train)."""
    if not os.path.exists(ADAPTER_DIR):
        raise FileNotFoundError(
            f"Không tìm thấy {ADAPTER_DIR}. Hãy chạy `python -m pipeline.train` "
            f"trước để có model đã train."
        )

    print(f"Đang load model đã train từ {ADAPTER_DIR}...")
    tokenizer = AutoTokenizer.from_pretrained(str(ADAPTER_DIR))

    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_NAME,
        torch_dtype=torch.float16 if USE_GPU else torch.float32,
        device_map="auto" if USE_GPU else {"": "cpu"},
    )
    model = PeftModel.from_pretrained(base_model, str(ADAPTER_DIR))
    model.eval()
    print("Load xong.")
    return model, tokenizer


def load_raw_test_for_export(path):
    """Đọc thẳng test.jsonl -> Dataset {question, answer} (map ground_truth
    -> answer nếu cần), giống hệt logic trong pipeline/train.py."""
    if not os.path.exists(path):
        return None

    raw_samples = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            raw_samples.append({
                "question": row["question"],
                "answer": row.get("ground_truth", row.get("answer", "")),
            })

    return Dataset.from_list(raw_samples) if raw_samples else None


def main(max_samples: int = None):
    """
    Args:
        max_samples: số mẫu test dùng để tính ROUGE/BLEU. Nếu để None (mặc
            định), sẽ đọc từ dòng lệnh (--max_samples, mặc định 100 nếu
            không truyền) -- dùng khi chạy `python -m pipeline.run_evaluation`.
            Truyền trực tiếp giá trị khi gọi từ notebook, vd:
                run_evaluation.main(max_samples=1733)
            để bỏ qua argparse hoàn toàn (tránh lỗi "-f kernel.json" của
            Jupyter/Colab/Kaggle).
    """
    if max_samples is None:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--max_samples",
            type=int,
            default=100,
            help="Số mẫu test dùng để tính ROUGE/BLEU (mặc định 100, giống train.py). "
                 "Đặt lớn hơn (vd: 1733) để chạy trên toàn bộ tập test -- sẽ lâu hơn.",
        )
        args = parser.parse_known_args()[0]
        max_samples = args.max_samples

    model, tokenizer = load_trained_model()

    print("Đang tải tập test (thô)...")
    test_raw = load_raw_test_for_export(TEST_FILE)
    if test_raw is None:
        raise FileNotFoundError(
            f"Không tìm thấy/rỗng {TEST_FILE}. Hãy chạy "
            f"`python -m pipeline.build_train_dataset` trước."
        )
    print(f"Số câu hỏi test: {len(test_raw)} | Sẽ chạy: {min(len(test_raw), max_samples)}")

    save_predictions_csv(
        model=model,
        tokenizer=tokenizer,
        dataset=test_raw,
        output_path=str(PREDICTIONS_CSV),
        system_prompt=SYSTEM_PROMPT,
        prompt_style=PROMPT_STYLE,
        max_new_tokens=MAX_NEW_TOKENS_TRAIN_GEN,
        max_samples=max_samples,
    )
    print(f"Đã lưu CSV dự đoán -> {PREDICTIONS_CSV}")

    pred_df = pd.read_csv(PREDICTIONS_CSV)
    print(f"ROUGE-1 (avg): {pred_df['rouge1'].mean():.4f}")
    print(f"ROUGE-2 (avg): {pred_df['rouge2'].mean():.4f}")
    print(f"ROUGE-L (avg): {pred_df['rougeL'].mean():.4f}")
    print(f"BLEU    (avg): {pred_df['bleu'].mean():.4f}")
    print(
        "Bước tiếp theo: chạy `python -m pipeline.evaluate` để đưa CSV này "
        "qua LLM Judge (RAGAs + Prometheus/API)."
    )


if __name__ == "__main__":
    main()