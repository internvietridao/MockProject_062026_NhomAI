"""CLI entrypoint for the PDF-to-Markdown preprocessing pipeline."""

from __future__ import annotations

from src.config import PipelineConfig
from src.pipeline import PDFMarkdownPipeline
from src.utils import configure_logging


def main() -> None:
    """Run the configured PDF-to-Markdown preprocessing pipeline."""

    config = PipelineConfig()
    logger = configure_logging(config.log_level)
    pipeline = PDFMarkdownPipeline(config, logger)
    pipeline.run()


if __name__ == "__main__":
    main()
