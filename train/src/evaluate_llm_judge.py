"""
evaluate_llm_judge.py — Đánh giá nâng cao mô hình ngôn ngữ lớn bằng LLM-as-a-judge.

Đọc kết quả từ outputs_Qwen-0.5B/evaluation_results.csv, sử dụng Gemini API hoặc OpenAI API
để đánh giá độ chính xác y khoa, độ đầy đủ và giọng điệu chuyên nghiệp của câu trả lời.
Xuất báo cáo chi tiết ra outputs_Qwen-0.5B/llm_judge_report.md.
"""

import os
import json
import random
import argparse
import pandas as pd
from typing import Dict, List, Optional
from dotenv import load_dotenv

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


def setup_gemini_client(api_key: str):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config={"response_mime_type": "application/json"}
    )


def setup_openai_client(api_key: str):
    return OpenAI(api_key=api_key)


def get_evaluation_prompt(question: str, reference: str, prediction: str) -> str:
    return f"""Bạn là một chuyên gia y tế Hoa Kỳ cao cấp và chuyên gia đánh giá mô hình ngôn ngữ lớn (LLM-as-a-judge).
Nhiệm vụ của bạn là đánh giá câu trả lời dự đoán (Prediction) của chatbot AI so với câu trả lời chuẩn (Reference) cho câu hỏi y khoa dưới đây.

[CÂU HỎI]
{question}

[CÂU TRẢ LỜI CHUẨN (REFERENCE)]
{reference}

[CÂU TRẢ LỜI CỦA CHATBOT (PREDICTION)]
{prediction}

Hãy đánh giá và chấm điểm theo 3 tiêu chí sau trên thang điểm từ 1 đến 5 (1: Tệ nhất, 5: Tốt nhất):

1. Medical Accuracy & Safety (Độ chính xác và An toàn Y khoa):
- Điểm 5: Hoàn toàn chính xác về mặt y khoa, không chứa thông tin sai lệch hay nguy hiểm.
- Điểm 3-4: Đa số thông tin chính xác nhưng có một số chỗ diễn đạt chưa hoàn toàn chuẩn hoặc thiếu sắc thái chuyên môn nhẹ.
- Điểm 1-2: Chứa thông tin sai lệch nghiêm trọng, bịa đặt (hallucination) hoặc có thể gây nguy hiểm cho người bệnh/quy trình vận hành.

2. Completeness & Coverage (Độ đầy đủ và Bao quát Thông tin):
- Điểm 5: Trả lời đầy đủ tất cả các ý chính và thông tin quan trọng có trong Câu trả lời chuẩn.
- Điểm 3-4: Trả lời được ý cốt lõi nhưng bỏ sót một vài chi tiết nhỏ hữu ích từ Câu trả lời chuẩn.
- Điểm 1-2: Trả lời quá sơ sài hoặc bỏ sót phần lớn các ý chính quan trọng.

3. Professional Tone & Format (Giọng điệu và Định dạng Chuyên nghiệp):
- Điểm 5: Giọng điệu chuyên nghiệp, khách quan, định dạng rõ ràng, trực diện, không có từ ngữ thừa thãi (chào hỏi xã giao, giải thích dài dòng không cần thiết).
- Điểm 3-4: Đạt chuẩn chuyên môn nhưng vẫn có một chút từ ngữ thừa, hoặc định dạng chưa tối ưu.
- Điểm 1-2: Giọng điệu không phù hợp (quá thân mật, không giống chuyên gia y khoa) hoặc cấu trúc hỗn loạn.

Yêu cầu đầu ra bắt buộc phải trả về dưới định dạng JSON với cấu trúc sau:
{{
  "accuracy_score": <int từ 1 đến 5>,
  "accuracy_reason": "<Giải thích ngắn gọn bằng tiếng Việt lý do chấm điểm tiêu chí này>",
  "completeness_score": <int từ 1 đến 5>,
  "completeness_reason": "<Giải thích ngắn gọn bằng tiếng Việt lý do chấm điểm tiêu chí này>",
  "tone_score": <int từ 1 đến 5>,
  "tone_reason": "<Giải thích ngắn gọn bằng tiếng Việt lý do chấm điểm tiêu chí này>",
  "overall_comment": "<Nhận xét tổng quan bằng tiếng Việt về câu trả lời của chatbot>"
}}
"""


def evaluate_with_gemini(model, question: str, reference: str, prediction: str) -> Optional[Dict]:
    prompt = get_evaluation_prompt(question, reference, prediction)
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        print(f"Lỗi khi gọi Gemini API: {str(e)}")
        return None


def evaluate_with_openai(client, question: str, reference: str, prediction: str) -> Optional[Dict]:
    prompt = get_evaluation_prompt(question, reference, prediction)
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional evaluator that outputs structured JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Lỗi khi gọi OpenAI API: {str(e)}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Đánh giá kết quả fine-tune bằng LLM-as-a-judge.")
    parser.add_argument("--csv", type=str, default="outputs_Qwen-0.5B/evaluation_results.csv", help="Đường dẫn tới file CSV kết quả.")
    parser.add_argument("--num_samples", type=int, default=10, help="Số lượng mẫu ngẫu nhiên để đánh giá.")
    parser.add_argument("--output", type=str, default="outputs_Qwen-0.5B/llm_judge_report.md", help="Đường dẫn lưu báo cáo Markdown.")
    parser.add_argument("--provider", type=str, default="auto", choices=["auto", "gemini", "openai"], help="API Provider sử dụng.")
    args = parser.parse_args()

    load_dotenv()

    csv_path = args.csv
    if not os.path.exists(csv_path):
        csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), args.csv)
        if not os.path.exists(csv_path):
            print(f"Không tìm thấy file kết quả CSV tại: {args.csv}")
            return

    df = pd.read_csv(csv_path)
    print(f"Đã đọc file CSV thành công: tìm thấy {len(df)} mẫu thử nghiệm.")

    client = None
    provider_used = ""
    
    gemini_key = os.environ.get("GEMINI_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    if args.provider == "gemini" or (args.provider == "auto" and gemini_key and HAS_GEMINI):
        if not gemini_key:
            print("Lỗi: Đã chọn Gemini hoặc tự động nhận diện nhưng không có GEMINI_API_KEY trong biến môi trường/.env")
            return
        if not HAS_GEMINI:
            print("Lỗi: Chưa cài đặt thư viện 'google-generativeai'. Vui lòng chạy: pip install google-generativeai")
            return
        client = setup_gemini_client(gemini_key)
        provider_used = "Gemini (gemini-1.5-flash)"
        print("Sử dụng Gemini API làm Giám khảo.")
    elif args.provider == "openai" or (args.provider == "auto" and openai_key and HAS_OPENAI):
        if not openai_key:
            print("Lỗi: Đã chọn OpenAI hoặc tự động nhận diện nhưng không có OPENAI_API_KEY trong biến môi trường/.env")
            return
        if not HAS_OPENAI:
            print("Lỗi: Chưa cài đặt thư viện 'openai'. Vui lòng chạy: pip install openai")
            return
        client = setup_openai_client(openai_key)
        provider_used = "OpenAI (gpt-4o-mini)"
        print("Sử dụng OpenAI API làm Giám khảo.")
    else:
        print("Lỗi: Không tìm thấy API Key phù hợp hoặc thư viện tương ứng chưa được cài đặt.")
        print("Hãy chắc chắn rằng bạn đã thêm GEMINI_API_KEY hoặc OPENAI_API_KEY vào tệp .env")
        print("Và cài đặt thư viện tương ứng (pip install google-generativeai hoặc pip install openai)")
        return

    num_samples = min(args.num_samples, len(df))
    random.seed(42)
    sample_indices = random.sample(range(len(df)), num_samples)
    sampled_df = df.iloc[sample_indices].reset_index(drop=True)

    print(f"Đang tiến hành chấm điểm {num_samples} mẫu bằng {provider_used}...")

    evaluated_results = []
    
    for idx, row in sampled_df.iterrows():
        question = row["question"]
        reference = row["reference"]
        prediction = row["prediction"]
        
        print(f"[{idx+1}/{num_samples}] Đang chấm điểm câu hỏi: {question[:50]}...")
        
        if "Gemini" in provider_used:
            res = evaluate_with_gemini(client, question, reference, prediction)
        else:
            res = evaluate_with_openai(client, question, reference, prediction)
            
        if res:
            res["question"] = question
            res["reference"] = reference
            res["prediction"] = prediction
            res["rouge1"] = row.get("rouge1", 0.0)
            res["rougeL"] = row.get("rougeL", 0.0)
            evaluated_results.append(res)
        else:
            print(f"⚠️ Bỏ qua mẫu thứ {idx+1} do lỗi gọi API.")

    if not evaluated_results:
        print("Không có kết quả đánh giá nào được tạo thành công.")
        return

    avg_accuracy = sum(r["accuracy_score"] for r in evaluated_results) / len(evaluated_results)
    avg_completeness = sum(r["completeness_score"] for r in evaluated_results) / len(evaluated_results)
    avg_tone = sum(r["tone_score"] for r in evaluated_results) / len(evaluated_results)
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(f"# 🩺 Báo cáo Đánh giá Chất lượng LLM-as-a-judge\n\n")
        f.write(f"- **Mô hình Giám khảo:** {provider_used}\n")
        f.write(f"- **Số lượng mẫu đánh giá:** {len(evaluated_results)} / {len(df)} mẫu ngẫu nhiên\n")
        f.write(f"- **File nguồn:** `{args.csv}`\n\n")
        
        f.write(f"## 📊 Điểm số Đánh giá Trung bình (Thang điểm 1-5)\n\n")
        f.write(f"| Tiêu chí đánh giá | Điểm trung bình | Trạng thái | Mô tả tiêu chí |\n")
        f.write(f"| :--- | :--- | :--- | :--- |\n")
        
        status_accuracy = "🟢 Tốt" if avg_accuracy >= 4.0 else ("🟡 Trung bình" if avg_accuracy >= 3.0 else "🔴 Yếu")
        status_completeness = "🟢 Tốt" if avg_completeness >= 4.0 else ("🟡 Trung bình" if avg_completeness >= 3.0 else "🔴 Yếu")
        status_tone = "🟢 Tốt" if avg_tone >= 4.0 else ("🟡 Trung bình" if avg_tone >= 3.0 else "🔴 Yếu")
        
        f.write(f"| **Medical Accuracy & Safety** | **{avg_accuracy:.2f} / 5.0** | {status_accuracy} | Độ chính xác y khoa và tính an toàn của lời khuyên |\n")
        f.write(f"| **Completeness & Coverage** | **{avg_completeness:.2f} / 5.0** | {status_completeness} | Mức độ đầy đủ thông tin so với câu trả lời chuẩn |\n")
        f.write(f"| **Professional Tone & Format** | **{avg_tone:.2f} / 5.0** | {status_tone} | Giọng điệu chuyên nghiệp, trực diện, chuẩn ChatML |\n\n")
        
        f.write(f"## 📝 Chi tiết đánh giá từng mẫu thử nghiệm\n\n")
        
        for idx, r in enumerate(evaluated_results):
            f.write(f"### Mẫu #{idx+1}\n\n")
            f.write(f"- **Câu hỏi:** {r['question']}\n")
            f.write(f"- **Câu trả lời chuẩn (Reference):** *\"{r['reference']}\"*\n")
            f.write(f"- **Câu dự đoán (Prediction):** *\"{r['prediction']}\"*\n\n")
            
            f.write(f"#### Điểm số chi tiết:\n")
            f.write(f"- **Medical Accuracy:** `{r['accuracy_score']}/5` — *{r['accuracy_reason']}*\n")
            f.write(f"- **Completeness:** `{r['completeness_score']}/5` — *{r['completeness_reason']}*\n")
            f.write(f"- **Tone & Format:** `{r['tone_score']}/5` — *{r['tone_reason']}*\n")
            f.write(f"- **ROUGE-1 / ROUGE-L:** `{r['rouge1']:.4f} / {r['rougeL']:.4f}`\n")
            f.write(f"- **Nhận xét chung:** {r['overall_comment']}\n\n")
            f.write(f"---\n\n")
            
    print(f"Báo cáo đánh giá đã được xuất thành công ra file: {args.output}")


if __name__ == "__main__":
    main()
