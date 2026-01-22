"""Manager Agent for orchestrating research workflow.

Coordinates the research process by managing topic queue,
delegating tasks to research agents, and monitoring progress.
"""

import json
import logging
from typing import Any

from src.agents.base_agent import BaseAgent
from ..data_structures import DynamicTopicQueue, TopicBlock, TopicStatus

logger = logging.getLogger(__name__)

MANAGER_SYSTEM_PROMPT = """You are a research manager coordinating a financial analysis team.

Your responsibilities:
1. Evaluate research progress and quality
2. Decide which topics need more research
3. Determine when research is sufficient
4. Prioritize remaining work

For each decision, consider:
- Coverage: Are all key aspects addressed?
- Depth: Is the analysis sufficiently detailed?
- Quality: Are findings reliable and well-sourced?
- Coherence: Do findings form a consistent picture?

Output your decisions as JSON:
{
    "assessment": {
        "coverage_score": 1-10,
        "depth_score": 1-10,
        "quality_score": 1-10,
        "overall_score": 1-10
    },
    "decision": "continue" | "sufficient" | "refocus",
    "reasoning": "Brief explanation of decision",
    "next_actions": [
        {
            "action": "research_topic" | "deepen_topic" | "synthesize" | "conclude",
            "target": "topic or area",
            "priority": 1-5
        }
    ],
    "gaps_identified": ["Gap 1", "Gap 2"],
    "ready_for_report": true/false
}"""


class ManagerAgent(BaseAgent):
    """Agent for managing the research workflow.

    Coordinates topic queue, evaluates progress, and makes
    decisions about research direction.
    """

    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 1500,
    ):
        """Initialize the ManagerAgent.

        Args:
            model: LLM model to use.
            temperature: Lower temperature for consistent decisions.
            max_tokens: Max tokens for response.
        """
        super().__init__(model=model, temperature=temperature, max_tokens=max_tokens)
        self._iteration_count = 0
        self._max_iterations = 20  # Safety limit

    async def process(
        self,
        queue: DynamicTopicQueue,
        research_objective: str,
        current_findings: str = "",
    ) -> dict[str, Any]:
        """Evaluate research progress and decide next steps.

        Args:
            queue: The topic queue with current state.
            research_objective: The main research objective.
            current_findings: Summary of findings so far.

        Returns:
            Dictionary with assessment and next actions.
        """
        self._iteration_count += 1

        # Get queue statistics
        stats = queue.get_statistics()

        # Check iteration limit
        if self._iteration_count >= self._max_iterations:
            logger.warning(f"Reached max iterations ({self._max_iterations})")
            return {
                "assessment": {"overall_score": 6},
                "decision": "sufficient",
                "reasoning": "Reached maximum iteration limit",
                "next_actions": [{"action": "conclude", "target": "all", "priority": 1}],
                "gaps_identified": [],
                "ready_for_report": True,
            }

        # Build status summary
        status_summary = self._build_status_summary(queue, stats)

        messages = [
            {"role": "system", "content": MANAGER_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"""Research Objective: {research_objective}

Current Status:
{status_summary}

Research Findings So Far:
{current_findings or "No findings yet."}

Iteration: {self._iteration_count}/{self._max_iterations}

Evaluate progress and decide next steps.""",
            },
        ]

        try:
            response = await self.call_llm(messages)
            result = self._parse_response(response)

            # Add metadata
            result["iteration"] = self._iteration_count
            result["queue_stats"] = stats

            logger.info(
                f"Manager decision: {result.get('decision')} "
                f"(iteration {self._iteration_count})"
            )
            return result

        except Exception as e:
            logger.error(f"Error in ManagerAgent: {e}")
            return {
                "assessment": {"overall_score": 5},
                "decision": "continue",
                "reasoning": f"Error occurred: {e}",
                "next_actions": [],
                "gaps_identified": [],
                "ready_for_report": False,
                "error": str(e),
            }

    def _build_status_summary(
        self,
        queue: DynamicTopicQueue,
        stats: dict[str, Any],
    ) -> str:
        """Build a status summary for the LLM.

        Args:
            queue: Topic queue.
            stats: Queue statistics.

        Returns:
            Formatted status string.
        """
        lines = [
            f"Total Topics: {stats['total_blocks']}",
            f"- Pending: {stats['pending']}",
            f"- Researching: {stats['researching']}",
            f"- Completed: {stats['completed']}",
            f"- Failed: {stats['failed']}",
            f"Total Tool Calls: {stats['total_tool_calls']}",
            "",
            "Topic Details:",
        ]

        for block in queue.blocks:
            status_emoji = {
                TopicStatus.PENDING: "⏳",
                TopicStatus.RESEARCHING: "🔄",
                TopicStatus.COMPLETED: "✅",
                TopicStatus.FAILED: "❌",
            }.get(block.status, "❓")

            lines.append(
                f"  {status_emoji} {block.sub_topic} "
                f"(tools: {len(block.tool_traces)}, iterations: {block.iteration_count})"
            )

        return "\n".join(lines)

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

            return json.loads(json_str)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse manager response: {response[:100]}...")
            return {
                "assessment": {"overall_score": 5},
                "decision": "continue",
                "reasoning": response.strip(),
                "next_actions": [],
                "gaps_identified": [],
                "ready_for_report": False,
            }

    def get_next_topic(self, queue: DynamicTopicQueue) -> TopicBlock | None:
        """Get the next topic to research based on priorities.

        Args:
            queue: The topic queue.

        Returns:
            Next topic block to research, or None.
        """
        pending = [b for b in queue.blocks if b.status == TopicStatus.PENDING]
        if not pending:
            return None

        # Sort by priority (lower number = higher priority)
        pending.sort(key=lambda b: b.metadata.get("priority", 5))

        # Check dependencies
        completed_titles = {
            b.sub_topic for b in queue.blocks if b.status == TopicStatus.COMPLETED
        }

        for block in pending:
            dependencies = block.metadata.get("dependencies", [])
            if all(dep in completed_titles for dep in dependencies):
                return block

        # If no dependency-free topics, return highest priority
        return pending[0] if pending else None

    def should_continue(self, result: dict[str, Any]) -> bool:
        """Check if research should continue.

        Args:
            result: Result from process().

        Returns:
            True if research should continue.
        """
        decision = result.get("decision", "continue")
        return decision == "continue" and not result.get("ready_for_report", False)

    def reset_iteration_count(self) -> None:
        """Reset the iteration counter for a new research session."""
        self._iteration_count = 0

    def set_max_iterations(self, max_iterations: int) -> None:
        """Set the maximum number of iterations.

        Args:
            max_iterations: Maximum iterations allowed.
        """
        self._max_iterations = max_iterations
