import os
import json
import torch
import time  # 시간 측정을 위한 모듈
from datetime import timedelta
from PIL import Image
from transformers import AutoProcessor, AutoModelForImageTextToText
import file_converters as conv

# 1. 모델 로드 (최초 1회)
MODEL_PATH = "zai-org/GLM-OCR"
print(f"--- 모델 로드 중: {MODEL_PATH} ---")
processor = AutoProcessor.from_pretrained(MODEL_PATH)
model = AutoModelForImageTextToText.from_pretrained(
    MODEL_PATH, torch_dtype="auto", device_map="auto"
)

def process_directory(input_dir):
    """디렉토리 내의 모든 지원 파일을 처리"""
    start_total = time.perf_counter() # 전체 시작 시간 측정
    
    # 지원하는 확장자 정의
    valid_extensions = ('.pdf', '.docx', '.pptx')
    # 디렉토리 내 파일 목록 필터링
    files = [f for f in os.listdir(input_dir) if f.lower().endswith(valid_extensions)]
    
    if not files:
        print("처리할 지원 파일이 디렉토리에 없습니다.")
        return

    print(f"총 {len(files)}개의 파일을 발견했습니다. 처리를 시작합니다.\n")

    for file_name in files:
        file_path = os.path.join(input_dir, file_name)
        file_start = time.perf_counter() # 개별 파일 시작 시간
        
        print(f"[{file_name}] 처리 중...")
        
        try:
            # 개별 파일 OCR 수행 (결과는 파일명_final.md로 저장됨)
            run_ocr_on_file(file_path)
            
            file_end = time.perf_counter()
            file_duration = file_end - file_start
            print(f"ㄴ 완료! 소요 시간: {timedelta(seconds=int(file_duration))}\n")
        except Exception as e:
            print(f"ㄴ [오류 발생] {file_name}: {e}\n")

    end_total = time.perf_counter()
    total_duration = end_total - start_total
    print("=" * 50)
    print(f"모든 작업이 완료되었습니다.")
    print(f"전체 소요 시간: {timedelta(seconds=int(total_duration))}")
    print("=" * 50)

def run_ocr_on_file(input_file):
    """기존 단일 파일 처리 로직 (페이지 루프 포함)"""
    file_ext = os.path.splitext(input_file)[1].lower()
    base_name = os.path.splitext(input_file)[0]
    output_dir = f"temp_{os.path.basename(base_name)}"
    
    # 확장자별 변환 호출
    if file_ext == ".pdf":
        img_list = conv.convert_pdf_to_images(input_file, output_dir)
    elif file_ext == ".docx":
        img_list = conv.convert_docx_to_images(input_file, output_dir)
    elif file_ext == ".pptx":
        img_list = conv.convert_pptx_to_images(input_file, output_dir)

    all_results = []
    for idx, img_path in enumerate(img_list):
        raw_image = Image.open(img_path).convert("RGB")
        messages = [{"role": "user", "content": [
            {"type": "image", "image": raw_image},
            {"type": "text", "text": "Text Recognition:"}
        ]}]
        inputs = processor.apply_chat_template(
            messages, tokenize=True, add_generation_prompt=True,
            return_dict=True, return_tensors="pt"
        ).to(model.device)
        inputs.pop("token_type_ids", None)
        
        with torch.no_grad():
            generated_ids = model.generate(**inputs, max_new_tokens=8192)
        
        page_text = processor.decode(
            generated_ids[0][inputs["input_ids"].shape[1]:], 
            skip_special_tokens=True
        ).strip()
        all_results.append({"page": idx + 1, "content": page_text})

    # 파일 저장
    full_md = "\n\n".join([f"## Page {r['page']}\n{r['content']}" for r in all_results])
    with open(f"{base_name}_result.md", "w", encoding="utf-8") as f:
        f.write(full_md)
    
    with open(f"{base_name}_result.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=4)

# 실행: 디렉토리 경로를 입력하세요
if __name__ == "__main__":
    target_dir = "./documents_folder"  # 예시 디렉토리
    process_directory(target_dir)