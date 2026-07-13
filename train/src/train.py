"""
train.py — File thực thi chính (Main Script) cho LLM Fine-tuning Pipeline.

Kết nối tất cả module: config → data → model → training → evaluation → upload.
"""

import math
import os
import sys

from dotenv import load_dotenv
from trl import SFTTrainer, SFTConfig

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import ModelConfig, LoraConfig as AppLoraConfig, DataConfig, TrainConfig
from src.data_utils import load_tokenizer, get_formatting_func, preprocess_dataset
from src.model_utils import load_model_with_peft
from src.evaluation import save_predictions_csv, compute_perplexity


def main():
    load_dotenv()
    print("[1/8] Đã load biến môi trường từ .env")

    model_cfg = ModelConfig()
    lora_cfg = AppLoraConfig()
    data_cfg = DataConfig()
    train_cfg = TrainConfig()

    print(f"[2/8] Cấu hình:")
    print(f"  Model:       {model_cfg.model_id}")
    print(f"  LoRA r:      {lora_cfg.r}, alpha: {lora_cfg.lora_alpha}")
    print(f"  Prompt:      {data_cfg.prompt_style}")
    print(f"  Max Length:  {data_cfg.max_seq_length}")
    print(f"  Epochs:      {train_cfg.num_train_epochs}")
    effective_batch = train_cfg.per_device_train_batch_size * train_cfg.gradient_accumulation_steps
    print(f"  Batch Size:  {train_cfg.per_device_train_batch_size} x {train_cfg.gradient_accumulation_steps} (effective: {effective_batch})")
    print(f"  Push to Hub: {train_cfg.push_to_hub}")

    tokenizer = load_tokenizer(model_cfg.model_id)
    print(f"[3/8] Tokenizer loaded: vocab_size={tokenizer.vocab_size}, pad_token='{tokenizer.pad_token}'")

    train_dataset, val_dataset, test_dataset = preprocess_dataset(data_cfg, tokenizer)
    print(f"[4/8] Dataset: train={len(train_dataset)}, val={len(val_dataset)}, test={len(test_dataset)}")

    model = load_model_with_peft(model_cfg, lora_cfg, tokenizer)
    print("[5/8] Model loaded với QLoRA 4-bit + PEFT adapter")

    total_steps = math.ceil(
        len(train_dataset)
        / (train_cfg.per_device_train_batch_size * train_cfg.gradient_accumulation_steps)
    ) * train_cfg.num_train_epochs
    warmup_steps = int(train_cfg.warmup_ratio * total_steps)

    sft_config = SFTConfig(
        output_dir=train_cfg.output_dir,
        num_train_epochs=train_cfg.num_train_epochs,
        per_device_train_batch_size=train_cfg.per_device_train_batch_size,
        per_device_eval_batch_size=train_cfg.per_device_eval_batch_size,
        gradient_accumulation_steps=train_cfg.gradient_accumulation_steps,
        learning_rate=train_cfg.learning_rate,
        weight_decay=train_cfg.weight_decay,
        warmup_steps=warmup_steps,
        lr_scheduler_type=train_cfg.lr_scheduler_type,
        logging_steps=train_cfg.logging_steps,
        eval_strategy=train_cfg.eval_strategy,
        eval_steps=train_cfg.eval_steps,
        save_strategy=train_cfg.save_strategy,
        save_steps=train_cfg.save_steps,
        save_total_limit=train_cfg.save_total_limit,
        fp16=train_cfg.fp16,
        bf16=train_cfg.bf16,
        optim=train_cfg.optim,
        gradient_checkpointing=train_cfg.gradient_checkpointing,
        push_to_hub=train_cfg.push_to_hub,
        hub_model_id=train_cfg.hub_model_id,
        hub_token=train_cfg.hf_token,
        report_to=train_cfg.report_to,
        seed=train_cfg.seed,
        max_grad_norm=train_cfg.max_grad_norm,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
    )

    formatting_func = get_formatting_func(data_cfg.prompt_style, data_cfg.system_prompt)
    tokenizer.model_max_length = data_cfg.max_seq_length

    trainer = SFTTrainer(
        model=model,
        args=sft_config,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        processing_class=tokenizer,
        formatting_func=formatting_func,
    )

    print("[6/8] SFTTrainer khởi tạo thành công")

    print(f"\n{'=' * 60}")
    print("  BẮT ĐẦU TRAINING")
    print(f"{'=' * 60}\n")

    train_result = trainer.train()

    train_metrics = train_result.metrics
    train_loss = train_metrics.get("train_loss", 0)

    eval_metrics = trainer.evaluate()
    eval_loss = eval_metrics.get("eval_loss", 0)
    perplexity = compute_perplexity(eval_loss)

    print(f"\n[7/8] Training hoàn tất!")
    print(f"  Train Loss:   {train_loss:.4f}")
    print(f"  Eval Loss:    {eval_loss:.4f}")
    print(f"  Perplexity:   {perplexity:.4f} (từ eval_loss)")
    print(f"  Runtime:      {train_metrics.get('train_runtime', 0):.0f}s")

    trainer.save_model(train_cfg.output_dir)
    tokenizer.save_pretrained(train_cfg.output_dir)
    print(f"  Adapter saved → {train_cfg.output_dir}/")
    if train_cfg.push_to_hub:
        print("\n[UPLOAD] Đang push adapter lên Hugging Face Hub...")
        trainer.push_to_hub()
        print(f"[UPLOAD] Hoàn tất! Model ID: {train_cfg.hub_model_id}")

    eval_csv_path = os.path.join(train_cfg.output_dir, "evaluation_results.csv")
    print(f"\n[8/8] Chạy inference trên tập test để tính ROUGE/BLEU...")

    save_predictions_csv(
        model=model,
        tokenizer=tokenizer,
        dataset=test_dataset,
        output_path=eval_csv_path,
        system_prompt=data_cfg.system_prompt,
        prompt_style=data_cfg.prompt_style,
    )

if __name__ == "__main__":
    main()
