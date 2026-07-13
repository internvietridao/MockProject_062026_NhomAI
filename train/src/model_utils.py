"""
model_utils.py — Khởi tạo model: quantization, load base model, cấu hình PEFT/LoRA.

Tự động phát hiện target_modules cho bất kỳ kiến trúc model nào,
đảm bảo đổi model_id là chạy ngay, không cần sửa code.
"""

from typing import List

import torch
from transformers import AutoModelForCausalLM, BitsAndBytesConfig, PreTrainedTokenizer
from peft import LoraConfig as PeftLoraConfig, get_peft_model, prepare_model_for_kbit_training


def get_bnb_config() -> BitsAndBytesConfig:
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )


def find_target_modules(model) -> List[str]:
    target_modules = set()
    for name, module in model.named_modules():
        if isinstance(module, torch.nn.Linear):
            module_name = name.split(".")[-1]
            if module_name != "lm_head":
                target_modules.add(module_name)

    return sorted(list(target_modules))


def load_model_with_peft(
    model_cfg,
    lora_cfg,
    tokenizer: PreTrainedTokenizer,
) -> torch.nn.Module:
    bnb_config = get_bnb_config()

    model_kwargs = {
        "quantization_config": bnb_config,
        "torch_dtype": model_cfg.get_torch_dtype(),
        "device_map": {"": 0},
        "trust_remote_code": model_cfg.trust_remote_code,
    }

    if model_cfg.attn_implementation:
        model_kwargs["attn_implementation"] = model_cfg.attn_implementation

    model = AutoModelForCausalLM.from_pretrained(model_cfg.model_id, **model_kwargs)

    # Không cần resize_token_embeddings nếu không thêm token mới vào từ điển.
    # Việc resize có thể làm mất các special tokens ở cuối vocab và sinh lỗi mismatch kiểu dữ liệu (BFloat16).
    # model.resize_token_embeddings(len(tokenizer))

    model = prepare_model_for_kbit_training(model)

    if lora_cfg.target_modules == "auto":
        target_modules = find_target_modules(model)
        print(f"[MODEL] Tự động phát hiện target_modules: {target_modules}")
    else:
        target_modules = lora_cfg.target_modules

    peft_config = PeftLoraConfig(
        r=lora_cfg.r,
        lora_alpha=lora_cfg.lora_alpha,
        lora_dropout=lora_cfg.lora_dropout,
        target_modules=target_modules,
        bias=lora_cfg.bias,
        task_type=lora_cfg.task_type,
    )

    model = get_peft_model(model, peft_config)

    model.print_trainable_parameters()

    return model
