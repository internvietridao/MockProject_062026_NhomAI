"""Shared data models for PDF preprocessing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PageText:
    """Text extracted from one PDF page."""

    page: int
    text: str
    source: Path


@dataclass(frozen=True)
class TextLine:
    """A cleaned/reflowed text unit with page provenance."""

    text: str
    page: int
    end_page: int | None = None

