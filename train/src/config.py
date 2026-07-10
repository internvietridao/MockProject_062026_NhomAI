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
    """Cấu hình base model — đổi model_id để chuyển dòng model."""
    model_id: str = "unsloth/Llama-3.2-1B-Instruct"
    torch_dtype: str = "float16"          # "float16", "bfloat16", "float32"
    device_map: str = "auto"
    trust_remote_code: bool = True
    attn_implementation: Optional[str] = None  # "flash_attention_2" nếu GPU hỗ trợ

    def get_torch_dtype(self) -> torch.dtype:
        """Chuyển đổi string dtype sang torch.dtype."""
        dtype_map = {
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
            "float32": torch.float32,
        }
        return dtype_map.get(self.torch_dtype, torch.float16)


@dataclass
class LoraConfig:
    """Cấu hình LoRA/QLoRA adapter."""
    r: int = 16                       # Rank — càng cao càng biểu diễn tốt, càng tốn VRAM
    lora_alpha: int = 32              # Hệ số scale = alpha / r
    lora_dropout: float = 0.05
    target_modules: str = "auto"      # "auto" = tự phát hiện, hoặc list cụ thể
    bias: str = "none"
    task_type: str = "CAUSAL_LM"


@dataclass
class DataConfig:
    """Cấu hình dữ liệu và prompt template."""
    dataset_path: str = "data/final_train_dataset.json"
    prompt_style: str = "alpaca"      # "alpaca" hoặc "chatml"
    max_seq_length: int = 1024        # Giảm xuống 512 nếu OOM
    train_split_ratio: float = 0.9
    system_prompt: str = (
        "You are a medical AI assistant specializing in nursing home care in US."
    )
    seed: int = 42


@dataclass
class TrainConfig:
    """Cấu hình training — mặc định tối ưu cho Kaggle T4 (16GB VRAM)."""

    # Thư mục đầu ra
    output_dir: str = "outputs"

    # Hyperparameters
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 2
    per_device_eval_batch_size: int = 2
    gradient_accumulation_steps: int = 8    # Effective batch = 2 × 8 = 16
    learning_rate: float = 2e-4
    weight_decay: float = 0.01
    warmup_ratio: float = 0.05
    lr_scheduler_type: str = "cosine"
    max_grad_norm: float = 0.3

    # Logging & Evaluation
    logging_steps: int = 10
    eval_strategy: str = "steps"
    eval_steps: int = 50
    save_strategy: str = "steps"
    save_steps: int = 100
    save_total_limit: int = 2

    # Tối ưu phần cứng
    fp16: bool = True
    bf16: bool = False
    optim: str = "paged_adamw_8bit"        # Paged AdamW — giảm VRAM usage
    gradient_checkpointing: bool = True

    # Hugging Face Hub
    push_to_hub: bool = False
    hub_model_id: Optional[str] = None     # VD: "username/nursing-home-chatbot-lora"
    hf_token: Optional[str] = None         # Tự đọc từ .env nếu None

    # Tracking
    report_to: str = "none"                # Đổi thành "wandb" nếu cần
    seed: int = 42

    def __post_init__(self):
        """Tự động đọc HF_TOKEN từ biến môi trường nếu chưa set."""
        if self.hf_token is None:
            self.hf_token = os.environ.get("HF_TOKEN")

        # Kiểm tra token khi push_to_hub được bật
        if self.push_to_hub and not self.hf_token:
            raise ValueError(
                "push_to_hub=True nhưng không tìm thấy HF_TOKEN. "
                "Hãy set trong file .env hoặc truyền trực tiếp vào TrainConfig."
            )
