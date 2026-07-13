"""
model_utils.py — Khởi tạo model: quantization, load base model, cấu hình PEFT/LoRA.

Tự động phát hiện target_modules cho bất kỳ kiến trúc model nào,
đảm bảo đổi model_id là chạy ngay, không cần sửa code.
"""

from typing import List

import torch
from transformers import AutoModelForCausalLM, BitsAndBytesConfig, PreTrainedTokenizer
from peft import LoraConfig as PeftLoraConfig, get_peft_model, prepare_model_for_kbit_training


def get_bnb_config(compute_dtype: torch.dtype) -> BitsAndBytesConfig:
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=compute_dtype,
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
    target_dtype = model_cfg.get_torch_dtype()
    bnb_config = get_bnb_config(target_dtype)

    model_kwargs = {
        "quantization_config": bnb_config,
        "torch_dtype": model_cfg.get_torch_dtype(),
        "device_map": {"": 0},
        "trust_remote_code": model_cfg.trust_remote_code,
    }

    if model_cfg.attn_implementation:
        model_kwargs["attn_implementation"] = model_cfg.attn_implementation

    model = AutoModelForCausalLM.from_pretrained(model_cfg.model_id, **model_kwargs)

    # Ghi đè cấu hình torch_dtype của mô hình để prepare_model_for_kbit_training và PEFT
    # nhận biết và khởi tạo/ép kiểu các layer không lượng hóa sang float16 thay vì bfloat16 mặc định.
    model.config.torch_dtype = model_cfg.get_torch_dtype()

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

    # Ép kiểu các tham số trainable dạng float sang target_dtype để đồng bộ
    for name, param in model.named_parameters():
        if param.dtype in [torch.float16, torch.bfloat16, torch.float32] and param.requires_grad:
            param.data = param.data.to(target_dtype)

    model.print_trainable_parameters()

    return model
