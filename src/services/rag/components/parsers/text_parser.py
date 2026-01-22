"""Text file parser."""

import aiofiles

from ..base import BaseParser
from ...types import Document


class TextParser(BaseParser):
    """Parser for plain text files."""

    SUPPORTED_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".yaml", ".yml"}

    async def parse(self, file_path: str) -> Document:
        """Parse a text file into a Document.

        Args:
            file_path: Path to the text file.

        Returns:
            Parsed Document object.
        """
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            content = await f.read()

        return Document(
            content=content,
            file_path=file_path,
            metadata={
                "parser": "text",
                "encoding": "utf-8",
            },
        )

    def supports(self, file_path: str) -> bool:
        """Check if this parser supports the given file.

        Args:
            file_path: Path to check.

        Returns:
            True if file has a supported text extension.
        """
        lower_path = file_path.lower()
        return any(lower_path.endswith(ext) for ext in self.SUPPORTED_EXTENSIONS)
