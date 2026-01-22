"""Data structures for Research Pipeline.

Provides the core data structures for managing multi-agent research:
- ToolTrace: Records individual tool calls with citations
- TopicBlock: Represents a research topic with its state and traces
- DynamicTopicQueue: Manages the queue of topics to research

Based on DeepTutor's research pipeline architecture.
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class TopicStatus(str, Enum):
    """Status of a topic in the research queue."""

    PENDING = "pending"
    RESEARCHING = "researching"
    COMPLETED = "completed"
    FAILED = "failed"


class ToolType(str, Enum):
    """Types of research tools available."""

    RAG_SEARCH = "rag_search"
    WEB_SEARCH = "web_search"
    STOCK_DATA = "stock_data"
    FINANCIALS = "financials"
    NEWS_SEARCH = "news_search"
    YOUTUBE = "youtube"
    TECHNICAL_ANALYSIS = "technical_analysis"
    FUNDAMENTAL_ANALYSIS = "fundamental_analysis"


# Maximum size for raw answer storage (50KB)
MAX_RAW_ANSWER_SIZE = 50 * 1024


@dataclass
class ToolTrace:
    """Record of a single tool call during research.

    Attributes:
        tool_id: Unique identifier for this tool call.
        citation_id: Reference ID for citations (e.g., CIT-1-01).
        tool_type: Type of tool used.
        query: Query or parameters passed to the tool.
        raw_answer: Full response from the tool (auto-truncated).
        summary: Compressed summary of the response.
        timestamp: When the tool was called.
        raw_answer_truncated: Whether the raw answer was truncated.
        raw_answer_original_size: Original size before truncation.
        metadata: Additional metadata.
    """

    tool_id: str
    citation_id: str
    tool_type: str
    query: str
    raw_answer: str
    summary: str
    timestamp: str = ""
    raw_answer_truncated: bool = False
    raw_answer_original_size: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

        # Auto-truncate raw answer if too large
        if len(self.raw_answer) > MAX_RAW_ANSWER_SIZE:
            self.raw_answer_original_size = len(self.raw_answer)
            self.raw_answer = self._truncate_answer(self.raw_answer)
            self.raw_answer_truncated = True

    def _truncate_answer(self, answer: str) -> str:
        """Truncate answer while trying to preserve JSON structure."""
        if len(answer) <= MAX_RAW_ANSWER_SIZE:
            return answer

        # Try to parse as JSON and truncate cleanly
        try:
            data = json.loads(answer)
            # If it's a list, truncate items
            if isinstance(data, list) and len(data) > 5:
                truncated = data[:5]
                truncated.append({"_truncated": f"... {len(data) - 5} more items"})
                return json.dumps(truncated, ensure_ascii=False)
            # If dict, try to truncate long string values
            elif isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, str) and len(value) > 1000:
                        data[key] = value[:1000] + "... [truncated]"
                return json.dumps(data, ensure_ascii=False)[:MAX_RAW_ANSWER_SIZE]
        except (json.JSONDecodeError, TypeError):
            pass

        # Fallback: simple truncation with marker
        return answer[:MAX_RAW_ANSWER_SIZE - 50] + "\n... [truncated]"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ToolTrace":
        """Create from dictionary."""
        return cls(
            tool_id=data.get("tool_id", ""),
            citation_id=data.get("citation_id", ""),
            tool_type=data.get("tool_type", ""),
            query=data.get("query", ""),
            raw_answer=data.get("raw_answer", ""),
            summary=data.get("summary", ""),
            timestamp=data.get("timestamp", ""),
            raw_answer_truncated=data.get("raw_answer_truncated", False),
            raw_answer_original_size=data.get("raw_answer_original_size", 0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class TopicBlock:
    """A research topic block with its state and tool traces.

    Represents a single unit of research that can be scheduled
    and processed by the research pipeline.

    Attributes:
        block_id: Unique identifier for this block.
        sub_topic: The topic to research.
        overview: Description of what to research.
        status: Current status of the topic.
        tool_traces: List of tool calls made for this topic.
        iteration_count: Number of research iterations completed.
        created_at: When the block was created.
        updated_at: When the block was last updated.
        metadata: Additional metadata (e.g., symbols, market).
    """

    block_id: str
    sub_topic: str
    overview: str
    status: TopicStatus = TopicStatus.PENDING
    tool_traces: list[ToolTrace] = field(default_factory=list)
    iteration_count: int = 0
    created_at: str = ""
    updated_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

        # Convert string status to enum if needed
        if isinstance(self.status, str):
            self.status = TopicStatus(self.status)

    def add_tool_trace(self, trace: ToolTrace) -> None:
        """Add a tool trace to this block."""
        self.tool_traces.append(trace)
        self.updated_at = datetime.utcnow().isoformat()

    def get_latest_trace(self) -> ToolTrace | None:
        """Get the most recent tool trace."""
        return self.tool_traces[-1] if self.tool_traces else None

    def get_all_summaries(self) -> str:
        """Get all summaries concatenated."""
        return "\n\n".join(trace.summary for trace in self.tool_traces if trace.summary)

    def get_traces_by_tool(self, tool_type: str) -> list[ToolTrace]:
        """Get all traces for a specific tool type."""
        return [t for t in self.tool_traces if t.tool_type == tool_type]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "block_id": self.block_id,
            "sub_topic": self.sub_topic,
            "overview": self.overview,
            "status": self.status.value,
            "tool_traces": [t.to_dict() for t in self.tool_traces],
            "iteration_count": self.iteration_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TopicBlock":
        """Create from dictionary."""
        traces = [
            ToolTrace.from_dict(t) for t in data.get("tool_traces", [])
        ]
        return cls(
            block_id=data.get("block_id", ""),
            sub_topic=data.get("sub_topic", ""),
            overview=data.get("overview", ""),
            status=TopicStatus(data.get("status", "pending")),
            tool_traces=traces,
            iteration_count=data.get("iteration_count", 0),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            metadata=data.get("metadata", {}),
        )


class DynamicTopicQueue:
    """Dynamic queue for managing research topics.

    Provides a queue-based approach to managing research topics
    with automatic state persistence and deduplication.

    Attributes:
        research_id: Unique identifier for this research session.
        blocks: List of topic blocks in the queue.
        max_length: Maximum number of topics allowed (None for unlimited).
        state_file: Path for auto-persistence (None to disable).
    """

    def __init__(
        self,
        research_id: str,
        max_length: int | None = 50,
        state_file: str | Path | None = None,
    ):
        """Initialize the queue.

        Args:
            research_id: Unique identifier for this research.
            max_length: Maximum queue capacity.
            state_file: Path for auto-persistence.
        """
        self.research_id = research_id
        self.blocks: list[TopicBlock] = []
        self.block_counter = 0
        self.max_length = max_length
        self.state_file = Path(state_file) if state_file else None
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = self.created_at

    def add_block(
        self,
        sub_topic: str,
        overview: str,
        metadata: dict[str, Any] | None = None,
    ) -> TopicBlock | None:
        """Add a new topic block to the queue.

        Args:
            sub_topic: The topic to research.
            overview: Description of what to research.
            metadata: Additional metadata.

        Returns:
            The created TopicBlock, or None if queue is full or topic exists.
        """
        # Check capacity
        if self.max_length and len(self.blocks) >= self.max_length:
            logger.warning(f"Queue at capacity ({self.max_length}), cannot add: {sub_topic}")
            return None

        # Check for duplicates
        if self.has_topic(sub_topic):
            logger.debug(f"Topic already in queue: {sub_topic}")
            return None

        # Create new block
        self.block_counter += 1
        block = TopicBlock(
            block_id=f"block_{self.block_counter}",
            sub_topic=sub_topic,
            overview=overview,
            metadata=metadata or {},
        )

        self.blocks.append(block)
        self.updated_at = datetime.utcnow().isoformat()
        self._auto_save()

        logger.debug(f"Added topic block: {block.block_id} - {sub_topic}")
        return block

    def get_pending_block(self) -> TopicBlock | None:
        """Get the next pending topic block.

        Returns:
            The next pending block, or None if no pending blocks.
        """
        for block in self.blocks:
            if block.status == TopicStatus.PENDING:
                return block
        return None

    def get_block_by_id(self, block_id: str) -> TopicBlock | None:
        """Get a block by its ID.

        Args:
            block_id: Block identifier.

        Returns:
            The block if found, None otherwise.
        """
        for block in self.blocks:
            if block.block_id == block_id:
                return block
        return None

    def mark_researching(self, block_id: str) -> bool:
        """Mark a block as currently being researched.

        Args:
            block_id: Block identifier.

        Returns:
            True if successful, False if block not found.
        """
        block = self.get_block_by_id(block_id)
        if block:
            block.status = TopicStatus.RESEARCHING
            block.updated_at = datetime.utcnow().isoformat()
            self.updated_at = block.updated_at
            self._auto_save()
            return True
        return False

    def mark_completed(self, block_id: str) -> bool:
        """Mark a block as completed.

        Args:
            block_id: Block identifier.

        Returns:
            True if successful, False if block not found.
        """
        block = self.get_block_by_id(block_id)
        if block:
            block.status = TopicStatus.COMPLETED
            block.updated_at = datetime.utcnow().isoformat()
            self.updated_at = block.updated_at
            self._auto_save()
            return True
        return False

    def mark_failed(self, block_id: str) -> bool:
        """Mark a block as failed.

        Args:
            block_id: Block identifier.

        Returns:
            True if successful, False if block not found.
        """
        block = self.get_block_by_id(block_id)
        if block:
            block.status = TopicStatus.FAILED
            block.updated_at = datetime.utcnow().isoformat()
            self.updated_at = block.updated_at
            self._auto_save()
            return True
        return False

    def has_topic(self, sub_topic: str) -> bool:
        """Check if a topic already exists in the queue.

        Uses case-insensitive comparison with normalization.

        Args:
            sub_topic: Topic to check.

        Returns:
            True if topic exists.
        """
        normalized = self._normalize_topic(sub_topic)
        for block in self.blocks:
            if self._normalize_topic(block.sub_topic) == normalized:
                return True
        return False

    def _normalize_topic(self, topic: str) -> str:
        """Normalize a topic string for comparison."""
        return topic.lower().strip()

    def get_statistics(self) -> dict[str, Any]:
        """Get queue statistics.

        Returns:
            Dictionary with queue stats.
        """
        total_tool_calls = sum(len(b.tool_traces) for b in self.blocks)
        status_counts = {status.value: 0 for status in TopicStatus}

        for block in self.blocks:
            status_counts[block.status.value] += 1

        return {
            "research_id": self.research_id,
            "total_blocks": len(self.blocks),
            "pending": status_counts["pending"],
            "researching": status_counts["researching"],
            "completed": status_counts["completed"],
            "failed": status_counts["failed"],
            "total_tool_calls": total_tool_calls,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def get_completed_blocks(self) -> list[TopicBlock]:
        """Get all completed blocks."""
        return [b for b in self.blocks if b.status == TopicStatus.COMPLETED]

    def get_all_summaries(self) -> str:
        """Get all summaries from completed blocks."""
        summaries = []
        for block in self.get_completed_blocks():
            if block.tool_traces:
                block_summary = f"## {block.sub_topic}\n\n{block.get_all_summaries()}"
                summaries.append(block_summary)
        return "\n\n---\n\n".join(summaries)

    def _auto_save(self) -> None:
        """Auto-save state if state_file is set."""
        if self.state_file:
            self.save_to_json(self.state_file)

    def save_to_json(self, path: str | Path) -> None:
        """Save queue state to JSON file.

        Args:
            path: File path to save to.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "research_id": self.research_id,
            "block_counter": self.block_counter,
            "max_length": self.max_length,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "blocks": [b.to_dict() for b in self.blocks],
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.debug(f"Saved queue state to {path}")

    @classmethod
    def load_from_json(cls, path: str | Path) -> "DynamicTopicQueue":
        """Load queue state from JSON file.

        Args:
            path: File path to load from.

        Returns:
            DynamicTopicQueue instance.
        """
        path = Path(path)

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        queue = cls(
            research_id=data.get("research_id", ""),
            max_length=data.get("max_length"),
            state_file=path,
        )
        queue.block_counter = data.get("block_counter", 0)
        queue.created_at = data.get("created_at", "")
        queue.updated_at = data.get("updated_at", "")
        queue.blocks = [TopicBlock.from_dict(b) for b in data.get("blocks", [])]

        logger.debug(f"Loaded queue state from {path}")
        return queue

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "research_id": self.research_id,
            "block_counter": self.block_counter,
            "max_length": self.max_length,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "blocks": [b.to_dict() for b in self.blocks],
            "statistics": self.get_statistics(),
        }

    def __len__(self) -> int:
        return len(self.blocks)

    def __iter__(self):
        return iter(self.blocks)
