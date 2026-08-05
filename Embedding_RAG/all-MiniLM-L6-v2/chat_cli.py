import sys
import os
from pathlib import Path

# Setup Python Path
CURRENT_DIR = Path(__file__).parent.resolve()
sys.path.append(str(CURRENT_DIR / "test_vector_db"))

try:
    from rag_pipeline import generate_rag_response
except ImportError:
    from test_vector_db.rag_pipeline import generate_rag_response

def main():
    print("=" * 65)
    print("🤖 NURSING HOME MANAGEMENT AI ASSISTANT")
    print("   (Hybrid RAG + Qwen-0.5B Fine-tuned trên Lightning AI)")
    print("=" * 65)
    print("👉 Nhập câu hỏi của bạn bên dưới (gõ 'exit' hoặc 'quit' để thoát).\n")
    
    while True:
        try:
            user_input = input("👤 Bạn: ")
            if user_input.strip().lower() in ["exit", "quit", "q"]:
                print("👋 Cảm ơn bạn đã sử dụng. Tạm biệt!")
                break
                
            if not user_input.strip():
                continue
                
            print("⏳ Đang tìm kiếm tài liệu ChromaDB & gửi request tới Lightning AI API...")
            result = generate_rag_response(user_input.strip())
            
            print("\n🤖 AI Chatbot:")
            print(result["answer"])
            
            print("\n📚 Nguồn tài liệu tham khảo (Citations):")
            sources = result.get("sources", [])
            if sources:
                for idx, src in enumerate(sources, 1):
                    headings = src.get("headings", {})
                    headings_str = " > ".join(headings.values()) if headings else "N/A"
                    print(f"  [{idx}] File: {src['source_file']} | Mục: {headings_str}")
            else:
                print("  (Không có nguồn tham khảo)")
                
            print("=" * 65 + "\n")
            
        except KeyboardInterrupt:
            print("\n👋 Thoát chương trình.")
            break
        except Exception as e:
            print(f"❌ Đã xảy ra lỗi: {str(e)}\n")

if __name__ == "__main__":
    main()
