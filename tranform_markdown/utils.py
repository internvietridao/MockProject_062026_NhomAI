"""Utility helpers shared by pipeline modules."""

from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path


LOGGER_NAME = "pdf_markdown_pipeline"


def configure_logging(level: str) -> logging.Logger:
    """Configure process-wide logging and return the pipeline logger."""

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    return logging.getLogger(LOGGER_NAME)


def stable_document_slug(path: Path) -> str:
    """Create a stable, readable document slug for output filenames."""

    slug = re.sub(r"[^A-Za-z0-9]+", "_", path.stem).strip("_")
    if not slug:
        slug = hashlib.sha1(str(path).encode("utf-8")).hexdigest()[:10]
    return slug[:48]


def write_markdown(text: str, output_path: Path) -> None:
    """Write cleaned Markdown text using UTF-8."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
