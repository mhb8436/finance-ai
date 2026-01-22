"""Research Module.

Provides research capabilities:
- ResearchAgent: Legacy single-agent research (backward compatible)
- ResearchPipeline: New multi-agent research pipeline

Data Structures:
- ToolTrace, TopicBlock, DynamicTopicQueue

Pipeline Agents:
- RephraseAgent, DecomposeAgent, ManagerAgent
- PipelineResearchAgent, NoteAgent, ReportAgent
"""

# Legacy agent (backward compatible)
from .agent import ResearchAgent

# New pipeline
from .pipeline import ResearchPipeline, run_research

# Data structures
from .data_structures import (
    TopicStatus,
    ToolType,
    ToolTrace,
    TopicBlock,
    DynamicTopicQueue,
)

# Pipeline agents (renamed to avoid conflict with legacy)
from .agents.rephrase_agent import RephraseAgent
from .agents.decompose_agent import DecomposeAgent
from .agents.manager_agent import ManagerAgent
from .agents.research_agent import ResearchAgent as PipelineResearchAgent
from .agents.note_agent import NoteAgent
from .agents.report_agent import ReportAgent

__all__ = [
    # Legacy
    "ResearchAgent",
    # Pipeline
    "ResearchPipeline",
    "run_research",
    # Data structures
    "TopicStatus",
    "ToolType",
    "ToolTrace",
    "TopicBlock",
    "DynamicTopicQueue",
    # Pipeline agents
    "RephraseAgent",
    "DecomposeAgent",
    "ManagerAgent",
    "PipelineResearchAgent",
    "NoteAgent",
    "ReportAgent",
]
