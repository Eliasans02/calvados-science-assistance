from io import BytesIO

from src.extraction.text_extractor import (
    ExtractionResult,
    _normalize_text,
    extract_text_from_uploaded_file,
)


class FakeUpload(BytesIO):
    def __init__(self, data: bytes, name: str):
        super().__init__(data)
        self.name = name


def test_normalize_text_compacts_whitespace():
    text = "line1\r\n\r\n\r\nline2   \t  text"
    assert _normalize_text(text) == "line1\n\nline2 text"


def test_txt_extraction_cp1251():
    raw = "Привет мир".encode("cp1251")
    file = FakeUpload(raw, "doc.txt")
    result = extract_text_from_uploaded_file(file)
    assert isinstance(result, ExtractionResult)
    assert "Привет" in result.text
    assert result.warning is None


def test_docx_extraction(monkeypatch):
    class DummyParagraph:
        def __init__(self, text):
            self.text = text

    class DummyDoc:
        paragraphs = [DummyParagraph("Строка 1"), DummyParagraph("Строка 2")]

    def fake_document(_uploaded):
        return DummyDoc()

    import src.extraction.text_extractor as extractor

    monkeypatch.setattr(extractor, "Document", fake_document, raising=False)
    # force module path where function imports from docx import Document
    monkeypatch.setitem(__import__("sys").modules, "docx", type("M", (), {"Document": fake_document}))

    file = FakeUpload(b"dummy", "file.docx")
    result = extract_text_from_uploaded_file(file)
    assert "Строка 1" in result.text
    assert result.warning is None


def test_pdf_empty_warns(monkeypatch):
    class DummyPage:
        def extract_text(self):
            return ""

    class DummyReader:
        pages = [DummyPage()]

    def fake_reader(_uploaded):
        return DummyReader()

    import src.extraction.text_extractor as extractor

    monkeypatch.setitem(__import__("sys").modules, "pypdf", type("M", (), {"PdfReader": fake_reader}))

    file = FakeUpload(b"%PDF-1.4", "scan.pdf")
    result = extract_text_from_uploaded_file(file)
    assert result.text == ""
    assert result.warning is not None


def test_pdf_ocr_fallback(monkeypatch):
    class DummyPage:
        def extract_text(self):
            return ""

    class DummyReader:
        pages = [DummyPage()]

    def fake_reader(_uploaded):
        return DummyReader()

    def fake_convert_from_bytes(_raw):
        return ["img1"]

    class FakeTesseract:
        @staticmethod
        def image_to_string(_img, lang=None):
            return "Распознанный OCR текст"

    import src.extraction.text_extractor as extractor

    monkeypatch.setitem(__import__("sys").modules, "pypdf", type("M", (), {"PdfReader": fake_reader}))
    monkeypatch.setitem(__import__("sys").modules, "pdf2image", type("M", (), {"convert_from_bytes": fake_convert_from_bytes}))
    monkeypatch.setitem(__import__("sys").modules, "pytesseract", FakeTesseract)

    file = FakeUpload(b"%PDF-1.4", "scan.pdf")
    result = extract_text_from_uploaded_file(file)
    assert "OCR текст" in result.text
    assert result.warning is not None
