import os
import fitz  # PyMuPDF
from PIL import Image

def convert_pdf_to_images(pdf_path, output_folder):
    """PDF 각 페이지를 JPG로 변환"""
    doc = fitz.open(pdf_path)
    image_paths = []
    if not os.path.exists(output_folder):
        os.makedirs(output_folder, exist_ok=True)

    for page_index in range(len(doc)):
        page = doc.load_page(page_index)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        output_path = os.path.join(output_folder, f"page_{page_index + 1}.jpg")
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img.save(output_path, "JPEG")
        image_paths.append(output_path)
    doc.close()
    return image_paths

def convert_docx_to_images(docx_path, output_folder):
    """DOCX -> PDF -> Image 변환 (Windows 환경 권장)"""
    from docx2pdf import convert
    temp_pdf = os.path.join(output_folder, "temp_docx.pdf")
    convert(docx_path, temp_pdf)
    paths = convert_pdf_to_images(temp_pdf, output_folder)
    if os.path.exists(temp_pdf): os.remove(temp_pdf)
    return paths

def convert_pptx_to_images(pptx_path, output_folder):
    """PPTX -> PDF -> Image 변환 (Windows 환경 권장)"""
    import comtypes.client
    temp_pdf = os.path.abspath(os.path.join(output_folder, "temp_pptx.pdf"))
    powerpoint = comtypes.client.CreateObject("Powerpoint.Application")
    deck = powerpoint.Presentations.Open(os.path.abspath(pptx_path), WithWindow=False)
    deck.SaveAs(temp_pdf, 32)
    deck.Close()
    powerpoint.Quit()
    paths = convert_pdf_to_images(temp_pdf, output_folder)
    if os.path.exists(temp_pdf): os.remove(temp_pdf)
    return paths