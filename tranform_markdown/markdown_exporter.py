"""Export cleaned, reflowed PDF text to Markdown."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from .config import PipelineConfig
from .models import TextLine


class MarkdownExporter:
    """Render reflowed PDF text as clean Markdown without chunking."""

    _BULLET_RE = re.compile(r"^\s*(?:[-*]|\u2022|\u2023|\u25e6)\s+")
    _NUMBERED_RE = re.compile(r"^\s*(?:\(?[a-zA-Z0-9]{1,3}\)|\d+(?:\.\d+)*[.)])\s+")
    _CHAPTER_RE = re.compile(r"^\s*chapter\s+\d+", re.I)
    _SECTION_RE = re.compile(r"^\s*section\s+\d+", re.I)
    _NUMBERED_HEADING_RE = re.compile(r"^\s*\d+(?:\.\d+)+\.?\s+\S+")
    _ENDS_SENTENCE_RE = re.compile(r"[.!?]\s*(?:[\"')\]]+)?$")

    def __init__(self, config: PipelineConfig, logger: logging.Logger) -> None:
        self.config = config
        self.logger = logger

    def export(self, source: Path, lines: list[TextLine]) -> str:
        """Convert cleaned and reflowed text lines into Markdown."""

        output: list[str] = [
            f"# {source.stem}",
            "",
            f"<!-- source: {source} -->",
            "",
        ]
        current_page: int | None = None
        in_table = False

        for line in lines:
            page = line.page
            if self.config.include_page_markers and page != current_page:
                if in_table:
                    output.append("```")
                    output.append("")
                    in_table = False
                output.append(f"<!-- page: {page} -->")
                output.append("")
                current_page = page

            text = line.text.strip()
            if not text:
                continue

            if self._is_table_line(text):
                if not in_table:
                    output.append("```text")
                    in_table = True
                output.append(text)
                continue

            if in_table:
                output.append("```")
                output.append("")
                in_table = False

            output.extend(self._render_non_table_line(text))

        if in_table:
            output.append("```")
            output.append("")

        markdown = "\n".join(output).strip() + "\n"
        markdown = re.sub(r"\n{4,}", "\n\n\n", markdown)
        self.logger.info("Exported markdown lines: %s", len(lines))
        return markdown

    def _render_non_table_line(self, text: str) -> list[str]:
        if self._BULLET_RE.match(text):
            return [self._normalize_bullet(text), ""]
        if self._NUMBERED_RE.match(text):
            return [text, ""]
        if self._is_heading(text):
            return [self._render_heading(text), ""]
        return [text, ""]

    def _render_heading(self, text: str) -> str:
        if text.startswith("#"):
            return text
        if self._CHAPTER_RE.match(text):
            return f"# {text}"
        if self._SECTION_RE.match(text):
            return f"## {text}"
        if self._NUMBERED_HEADING_RE.match(text):
            return f"### {text}"
        return f"## {text}"

    @classmethod
    def _normalize_bullet(cls, text: str) -> str:
        return cls._BULLET_RE.sub("- ", text, count=1)

    @staticmethod
    def _is_table_line(text: str) -> bool:
        if "|" in text or "\t" in text:
            return True
        return len(re.findall(r"\S(?: {2,})\S", text)) >= 2

    def _is_heading(self, text: str) -> bool:
        words = text.split()
        if not words or len(words) > self.config.max_heading_words:
            return False
        if len(text) > self.config.max_heading_chars:
            return False
        if self._BULLET_RE.match(text) or self._NUMBERED_RE.match(text):
            return False
        if self._CHAPTER_RE.match(text) or self._SECTION_RE.match(text):
            return True
        if self._NUMBERED_HEADING_RE.match(text):
            return True
        if self._ENDS_SENTENCE_RE.search(text):
            return False
        alpha = [char for char in text if char.isalpha()]
        if not alpha:
            return False
        uppercase_ratio = sum(char.isupper() for char in alpha) / len(alpha)
        return uppercase_ratio > 0.72 or len(words) <= 7
