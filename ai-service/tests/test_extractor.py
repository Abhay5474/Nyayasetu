import io

import pymupdf as fitz
import pytest
from PIL import Image

from app.extraction.extractor import DocumentExtractor, ExtractionError, sniff_kind
from tests.conftest import make_pdf


class FakeOcr:
    name = "fake"

    def __init__(self, text="Scanned order: the appellant must appear before the Commission on 12/03/2025."):
        self.text, self.calls = text, 0

    def image_to_text(self, image):
        self.calls += 1
        return self.text


@pytest.fixture
def extractor(settings):
    ocr = FakeOcr()
    return DocumentExtractor(settings, ocr_factory=lambda _s: ocr), ocr


def test_digital_pdf_skips_ocr(extractor):
    ex, ocr = extractor
    pdf = make_pdf(["The Public Information Officer must reply to the RTI application within thirty days of receipt."])
    r = ex.extract(pdf)
    assert r.method == "digital" and r.page_count == 1 and ocr.calls == 0
    assert "Public Information Officer" in r.text and r.language_hint == "en"


def test_scanned_pdf_falls_back_to_ocr(extractor):
    ex, ocr = extractor
    src = fitz.open()
    page = src.new_page()
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 200, 200), False)
    pix.set_rect(pix.irect, (240, 240, 240))
    page.insert_image(page.rect, pixmap=pix)  # image-only page => no text layer
    r = ex.extract(src.tobytes())
    assert r.method == "ocr" and r.ocr_pages == [1] and ocr.calls == 1
    assert "appellant must appear" in r.text


def test_mixed_pdf(extractor):
    ex, ocr = extractor
    doc = fitz.open(stream=make_pdf(["A digital page with plenty of readable text for the extractor to keep as is."]), filetype="pdf")
    blank = doc.new_page()
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 100, 100), False)
    pix.set_rect(pix.irect, (200, 200, 200))
    blank.insert_image(blank.rect, pixmap=pix)
    r = ex.extract(doc.tobytes())
    assert r.method == "mixed" and r.ocr_pages == [2]


def test_image_upload_uses_ocr(extractor):
    ex, ocr = extractor
    buf = io.BytesIO()
    Image.new("RGB", (300, 300), "white").save(buf, "PNG")
    r = ex.extract(buf.getvalue())
    assert r.method == "ocr" and ocr.calls == 1


def test_rejects_unknown_and_empty(extractor):
    ex, _ = extractor
    with pytest.raises(ExtractionError):
        sniff_kind(b"MZ\x90\x00 this is an exe")
    with pytest.raises(ExtractionError):
        ex.extract(b"%PDF-1.4 garbage that is not a pdf")
    ex2 = DocumentExtractor(ex.settings, ocr_factory=lambda _s: FakeOcr(""))
    with pytest.raises(ExtractionError):
        ex2.extract(make_pdf([""]))
