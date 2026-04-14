"""Robust TXT/PDF/DOCX extraction with normalization and graceful fallbacks."""

from __future__ import annotations

import re
from dataclasses import dataclass
from io import BytesIO
from typing import Optional


@dataclass
class ExtractionResult:
    text: str
    warning: Optional[str] = None


def _normalize_text(text: str) -> str:
    """Normalize text by removing extra whitespace and standardizing line breaks."""
    text = (text or "").replace("\x00", "")
    
    # Standardize line breaks
    text = re.sub(r"\r\n?", "\n", text)
    
    # Remove excessive blank lines (keep max 2)
    text = re.sub(r"\n{3,}", "\n\n", text)
    
    # Collapse multiple spaces/tabs into single space
    text = re.sub(r"[ \t]+", " ", text)
    
    # Remove trailing spaces at end of lines
    text = re.sub(r" +\n", "\n", text)
    
    # Remove zero-width spaces and other invisible characters
    text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
    
    return text.strip()


def _extract_txt(uploaded_file) -> ExtractionResult:
    raw = uploaded_file.read()
    if isinstance(raw, str):
        return ExtractionResult(text=_normalize_text(raw))
    for encoding in ("utf-8", "utf-8-sig", "cp1251", "latin-1"):
        try:
            return ExtractionResult(text=_normalize_text(raw.decode(encoding)))
        except Exception:
            continue
    return ExtractionResult(text="", warning="Не удалось декодировать TXT файл")


def _extract_pdf_from_bytes(raw: bytes) -> ExtractionResult:
    try:
        from pypdf import PdfReader
    except Exception:
        return ExtractionResult(text="", warning="Для PDF нужен пакет pypdf")

    reader = PdfReader(BytesIO(raw))
    parts = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            parts.append("")
    text = _normalize_text("\n".join(parts))
    # OCR fallback for scanned/image PDFs where text layer is missing.
    if len(text) >= 120:
        return ExtractionResult(text=text)

    ocr_result = _extract_pdf_via_ocr(raw)
    if ocr_result.text:
        return ocr_result
    if text:
        return ExtractionResult(
            text=text,
            warning="Извлечен только частичный текст PDF. OCR недоступен или не дал результата.",
        )
    return ExtractionResult(text="", warning=ocr_result.warning or "PDF не содержит извлекаемого текста (возможно, скан/изображение)")


def _extract_pdf_via_ocr(raw: bytes) -> ExtractionResult:
    """OCR fallback pipeline for scanned PDF pages with image preprocessing."""
    try:
        from pdf2image import convert_from_bytes
        import pytesseract
        from PIL import ImageEnhance, ImageFilter
    except Exception:
        return ExtractionResult(text="", warning="Для OCR PDF установите pytesseract и pdf2image")

    try:
        # Higher DPI for better OCR quality
        try:
            images = convert_from_bytes(raw, dpi=300)
        except TypeError:
            images = convert_from_bytes(raw)
    except Exception:
        return ExtractionResult(text="", warning="Не удалось преобразовать PDF в изображения для OCR")

    ocr_chunks = []
    for idx, image in enumerate(images[:50]):  # safety cap
        try:
            # Preprocess image for better OCR when PIL image object is available.
            if hasattr(image, "convert"):
                image = image.convert('L')
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(2.0)
                image = image.filter(ImageFilter.SHARPEN)

            # OCR with custom config for better accuracy.
            custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'
            try:
                chunk = pytesseract.image_to_string(image, lang="rus+eng", config=custom_config)
            except TypeError:
                # Test/mocked implementations may not accept "config".
                chunk = pytesseract.image_to_string(image, lang="rus+eng")
            
            if chunk and len(chunk.strip()) > 10:  # Only add meaningful chunks
                ocr_chunks.append(chunk)
        except Exception as e:
            print(f"OCR failed on page {idx+1}: {e}")
            continue

    text = _normalize_text("\n".join(ocr_chunks))
    if text and len(text) > 10:
        return ExtractionResult(text=text, warning="Текст извлечен через OCR (распознано страниц: {})".format(len(ocr_chunks)))
    return ExtractionResult(text="", warning="OCR не смог распознать текст PDF")


def _extract_docx_from_bytes(raw: bytes) -> ExtractionResult:
    try:
        from docx import Document
    except Exception:
        return ExtractionResult(text="", warning="Для DOCX нужен пакет python-docx")

    doc = Document(BytesIO(raw))
    blocks = []
    for p in doc.paragraphs:
        if p.text and p.text.strip():
            blocks.append(p.text.strip())
    text = _normalize_text("\n".join(blocks))
    if not text:
        return ExtractionResult(text="", warning="DOCX пустой или не содержит текста")
    return ExtractionResult(text=text)


def extract_text_from_uploaded_file(uploaded_file) -> ExtractionResult:
    name = (uploaded_file.name or "").lower()
    raw = uploaded_file.read()
    if hasattr(uploaded_file, "seek"):
        try:
            uploaded_file.seek(0)
        except Exception:
            pass

    if name.endswith(".txt"):
        temp = BytesIO(raw)
        temp.name = name
        return _extract_txt(temp)
    if name.endswith(".pdf"):
        return _extract_pdf_from_bytes(raw)
    if name.endswith(".docx"):
        return _extract_docx_from_bytes(raw)
    return ExtractionResult(text="", warning="Неподдерживаемый формат файла")
