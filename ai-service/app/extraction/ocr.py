"""OCR engines (Tesseract by default, PaddleOCR optional)."""
from __future__ import annotations

import logging
from typing import Protocol

from PIL import Image, ImageOps

from app.config import Settings

log = logging.getLogger(__name__)


class OcrEngine(Protocol):
    name: str

    def image_to_text(self, image: Image.Image) -> str: ...


def preprocess(image: Image.Image) -> Image.Image:
    """Light clean-up that helps on phone photos / low-contrast scans."""
    img = image.convert("L")
    img = ImageOps.autocontrast(img)
    if min(img.size) < 1000:  # tiny images OCR badly; upscale
        scale = 1000 / min(img.size)
        img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    return img


class TesseractEngine:
    name = "tesseract"

    def __init__(self, langs: str):
        import pytesseract

        self._pt = pytesseract
        self.langs = self._usable_langs(langs)

    def _usable_langs(self, wanted: str) -> str:
        """Drop language packs that are not installed instead of failing every page."""
        try:
            installed = set(self._pt.get_languages(config=""))
        except Exception as exc:  # tesseract binary missing
            raise RuntimeError(f"Tesseract is not available: {exc}") from exc
        usable = [lang for lang in wanted.split("+") if lang in installed]
        missing = [lang for lang in wanted.split("+") if lang not in installed]
        if missing:
            log.warning("Tesseract language packs missing: %s", ",".join(missing))
        if not usable:
            raise RuntimeError(f"None of the requested Tesseract languages are installed: {wanted}")
        return "+".join(usable)

    def image_to_text(self, image: Image.Image) -> str:
        return self._pt.image_to_string(preprocess(image), lang=self.langs, config="--psm 3")


class PaddleEngine:
    """Optional: `pip install paddlepaddle paddleocr`. Uses the Devanagari model for mr/hi."""

    name = "paddle"

    def __init__(self, _langs: str):
        from paddleocr import PaddleOCR  # imported lazily: heavy optional dependency

        self._ocr = PaddleOCR(lang="devanagari", use_angle_cls=True, show_log=False)

    def image_to_text(self, image: Image.Image) -> str:
        import numpy as np

        result = self._ocr.ocr(np.array(preprocess(image).convert("RGB")), cls=True)
        lines: list[str] = []
        for page in result or []:
            for item in page or []:
                lines.append(item[1][0])
        return "\n".join(lines)


_ENGINES = {"tesseract": TesseractEngine, "paddle": PaddleEngine}


def build_ocr_engine(settings: Settings) -> OcrEngine:
    return _ENGINES[settings.ocr_engine](settings.ocr_langs)
