"""Text reflow for PDF layout line breaks."""

from __future__ import annotations

import logging
import re

from .config import PipelineConfig
from .models import PageText, TextLine


class TextReflow:
    """Join wrapped PDF lines while preserving true document structure."""

    _BULLET_RE = re.compile(r"^\s*(?:[-*•‣◦]|\(?[a-zA-Z0-9]{1,3}\)|[0-9]+[.)])\s+")
    _NUMBERED_RE = re.compile(r"^\s*(?:\d+(?:\.\d+)*[.)])\s+")
    _ENDS_SENTENCE_RE = re.compile(r"[.!?:;]\s*(?:[\"')\]]+)?$")
    _HEADING_NUMBER_RE = re.compile(r"^\s*(?:chapter|section|appendix)?\s*\d+(?:\.\d+)*\.?\s+\S+", re.I)

    def __init__(self, config: PipelineConfig, logger: logging.Logger) -> None:
        self.config = config
        self.logger = logger

    def reflow(self, pages: list[PageText]) -> list[TextLine]:
        """Return paragraph-like lines with original page provenance."""

        output: list[TextLine] = []
        buffer: list[TextLine] = []

        for page in pages:
            raw_lines = page.text.splitlines()
            for raw in raw_lines:
                line = raw.strip()
                if not line:
                    self._flush(buffer, output)
                    buffer = []
                    continue
                current = TextLine(text=line, page=page.page)
                if not buffer:
                    buffer.append(current)
                    continue
                previous = buffer[-1]
                if self._should_join(previous.text, current.text):
                    buffer[-1] = TextLine(
                        text=self._join_lines(previous.text, current.text),
                        page=previous.page,
                        end_page=current.end_page or current.page,
                    )
                else:
                    self._flush(buffer, output)
                    buffer = [current]

        self._flush(buffer, output)

        self.logger.info("Reflowed text units: %s", len(output))
        return output

    def _should_join(self, previous: str, current: str) -> bool:
        if self._is_table_line(previous) or self._is_table_line(current):
            return False
        if self._is_list_item(current) or self._is_heading(current):
            return False
        if self._is_list_item(previous):
            return self._is_continuation_line(current)
        if self._is_heading(previous):
            return False
        if previous.endswith("-") and not previous.endswith((" -", " --")):
            return True
        if self._ENDS_SENTENCE_RE.search(previous):
            return False
        if len(previous) > self.config.max_line_join_gap_chars:
            return False
        return self._is_continuation_line(current)

    @staticmethod
    def _join_lines(previous: str, current: str) -> str:
        if previous.endswith("-") and not previous.endswith((" -", " --")):
            return previous[:-1] + current
        return f"{previous} {current}"

    def _is_heading(self, line: str) -> bool:
        words = line.split()
        if not words or len(words) > self.config.max_heading_words:
            return False
        if len(line) > self.config.max_heading_chars:
            return False
        if self._BULLET_RE.match(line):
            return False
        if self._HEADING_NUMBER_RE.match(line):
            return True
        alpha = [char for char in line if char.isalpha()]
        if alpha and sum(char.isupper() for char in alpha) / len(alpha) > 0.75:
            return True
        return not self._ENDS_SENTENCE_RE.search(line) and len(words) <= 8

    def _is_table_line(self, line: str) -> bool:
        if "|" in line or "\t" in line:
            return True
        return len(re.findall(r"\S(?: {2,})\S", line)) >= self.config.table_min_columns

    def _is_list_item(self, line: str) -> bool:
        return bool(self._BULLET_RE.match(line) or self._NUMBERED_RE.match(line))

    @staticmethod
    def _is_continuation_line(line: str) -> bool:
        return bool(line) and not re.match(r"^[A-Z][A-Z\s]{2,}$", line)

    @staticmethod
    def _flush(buffer: list[TextLine], output: list[TextLine]) -> None:
        output.extend(item for item in buffer if item.text.strip())
