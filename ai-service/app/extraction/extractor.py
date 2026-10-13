"""Digital-PDF text extraction (PyMuPDF) with OCR fallback for scans and images."""
from __future__ import annotations

import io
import logging
from dataclasses import dataclass, field
from typing import Callable

import pymupdf  # PyMuPDF
from PIL import Image

from app.config import Settings
from app.extraction.ocr import OcrEngine, build_ocr_engine
from app.processing.cleaning import clean_pages, detect_language, looks_garbled

log = logging.getLogger(__name__)

IMAGE_MAGIC = {
    b"\x89PNG\r\n\x1a\n": "png",
    b"\xff\xd8\xff": "jpeg",
    b"II*\x00": "tiff",
    b"MM\x00*": "tiff",
    b"BM": "bmp",
}


class ExtractionError(Exception):
    """Raised for unreadable / unsupported / empty documents (maps to HTTP 422)."""


@dataclass
class ExtractionResult:
    text: str
    page_count: int
    method: str
    ocr_pages: list[int] = field(default_factory=list)
    language_hint: str = "unknown"
    warnings: list[str] = field(default_factory=list)


def sniff_kind(data: bytes) -> str:
    """Decide the file type from its bytes, never from the client-supplied name."""
    if data.startswith(b"%PDF-"):
        return "pdf"
    if data[:12].startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image"
    for magic in IMAGE_MAGIC:
        if data.startswith(magic):
            return "image"
    raise ExtractionError("Unsupported file type. Upload a PDF, PNG, JPEG, TIFF, BMP or WEBP file.")


class DocumentExtractor:
    def __init__(self, settings: Settings, ocr_factory: Callable[[Settings], OcrEngine] = build_ocr_engine):
        self.settings = settings
        self._ocr_factory = ocr_factory
        self._ocr: OcrEngine | None = None

    @property
    def ocr(self) -> OcrEngine:
        if self._ocr is None:  # lazily: digital PDFs never need Tesseract
            self._ocr = self._ocr_factory(self.settings)
        return self._ocr

    # ------------------------------------------------------------------ public
    def extract(self, data: bytes) -> ExtractionResult:
        kind = sniff_kind(data)
        result = self._from_pdf(data) if kind == "pdf" else self._from_image(data)
        if len(result.text.strip()) < 20:
            raise ExtractionError(
                "No readable text found. The scan may be too blurry, blank or in an unsupported script."
            )
        result.language_hint = detect_language(result.text)
        return result

    # ------------------------------------------------------------------ pdf
    def _from_pdf(self, data: bytes) -> ExtractionResult:
        s = self.settings
        try:
            doc = pymupdf.open(stream=data, filetype="pdf")
        except Exception as exc:
            raise ExtractionError(f"Could not open PDF: {exc}") from exc
        with doc:
            if doc.needs_pass:
                raise ExtractionError("The PDF is password protected.")
            warnings: list[str] = []
            total = doc.page_count
            if total == 0:
                raise ExtractionError("The PDF has no pages.")
            if total > s.max_pages:
                warnings.append(f"Only the first {s.max_pages} of {total} pages were processed.")
            pages: list[str] = []
            ocr_pages: list[int] = []
            for index in range(min(total, s.max_pages)):
                page = doc[index]
                text = page.get_text("text", sort=True)
                if len(text.strip()) < s.min_chars_per_page or looks_garbled(text):
                    ocr_text = self._ocr_pdf_page(page, index + 1, warnings)
                    if ocr_text.strip() and (len(ocr_text.strip()) > len(text.strip()) or looks_garbled(text)):
                        text = ocr_text
                        ocr_pages.append(index + 1)
                pages.append(text)
        processed = len(pages)
        method = "digital" if not ocr_pages else ("ocr" if len(ocr_pages) == processed else "mixed")
        return ExtractionResult(clean_pages(pages), processed, method, ocr_pages, warnings=warnings)

    def _ocr_pdf_page(self, page: pymupdf.Page, number: int, warnings: list[str]) -> str:
        try:
            pix = page.get_pixmap(dpi=self.settings.ocr_dpi)
            image = Image.open(io.BytesIO(pix.tobytes("png")))
            return self.ocr.image_to_text(image)
        except Exception as exc:
            log.warning("OCR failed on page %s: %s", number, exc)
            warnings.append(f"OCR failed on page {number}: {exc}")
            return ""

    # ------------------------------------------------------------------ images
    def _from_image(self, data: bytes) -> ExtractionResult:
        try:
            image = Image.open(io.BytesIO(data))
            image.load()
        except Exception as exc:
            raise ExtractionError(f"Could not read image: {exc}") from exc
        warnings: list[str] = []
        frames = getattr(image, "n_frames", 1)
        limit = min(frames, self.settings.max_pages)
        if frames > limit:
            warnings.append(f"Only the first {limit} of {frames} image pages were processed.")
        pages: list[str] = []
        for i in range(limit):
            image.seek(i)
            try:
                pages.append(self.ocr.image_to_text(image.copy()))
            except RuntimeError:
                raise ExtractionError("OCR engine is not available on this server.")
        return ExtractionResult(clean_pages(pages), limit, "ocr", list(range(1, limit + 1)), warnings=warnings)
