import os
import json
import xml.etree.ElementTree as ET

# Thư mục chứa 12 folder (1_CancerGov_QA, 2_GARD_QA, ...)
ROOT_DIR = "."

import re

def clean_text(text):
    if not text:
        return ""

    # Gộp mọi khoảng trắng (space, tab, newline) thành 1 space
    text = re.sub(r"\s+", " ", text)

    return text.strip()

all_data = []


for folder in sorted(os.listdir(ROOT_DIR)):
    folder_path = os.path.join(ROOT_DIR, folder)

    if not os.path.isdir(folder_path):
        continue

    """if not folder.startswith(("1_", "2_", "3_")):
        continue"""

    # Bỏ tiền tố số, ví dụ:
    # 1_CancerGov_QA -> CancerGov_QA
    source_name = folder.split("_", 1)[1] if "_" in folder else folder
    source = f"MedQuAD/{source_name}"

    print(f"Processing {folder}...")

    for file_name in sorted(os.listdir(folder_path)):
        if not file_name.endswith(".xml"):
            continue

        file_path = os.path.join(folder_path, file_name)

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            qa_pairs = root.find("QAPairs")
            if qa_pairs is None:
                continue

            for qa in qa_pairs.findall("QAPair"):
                question = clean_text(qa.findtext("Question", default=""))
                answer = clean_text(qa.findtext("Answer", default=""))

                if question and answer:
                    all_data.append({
                        "question": question,
                        "answer": answer,
                        "source": source
                    })

        except Exception as e:
            print(f"Error: {file_path}")
            print(e)

# Ghi ra một file JSON duy nhất
with open("medquad.json", "w", encoding="utf-8") as f:
    json.dump(all_data, f, ensure_ascii=False, indent=4)

print(f"\nDone!")
print(f"Total QA pairs: {len(all_data)}")