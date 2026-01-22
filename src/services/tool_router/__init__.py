"""Tool Router Service.

Provides unified tool execution with:
- Retry logic with configurable retries
- Timeout handling
- Error handling and fallback
- Result summarization (NoteAgent pattern)
"""

from .types import ToolResult, ToolConfig, ToolStatus
from .router import ToolRouter, get_tool_router

__all__ = [
    "ToolResult",
    "ToolConfig",
    "ToolStatus",
    "ToolRouter",
    "get_tool_router",
]
