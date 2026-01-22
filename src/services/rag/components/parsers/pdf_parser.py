"""PDF file parser."""

import asyncio
from pathlib import Path
from typing import Any

from ..base import BaseParser
from ...types import Document, Chunk


class PDFParser(BaseParser):
    """Parser for PDF files using pdfplumber."""

    SUPPORTED_EXTENSIONS = {".pdf"}

    async def parse(self, file_path: str) -> Document:
        """Parse a PDF file into a Document.

        Args:
            file_path: Path to the PDF file.

        Returns:
            Parsed Document object with text and table chunks.
        """
        # Run in thread pool since pdfplumber is synchronous
        return await asyncio.to_thread(self._parse_sync, file_path)

    def _parse_sync(self, file_path: str) -> Document:
        """Synchronous PDF parsing implementation."""
        try:
            import pdfplumber
        except ImportError:
            raise ImportError(
                "pdfplumber is required for PDF parsing. "
                "Install with: pip install pdfplumber"
            )

        all_text: list[str] = []
        chunks: list[Chunk] = []

        with pdfplumber.open(file_path) as pdf:
            metadata: dict[str, Any] = {
                "parser": "pdf",
                "total_pages": len(pdf.pages),
                "pdf_info": pdf.metadata or {},
            }

            for page_num, page in enumerate(pdf.pages, start=1):
                # Extract text
                text = page.extract_text() or ""
                if text.strip():
                    all_text.append(text)
                    chunks.append(
                        Chunk(
                            content=text,
                            chunk_type="text",
                            metadata={
                                "page": page_num,
                                "source": file_path,
                            },
                        )
                    )

                # Extract tables
                tables = page.extract_tables()
                for table_idx, table in enumerate(tables):
                    if table:
                        table_text = self._table_to_text(table)
                        if table_text.strip():
                            chunks.append(
                                Chunk(
                                    content=table_text,
                                    chunk_type="table",
                                    metadata={
                                        "page": page_num,
                                        "table_index": table_idx,
                                        "source": file_path,
                                    },
                                )
                            )

        document = Document(
            content="\n\n".join(all_text),
            file_path=file_path,
            metadata=metadata,
            chunks=chunks,
        )

        return document

    def _table_to_text(self, table: list[list[str | None]]) -> str:
        """Convert table to text format.

        Args:
            table: 2D list of table cells.

        Returns:
            Text representation of the table.
        """
        rows: list[str] = []
        for row in table:
            cells = [str(cell) if cell else "" for cell in row]
            rows.append(" | ".join(cells))
        return "\n".join(rows)

    def supports(self, file_path: str) -> bool:
        """Check if this parser supports the given file.

        Args:
            file_path: Path to check.

        Returns:
            True if file is a PDF.
        """
        return file_path.lower().endswith(".pdf")
