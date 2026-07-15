"""
config.py — Cấu hình tập trung cho LLM Fine-tuning Pipeline.

Tất cả tham số (model, LoRA, data, training) được gom vào đây.
Người dùng chỉ cần thay đổi file này để điều chỉnh toàn bộ pipeline.
"""

import os
from dataclasses import dataclass
from typing import Optional

import torch


@dataclass
class ModelConfig:
    model_id: str = "unsloth/Phi-3-mini-4k-instruct-bnb-4bit"
    torch_dtype: str = "bfloat16"
    device_map: str = "auto"
    trust_remote_code: bool = True
    attn_implementation: Optional[str] = None
    temperature: float = 0.1
    do_sample: bool = True

    def get_torch_dtype(self) -> torch.dtype:
        dtype_map = {
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
            "float32": torch.float32,
        }
        return dtype_map.get(self.torch_dtype, torch.bfloat16)


@dataclass
class LoraConfig:
    r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.0
    target_modules: str = "auto"
    bias: str = "none"
    task_type: str = "CAUSAL_LM"


@dataclass
class DataConfig:
    dataset_path: str = "data/final_train_dataset.json"
    prompt_style: str = "phi3"
    max_seq_length: int = 2048
    train_split_ratio: float = 0.8
    val_split_ratio: float = 0.1
    system_prompt: str = (
        "You are a highly precise medical AI Assistant specializing in US nursing home care and management. "
        "Your answer must be direct, strictly factual, and professional. Avoid speculation, extrapolation, "
        "or conversational fluff."
    )
    seed: int = 42


@dataclass
class TrainConfig:
    output_dir: str = "outputs_Phi-3-3.8B"
    num_train_epochs: int = 1
    per_device_train_batch_size: int = 2
    per_device_eval_batch_size: int = 2
    gradient_accumulation_steps: int = 8
    learning_rate: float = 2e-4
    weight_decay: float = 0.01
    warmup_ratio: float = 0.05
    lr_scheduler_type: str = "cosine"
    max_grad_norm: float = 0.3

    logging_steps: int = 10
    eval_strategy: str = "steps"
    eval_steps: int = 200
    save_strategy: str = "steps"
    save_steps: int = 200
    save_total_limit: int = 2

    fp16: bool = True
    bf16: bool = False
    optim: str = "paged_adamw_8bit"
    gradient_checkpointing: bool = True

    push_to_hub: bool = False
    hub_model_id: Optional[str] = None
    hf_token: Optional[str] = None

    report_to: str = "none"
    seed: int = 42
    early_stopping_patience: int = 3

    def __post_init__(self):
        if self.hf_token is None:
            self.hf_token = os.environ.get("HF_TOKEN")

        if self.push_to_hub and not self.hf_token:
            raise ValueError(
                "push_to_hub=True nhưng không tìm thấy HF_TOKEN. "
                "Hãy set trong file .env hoặc truyền trực tiếp vào TrainConfig."
            )
