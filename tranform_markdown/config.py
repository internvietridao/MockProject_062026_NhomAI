"""Configuration for the PDF preprocessing pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class PipelineConfig:
    """Runtime configuration kept out of processing logic."""

    input_dir: Path = PROJECT_ROOT / "data_process" / "pdf_file"
    output_dir: Path = PROJECT_ROOT / "data" / "output"
    markdown_output_dirname: str = "markdown"
    markdown_extension: str = ".md"
    include_page_markers: bool = True
    log_level: str = "INFO"
    min_repeated_line_ratio: float = 0.55
    max_heading_words: int = 18
    max_heading_chars: int = 140
    max_line_join_gap_chars: int = 110
    table_min_columns: int = 2

    @property
    def markdown_output_dir(self) -> Path:
        """Resolved Markdown output directory."""

        return self.output_dir / self.markdown_output_dirname
