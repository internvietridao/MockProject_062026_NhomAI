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
    """
    Tạo cấu hình BitsAndBytes cho QLoRA 4-bit.

    Sử dụng NF4 quantization type với double quantization
    để tối ưu VRAM trên Kaggle T4/P100.
    """
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )


def find_target_modules(model) -> List[str]:
    """
    Tự động tìm tất cả Linear layers phù hợp cho LoRA injection.

    Quét model.named_modules(), thu thập tên các nn.Linear layers,
    loại trừ lm_head (output projection) để tránh ảnh hưởng vocabulary.

    Hoạt động với mọi kiến trúc: Llama, Mistral, Gemma, Qwen, Phi...
    """
    target_modules = set()
    for name, module in model.named_modules():
        if isinstance(module, torch.nn.Linear):
            # Lấy tên module cuối cùng (vd: "model.layers.0.self_attn.q_proj" → "q_proj")
            module_name = name.split(".")[-1]
            # Loại trừ lm_head — không nên LoRA trên output projection
            if module_name != "lm_head":
                target_modules.add(module_name)

    return sorted(list(target_modules))


def load_model_with_peft(
    model_cfg,
    lora_cfg,
    tokenizer: PreTrainedTokenizer,
) -> torch.nn.Module:
    """
    Load base model với quantization 4-bit, rồi wrap bằng PEFT/LoRA adapter.

    Args:
        model_cfg: ModelConfig chứa model_id, dtype, device_map
        lora_cfg: LoraConfig chứa tham số LoRA
        tokenizer: Tokenizer đã load (cần để resize embedding nếu thêm special tokens)

    Returns:
        PEFT model sẵn sàng training
    """
    # Cấu hình quantization 4-bit
    bnb_config = get_bnb_config()

    # Chuẩn bị kwargs cho model loading
    model_kwargs = {
        "quantization_config": bnb_config,
        "torch_dtype": model_cfg.get_torch_dtype(),
        "device_map": model_cfg.device_map,
        "trust_remote_code": model_cfg.trust_remote_code,
    }

    # Thêm attention implementation nếu được chỉ định
    if model_cfg.attn_implementation:
        model_kwargs["attn_implementation"] = model_cfg.attn_implementation

    # Load base model
    model = AutoModelForCausalLM.from_pretrained(model_cfg.model_id, **model_kwargs)

    # Resize embedding nếu tokenizer có thêm special tokens
    model.resize_token_embeddings(len(tokenizer))

    # Chuẩn bị model cho k-bit training (freeze base, enable gradient cho adapter)
    model = prepare_model_for_kbit_training(model)

    # Tự động phát hiện target_modules nếu cấu hình là "auto"
    if lora_cfg.target_modules == "auto":
        target_modules = find_target_modules(model)
        print(f"[MODEL] Tự động phát hiện target_modules: {target_modules}")
    else:
        target_modules = lora_cfg.target_modules

    # Cấu hình PEFT LoRA
    peft_config = PeftLoraConfig(
        r=lora_cfg.r,
        lora_alpha=lora_cfg.lora_alpha,
        lora_dropout=lora_cfg.lora_dropout,
        target_modules=target_modules,
        bias=lora_cfg.bias,
        task_type=lora_cfg.task_type,
    )

    # Wrap model bằng PEFT adapter
    model = get_peft_model(model, peft_config)

    # In thông tin trainable parameters
    model.print_trainable_parameters()

    return model
