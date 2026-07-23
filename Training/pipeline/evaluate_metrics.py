"""
evaluate_metrics.py
-------------------
Đánh giá các metrics bổ sung: ROUGE, BLEU, Perplexity
"""

import json
import os
import math
import sys
import torch
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from rouge_score import rouge_scorer
from sacrebleu.metrics import BLEU
import numpy as np

# Add parent directory to path to import src
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.config import ADAPTER_DIR, BASE_MODEL_NAME, TEST_FILE

USE_GPU = torch.cuda.is_available()
USE_MPS = torch.backends.mps.is_available() if hasattr(torch.backends, 'mps') else False
DEVICE = "cuda" if USE_GPU else ("mps" if USE_MPS else "cpu")
print(f"Using device: {DEVICE}", flush=True)

def load_model():
    """Load model đã train để đánh giá"""
    print("Đang load model...", flush=True)
    print("  - Loading tokenizer...", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(str(ADAPTER_DIR))
    
    print("  - Loading base model...", flush=True)
    if USE_GPU or USE_MPS:
        base_model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL_NAME,
            torch_dtype=torch.float16,
        )
        base_model = base_model.to(DEVICE)
    else:
        base_model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL_NAME,
            torch_dtype=torch.float32,
        )
    
    print("  - Loading adapter...", flush=True)
    model = PeftModel.from_pretrained(base_model, str(ADAPTER_DIR))
    model.eval()
    # Create fresh generation config without sampling params to avoid warning
    from transformers import GenerationConfig
    model.generation_config = GenerationConfig(
        max_new_tokens=300,
        do_sample=False,
    )
    return model, tokenizer

def load_test_data():
    """Load dữ liệu test từ test.jsonl"""
    if not os.path.exists(TEST_FILE):
        raise FileNotFoundError(f"Không tìm thấy {TEST_FILE}")
    
    samples = []
    with open(TEST_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                samples.append(json.loads(line))
    
    return samples

def calculate_rouge(predictions, references):
    """Tính ROUGE scores"""
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
    
    rouge1_scores = []
    rouge2_scores = []
    rougeL_scores = []
    
    for pred, ref in zip(predictions, references):
        scores = scorer.score(ref, pred)
        rouge1_scores.append(scores['rouge1'].fmeasure)
        rouge2_scores.append(scores['rouge2'].fmeasure)
        rougeL_scores.append(scores['rougeL'].fmeasure)
    
    return {
        'rouge1': np.mean(rouge1_scores) * 100,
        'rouge2': np.mean(rouge2_scores) * 100,
        'rougeL': np.mean(rougeL_scores) * 100,
    }

def calculate_bleu(predictions, references):
    """Tính BLEU score"""
    bleu = BLEU()
    
    # sacrebleu expects list of references as list of lists
    refs = [[ref] for ref in references]
    result = bleu.corpus_score(predictions, refs)
    
    return result.score

def calculate_perplexity(model, tokenizer, texts):
    """Tính perplexity trên tập dữ liệu"""
    total_loss = 0
    total_tokens = 0
    
    model.eval()
    
    with torch.no_grad():
        for text in texts:
            inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            if USE_GPU or USE_MPS:
                inputs = {k: v.to(model.device) for k, v in inputs.items()}
            
            outputs = model(**inputs, labels=inputs["input_ids"])
            loss = outputs.loss
            
            total_loss += loss.item() * inputs["input_ids"].size(1)
            total_tokens += inputs["input_ids"].size(1)
    
    avg_loss = total_loss / total_tokens
    perplexity = math.exp(avg_loss)
    
    return perplexity, avg_loss

def get_training_metrics():
    """Lấy train loss và val loss từ training logs nếu có"""
    # Tìm file training logs trong output folder
    output_dir = Path(ADAPTER_DIR)
    
    train_losses = []
    val_losses = []
    
    # Tìm trainer_state.json (được tạo bởi HuggingFace Trainer)
    trainer_state_file = output_dir / "trainer_state.json"
    if trainer_state_file.exists():
        with open(trainer_state_file, 'r') as f:
            state = json.load(f)
            
        if 'log_history' in state:
            for entry in state['log_history']:
                if 'loss' in entry:
                    train_losses.append(entry['loss'])
                if 'eval_loss' in entry:
                    val_losses.append(entry['eval_loss'])
    
    final_train_loss = train_losses[-1] if train_losses else None
    final_val_loss = val_losses[-1] if val_losses else None
    
    return final_train_loss, final_val_loss

def main():
    # Load model và dữ liệu
    model, tokenizer = load_model()
    samples = load_test_data()
    
    print(f"Số mẫu test: {len(samples)}")
    
    # Sinh câu trả lời
    predictions = []
    references = []
    
    print("Đang sinh câu trả lời...")
    for idx, sample in enumerate(samples, 1):
        if idx % 50 == 0 or idx == len(samples):
            print(f"  Progress: {idx}/{len(samples)} ({idx*100//len(samples)}%)", flush=True)
        # Dùng câu trả lời gốc làm reference
        references.append(sample['answer'] if 'answer' in sample else sample['ground_truth'])
        
        # Sinh prediction từ model
        messages = [
            {"role": "user", "content": sample['question']}
        ]
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(text, return_tensors="pt")
        
        if USE_GPU or USE_MPS:
            inputs = {k: v.to(model.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            output_ids = model.generate(**inputs, max_new_tokens=300, do_sample=False)
        
        new_tokens = output_ids[0][inputs["input_ids"].shape[1]:]
        prediction = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
        predictions.append(prediction)
    
    # Tính ROUGE
    print("\nĐang tính ROUGE...")
    rouge_scores = calculate_rouge(predictions, references)
    
    # Tính BLEU
    print("Đang tính BLEU...")
    bleu_score = calculate_bleu(predictions, references)
    
    # Tính Perplexity (trên tập reference)
    print("Đang tính Perplexity...")
    perplexity, avg_loss = calculate_perplexity(model, tokenizer, references)
    
    # Lấy training metrics
    print("Đang lấy training metrics...")
    train_loss, val_loss = get_training_metrics()
    
    # In kết quả
    print("\n" + "=" * 60)
    print("KẾT QUẢ ĐÁNH GIÁ")
    print("=" * 60)
    print(f"ROUGE-1:  {rouge_scores['rouge1']:.2f}%")
    print(f"ROUGE-2:  {rouge_scores['rouge2']:.2f}%")
    print(f"ROUGE-L:  {rouge_scores['rougeL']:.2f}%")
    print(f"BLEU:     {bleu_score:.2f}")
    print(f"Perplexity: {perplexity:.4f}")
    if train_loss is not None:
        print(f"Train Loss: {train_loss:.4f}")
    if val_loss is not None:
        print(f"Val Loss:   {val_loss:.4f}")
    print("=" * 60)

if __name__ == "__main__":
    main()
