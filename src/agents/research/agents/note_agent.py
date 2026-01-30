"""Note Agent for summarizing research findings.

Takes tool traces and findings from research and creates
structured notes with citations for report generation.
"""

import json
import logging
from typing import Any

from src.agents.base_agent import BaseAgent
from ..data_structures import TopicBlock, ToolTrace

logger = logging.getLogger(__name__)

NOTE_SYSTEM_PROMPT = """You are a research note-taker specializing in financial analysis.

Your task is to synthesize research findings into clear, structured notes.
Notes should:
1. Capture key insights with proper citations
2. Organize information logically
3. Highlight important data points
4. Note any contradictions or uncertainties
5. Be concise but comprehensive

Use citation format [CIT-X-YY] when referencing tool findings.

Output your notes as JSON:
{
    "topic": "The research topic",
    "summary": "2-3 sentence summary",
    "key_insights": [
        {
            "insight": "Key finding or insight",
            "citations": ["CIT-1-01", "CIT-1-02"],
            "confidence": "high/medium/low"
        }
    ],
    "data_points": [
        {
            "metric": "Metric name",
            "value": "Value",
            "context": "Brief context",
            "citation": "CIT-X-YY"
        }
    ],
    "uncertainties": ["Areas needing more research"],
    "connections": ["Connections to other topics"],
    "importance_score": 1-10
}"""

NOTE_USER_TEMPLATE = """Please create structured notes for the following research:

Topic: {topic}
Overview: {overview}

Tool Traces (Research Data):
{tool_traces}

Findings Summary:
{findings}

Create comprehensive notes with citations."""


class NoteAgent(BaseAgent):
    """Agent for creating research notes from findings.

    Synthesizes tool traces and findings into structured,
    citable notes for use in report generation.
    """

    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 16000,
    ):
        """Initialize the NoteAgent.

        Args:
            model: LLM model to use.
            temperature: Lower temperature for consistent notes.
            max_tokens: Max tokens for response (increased for reasoning models like gpt-5).
        """
        super().__init__(model=model, temperature=temperature, max_tokens=max_tokens)

    async def process(
        self,
        topic_block: TopicBlock,
        findings_summary: str = "",
    ) -> dict[str, Any]:
        """Create notes from a researched topic block.

        Args:
            topic_block: The completed topic block with traces.
            findings_summary: Optional additional findings summary.

        Returns:
            Dictionary with structured notes.
        """
        # Format tool traces for the prompt
        tool_traces_str = self._format_tool_traces(topic_block.tool_traces)

        messages = [
            {"role": "system", "content": NOTE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": NOTE_USER_TEMPLATE.format(
                    topic=topic_block.sub_topic,
                    overview=topic_block.overview,
                    tool_traces=tool_traces_str,
                    findings=findings_summary or topic_block.get_all_summaries(),
                ),
            },
        ]

        try:
            response = await self.call_llm(messages)
            result = self._parse_response(response)

            # Add metadata
            result["block_id"] = topic_block.block_id
            result["tool_count"] = len(topic_block.tool_traces)
            result["iteration_count"] = topic_block.iteration_count

            logger.info(f"Created notes for: {topic_block.sub_topic}")
            return result

        except Exception as e:
            logger.error(f"Error in NoteAgent: {e}")
            return {
                "topic": topic_block.sub_topic,
                "summary": f"Error creating notes: {e}",
                "key_insights": [],
                "data_points": [],
                "uncertainties": [],
                "connections": [],
                "importance_score": 5,
                "error": str(e),
            }

    def _format_tool_traces(self, traces: list[ToolTrace]) -> str:
        """Format tool traces for the prompt.

        Args:
            traces: List of tool traces.

        Returns:
            Formatted string.
        """
        if not traces:
            return "No tool traces available."

        parts = []
        for trace in traces:
            # Include both raw data and analysis for comprehensive notes
            raw_data_preview = trace.raw_answer
            # Truncate very long raw answers for the prompt but keep essential data
            if len(raw_data_preview) > 3000:
                raw_data_preview = raw_data_preview[:3000] + "\n... [truncated for brevity]"

            parts.append(f"""
[{trace.citation_id}] {trace.tool_type}
Query: {trace.query}
Data:
{raw_data_preview}
Analysis: {trace.summary}
---""")

        return "\n".join(parts)

    def _parse_response(self, response: str) -> dict[str, Any]:
        """Parse the LLM response.

        Args:
            response: Raw LLM response.

        Returns:
            Parsed dictionary.
        """
        try:
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_str = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                json_str = response[start:end].strip()
            else:
                start = response.find("{")
                end = response.rfind("}") + 1
                if start >= 0 and end > start:
                    json_str = response[start:end]
                else:
                    json_str = response

            result = json.loads(json_str)
            # Ensure we return a dict
            if isinstance(result, dict):
                return result
            elif isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict):
                return result[0]
            else:
                logger.warning(f"Unexpected JSON type: {type(result)}")
                return {
                    "topic": "",
                    "summary": response.strip(),
                    "key_insights": [],
                    "data_points": [],
                    "uncertainties": [],
                    "connections": [],
                    "importance_score": 5,
                }
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse note response: {response[:100]}...")
            return {
                "topic": "",
                "summary": response.strip(),
                "key_insights": [],
                "data_points": [],
                "uncertainties": [],
                "connections": [],
                "importance_score": 5,
            }

    async def create_batch_notes(
        self,
        topic_blocks: list[TopicBlock],
    ) -> list[dict[str, Any]]:
        """Create notes for multiple topic blocks.

        Args:
            topic_blocks: List of completed topic blocks.

        Returns:
            List of notes dictionaries.
        """
        notes = []
        for block in topic_blocks:
            if block.tool_traces:  # Only process blocks with data
                note = await self.process(block)
                notes.append(note)
            else:
                logger.debug(f"Skipping block without traces: {block.sub_topic}")

        return notes

    async def synthesize_notes(
        self,
        all_notes: list[dict[str, Any]],
        research_objective: str,
    ) -> dict[str, Any]:
        """Synthesize multiple notes into a cohesive summary.

        Args:
            all_notes: List of notes from different topics.
            research_objective: The main research objective.

        Returns:
            Synthesized summary dictionary.
        """
        if not all_notes:
            return {
                "overall_summary": "No notes to synthesize.",
                "key_themes": [],
                "cross_topic_insights": [],
                "data_summary": [],
                "confidence_assessment": "low",
            }

        # Build notes summary for synthesis
        notes_summary = []
        for note in all_notes:
            notes_summary.append(f"""
Topic: {note.get('topic', 'Unknown')}
Summary: {note.get('summary', '')}
Key Insights: {', '.join(i.get('insight', '') for i in note.get('key_insights', [])[:3])}
""")

        messages = [
            {
                "role": "system",
                "content": """You are synthesizing research notes into a cohesive summary.
Output JSON:
{
    "overall_summary": "Comprehensive 3-5 sentence summary",
    "key_themes": ["Theme 1", "Theme 2"],
    "cross_topic_insights": [
        {
            "insight": "Insight connecting multiple topics",
            "related_topics": ["Topic A", "Topic B"]
        }
    ],
    "data_summary": [
        {
            "metric": "Key metric",
            "finding": "What the data shows"
        }
    ],
    "confidence_assessment": "high/medium/low",
    "gaps_remaining": ["Gap 1", "Gap 2"]
}""",
            },
            {
                "role": "user",
                "content": f"""Research Objective: {research_objective}

Notes to Synthesize:
{''.join(notes_summary)}

Create a cohesive synthesis of all research findings.""",
            },
        ]

        try:
            response = await self.call_llm(messages)
            return self._parse_response(response)
        except Exception as e:
            logger.error(f"Error synthesizing notes: {e}")
            return {
                "overall_summary": f"Error in synthesis: {e}",
                "key_themes": [],
                "cross_topic_insights": [],
                "data_summary": [],
                "confidence_assessment": "low",
                "error": str(e),
            }
