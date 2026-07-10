"""
data_utils.py — Xử lý dữ liệu: load tokenizer, format prompt, chuẩn bị dataset.

Hỗ trợ 2 prompt template: Alpaca và ChatML.
Dataset đầu vào: JSON với format {question, answer, source}.
"""

import json
from typing import Callable, Tuple

from datasets import Dataset
from transformers import AutoTokenizer, PreTrainedTokenizer


def load_tokenizer(model_id: str) -> PreTrainedTokenizer:
    """
    Load tokenizer và tự động cấu hình pad_token.

    Nhiều model (Llama, Mistral) không có pad_token mặc định.
    Gán pad_token = eos_token để tránh lỗi khi padding.
    """
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)

    # Cấu hình pad_token nếu thiếu
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.pad_token_id = tokenizer.eos_token_id

    # Padding bên phải — cần thiết cho Causal LM training
    tokenizer.padding_side = "right"
    return tokenizer


def _format_alpaca(example: dict, system_prompt: str) -> str:
    """Format một entry {question, answer} theo Alpaca template."""
    return (
        f"### Instruction:\n{system_prompt}\n\n"
        f"### Input:\n{example['question']}\n\n"
        f"### Response:\n{example['answer']}"
    )


def _format_chatml(example: dict, system_prompt: str) -> str:
    """Format một entry {question, answer} theo ChatML template."""
    return (
        f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
        f"<|im_start|>user\n{example['question']}<|im_end|>\n"
        f"<|im_start|>assistant\n{example['answer']}<|im_end|>"
    )


def get_formatting_func(style: str, system_prompt: str) -> Callable:
    """
    Factory function: trả về hàm format prompt cho SFTTrainer.

    SFTTrainer yêu cầu formatting_func nhận batch (dict of lists)
    và trả về list[str].

    Args:
        style: "alpaca" hoặc "chatml"
        system_prompt: System prompt cho model
    """
    formatters = {
        "alpaca": _format_alpaca,
        "chatml": _format_chatml,
    }

    if style not in formatters:
        raise ValueError(
            f"prompt_style phải là 'alpaca' hoặc 'chatml', nhận được: '{style}'"
        )

    formatter = formatters[style]

    def formatting_func(examples):
        """Batch formatting — SFTTrainer truyền dict of lists."""
        texts = []
        for q, a in zip(examples["question"], examples["answer"]):
            entry = {"question": q, "answer": a}
            texts.append(formatter(entry, system_prompt))
        return texts

    return formatting_func


def preprocess_dataset(
    data_cfg,
    tokenizer: PreTrainedTokenizer,
) -> Tuple[Dataset, Dataset]:
    """
    Load JSON dataset, chia train/eval split.

    Args:
        data_cfg: DataConfig chứa đường dẫn dataset và tham số
        tokenizer: Tokenizer đã load (dùng cho tương lai nếu cần pre-tokenize)

    Returns:
        (train_dataset, eval_dataset)
    """
    # Đọc file JSON
    with open(data_cfg.dataset_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    print(f"[DATA] Đã load {len(raw_data)} mẫu từ {data_cfg.dataset_path}")

    # Chuyển thành HuggingFace Dataset
    dataset = Dataset.from_list(raw_data)

    # Chia train/eval
    split = dataset.train_test_split(
        test_size=1.0 - data_cfg.train_split_ratio,
        seed=data_cfg.seed,
    )

    return split["train"], split["test"]
