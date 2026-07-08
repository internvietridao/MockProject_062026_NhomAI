"""Orchestration for PDF preprocessing pipelines."""

from __future__ import annotations

import logging
import time
from pathlib import Path

from .cleaner import DocumentCleaner
from .config import PipelineConfig
from .markdown_exporter import MarkdownExporter
from .parser import PDFParser
from .reflow import TextReflow
from .utils import stable_document_slug, write_markdown


class PDFMarkdownPipeline:
    """Extract PDFs into cleaned Markdown files only."""

    def __init__(self, config: PipelineConfig, logger: logging.Logger) -> None:
        self.config = config
        self.logger = logger
        self.parser = PDFParser(logger)
        self.cleaner = DocumentCleaner(config, logger)
        self.reflow = TextReflow(config, logger)
        self.exporter = MarkdownExporter(config, logger)

    def run(self) -> list[Path]:
        """Process all PDFs from config.input_dir and export Markdown files."""

        started = time.perf_counter()
        output_paths: list[Path] = []
        pdf_files = self._discover_pdfs(self.config.input_dir)
        self.logger.info("Discovered PDF files: %s", len(pdf_files))

        for pdf_path in pdf_files:
            file_started = time.perf_counter()
            self.logger.info("Processing file: %s", pdf_path)
            try:
                pages = self.parser.parse(pdf_path)
                if not pages:
                    self.logger.warning("No pages extracted: %s", pdf_path)
                    continue
                cleaned = self.cleaner.clean(pages)
                reflowed = self.reflow.reflow(cleaned)
                markdown = self.exporter.export(pdf_path, reflowed)
                output_path = self._markdown_path(pdf_path)
                write_markdown(markdown, output_path)
                output_paths.append(output_path)
                self.logger.info(
                    "Finished file: %s | markdown=%s | seconds=%.2f",
                    pdf_path.name,
                    output_path,
                    time.perf_counter() - file_started,
                )
            except Exception as exc:  # noqa: BLE001 - file-level resilience.
                self.logger.warning("File processing failed | file=%s | error=%s", pdf_path, exc)

        self.logger.info("Generated markdown files: %s", len(output_paths))
        self.logger.info("Execution time: %.2f seconds", time.perf_counter() - started)
        return output_paths

    def _markdown_path(self, pdf_path: Path) -> Path:
        filename = stable_document_slug(pdf_path) + self.config.markdown_extension
        return self.config.markdown_output_dir / filename

    @staticmethod
    def _discover_pdfs(input_dir: Path) -> list[Path]:
        return sorted(path for path in input_dir.glob("*.pdf") if path.is_file())
