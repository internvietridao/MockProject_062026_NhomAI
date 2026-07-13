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

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.pad_token_id = tokenizer.eos_token_id
    
    tokenizer.padding_side = "right"
    return tokenizer


def _format_alpaca(example: dict, system_prompt: str) -> str:
    return (
        f"### Instruction:\n{system_prompt}\n\n"
        f"### Input:\n{example['question']}\n\n"
        f"### Response:\n{example['answer']}"
    )


def _format_chatml(example: dict, system_prompt: str) -> str:
    return (
        f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
        f"<|im_start|>user\n{example['question']}<|im_end|>\n"
        f"<|im_start|>assistant\n{example['answer']}<|im_end|>"
    )


def get_formatting_func(style: str, system_prompt: str) -> Callable:
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
        texts = []
        for q, a in zip(examples["question"], examples["answer"]):
            entry = {"question": q, "answer": a}
            texts.append(formatter(entry, system_prompt))
        return texts

    return formatting_func


def preprocess_dataset(
    data_cfg,
    tokenizer: PreTrainedTokenizer,
) -> Tuple[Dataset, Dataset, Dataset]:
    with open(data_cfg.dataset_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    print(f"[DATA] Đã load {len(raw_data)} mẫu từ {data_cfg.dataset_path}")
    dataset = Dataset.from_list(raw_data)
    dataset = dataset.class_encode_column("source")

    first_split = dataset.train_test_split(
        test_size=1.0 - data_cfg.train_split_ratio,
        seed=data_cfg.seed,
        stratify_by_column="source",
    )
    train_dataset = first_split["train"]
    temp_dataset = first_split["test"]

    remaining_ratio = 1.0 - data_cfg.train_split_ratio
    if remaining_ratio <= 0.0:
        raise ValueError("train_split_ratio phải nhỏ hơn 1.0")

    val_relative_ratio = data_cfg.val_split_ratio / remaining_ratio
    if val_relative_ratio >= 1.0 or val_relative_ratio <= 0.0:
        raise ValueError(
            f"Tỉ lệ val_split_ratio ({data_cfg.val_split_ratio}) không hợp lệ "
            f"so với train_split_ratio ({data_cfg.train_split_ratio})."
        )

    second_split = temp_dataset.train_test_split(
        test_size=1.0 - val_relative_ratio,
        seed=data_cfg.seed,
        stratify_by_column="source",
    )
    val_dataset = second_split["train"]
    test_dataset = second_split["test"]

    return train_dataset, val_dataset, test_dataset
