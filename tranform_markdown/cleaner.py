"""Conservative document cleaning for retrieval."""

from __future__ import annotations

import collections
import logging
import re
import unicodedata

from .config import PipelineConfig
from .models import PageText


class DocumentCleaner:
    """Remove repetitive layout noise without changing semantic content."""

    _PAGE_NUMBER_RE = re.compile(
        r"^\s*(?:page\s*)?\d+\s*(?:of|/|-)?\s*\d*\s*$",
        flags=re.IGNORECASE,
    )
    _WATERMARK_RE = re.compile(r"^\s*(?:draft|confidential|sample|watermark)\s*$", re.I)
    _MOJIBAKE_REPLACEMENTS = {
        "\u00e2\u20ac\u2122": "'",
        "\u00e2\u20ac\u0153": '"',
        "\u00e2\u20ac\ufffd": '"',
        "\u00e2\u20ac\u201d": "-",
        "\u00e2\u20ac\u201c": "-",
        "\u00e2\u20ac\u00a2": "-",
        "\u00e2\u20ac\u00a6": "...",
        "\u00c2\u00a0": " ",
        "\u00c2\u00ae": "(R)",
        "\u00c2\u00a9": "(C)",
    }

    def __init__(self, config: PipelineConfig, logger: logging.Logger) -> None:
        self.config = config
        self.logger = logger

    def clean(self, pages: list[PageText]) -> list[PageText]:
        """Clean all pages and remove detected repeated headers/footers."""

        repeated_lines = self._detect_repeated_layout_lines(pages)
        cleaned_pages: list[PageText] = []
        for page in pages:
            lines = []
            for raw_line in self._normalize_text(page.text).splitlines():
                line = raw_line.strip()
                comparable = self._comparable_line(line)
                if not line:
                    lines.append("")
                    continue
                if comparable in repeated_lines:
                    continue
                if self._PAGE_NUMBER_RE.match(line) or self._WATERMARK_RE.match(line):
                    continue
                lines.append(line)
            text = self._dedupe_empty_lines("\n".join(lines))
            cleaned_pages.append(PageText(page=page.page, text=text, source=page.source))
        self.logger.info("Cleaned pages: %s", len(cleaned_pages))
        return cleaned_pages

    def _detect_repeated_layout_lines(self, pages: list[PageText]) -> set[str]:
        if len(pages) < 3:
            return set()

        counter: collections.Counter[str] = collections.Counter()
        for page in pages:
            normalized = self._normalize_text(page.text)
            candidates = normalized.splitlines()[:4] + normalized.splitlines()[-4:]
            for line in candidates:
                comparable = self._comparable_line(line)
                if 3 <= len(comparable) <= 120 and not self._PAGE_NUMBER_RE.match(comparable):
                    counter[comparable] += 1

        threshold = max(2, int(len(pages) * self.config.min_repeated_line_ratio))
        repeated = {line for line, count in counter.items() if count >= threshold}
        if repeated:
            self.logger.info("Removed repeated header/footer candidates: %s", len(repeated))
        return repeated

    @staticmethod
    def _normalize_text(text: str) -> str:
        text = unicodedata.normalize("NFC", text)
        text = DocumentCleaner._repair_mojibake(text)
        for broken, replacement in DocumentCleaner._MOJIBAKE_REPLACEMENTS.items():
            text = text.replace(broken, replacement)
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = text.replace("\u00a0", " ").replace("\u200b", "")
        text = re.sub(r"[ \t\f\v]+", " ", text)
        return text

    @staticmethod
    def _repair_mojibake(text: str) -> str:
        markers = ("\u00e2", "\u00c2", "\u00c3")
        if not any(marker in text for marker in markers):
            return text
        try:
            repaired = text.encode("cp1252").decode("utf-8")
        except UnicodeError:
            return text

        original_score = sum(text.count(marker) for marker in markers)
        repaired_score = sum(repaired.count(marker) for marker in markers)
        return repaired if repaired_score < original_score else text

    @staticmethod
    def _dedupe_empty_lines(text: str) -> str:
        return re.sub(r"\n{3,}", "\n\n", text).strip()

    @staticmethod
    def _comparable_line(line: str) -> str:
        line = unicodedata.normalize("NFC", line)
        line = re.sub(r"\d+", "#", line)
        line = re.sub(r"\s+", " ", line).strip().lower()
        return line
