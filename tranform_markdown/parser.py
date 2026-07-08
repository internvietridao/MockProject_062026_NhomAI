"""PDF parsing with PyMuPDF."""

from __future__ import annotations

import logging
from pathlib import Path

import fitz

from .models import PageText


class PDFParser:
    """Extract page-level text from PDFs while preserving page order."""

    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger

    def parse(self, pdf_path: Path) -> list[PageText]:
        """Read all pages from a PDF without OCR."""

        pages: list[PageText] = []
        try:
            with fitz.open(pdf_path) as document:
                for index in range(document.page_count):
                    page_number = index + 1
                    self.logger.info("Current page %s/%s", page_number, document.page_count)
                    try:
                        page = document.load_page(index)
                        text = page.get_text("text", sort=True) or ""
                        pages.append(PageText(page=page_number, text=text, source=pdf_path))
                    except Exception as exc:  # noqa: BLE001 - continue on bad pages.
                        self.logger.warning(
                            "Page parse failed | file=%s | page=%s | error=%s",
                            pdf_path,
                            page_number,
                            exc,
                        )
        except Exception as exc:  # noqa: BLE001 - continue on bad files.
            self.logger.warning("PDF parse failed | file=%s | error=%s", pdf_path, exc)
        return pages
