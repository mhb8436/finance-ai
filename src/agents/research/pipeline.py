"""Research Pipeline Orchestrator.

Coordinates the multi-agent research workflow:
1. Rephrase: Optimize user's research topic
2. Decompose: Break into sub-topics
3. Research: Execute research with tools
4. Notes: Summarize findings
5. Report: Generate final report

Based on DeepTutor's research pipeline architecture.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Awaitable

from .data_structures import DynamicTopicQueue, TopicStatus, TopicBlock
from .agents import (
    RephraseAgent,
    DecomposeAgent,
    ManagerAgent,
    ResearchAgent,
    NoteAgent,
    ReportAgent,
)

logger = logging.getLogger(__name__)


class ResearchPipeline:
    """Orchestrates the multi-agent research workflow.

    Manages the flow from topic optimization through report generation,
    coordinating multiple specialized agents.

    Example:
        pipeline = ResearchPipeline()
        pipeline.register_tool("stock_data", stock_data_handler)

        result = await pipeline.run(
            topic="Analyze AAPL's investment potential",
            symbols=["AAPL"],
        )
        print(result["report"]["report_content"])
    """

    def __init__(
        self,
        model: str | None = None,
        state_dir: str | None = None,
        max_topics: int = 10,
        max_iterations_per_topic: int = 5,
        max_total_iterations: int = 50,
        use_tool_router: bool = True,
    ):
        """Initialize the research pipeline.

        Args:
            model: LLM model to use for all agents.
            state_dir: Directory for state persistence.
            max_topics: Maximum number of sub-topics.
            max_iterations_per_topic: Max iterations per topic.
            max_total_iterations: Max total research iterations.
            use_tool_router: If True, use unified ToolRouter for tool execution
                           with retry and timeout support.
        """
        self.model = model
        self.state_dir = Path(state_dir) if state_dir else None
        self.max_topics = max_topics
        self.max_iterations_per_topic = max_iterations_per_topic
        self.max_total_iterations = max_total_iterations
        self.use_tool_router = use_tool_router

        # Initialize agents
        self._rephrase_agent = RephraseAgent(model=model)
        self._decompose_agent = DecomposeAgent(model=model)
        self._manager_agent = ManagerAgent(model=model)
        self._research_agent = ResearchAgent(model=model, use_tool_router=use_tool_router)
        self._note_agent = NoteAgent(model=model)
        self._report_agent = ReportAgent(model=model)

        # Tool handlers (used only when use_tool_router=False)
        self._tool_handlers: dict[str, Callable[..., Awaitable[Any]]] = {}

        # State
        self._current_research_id: str | None = None
        self._queue: DynamicTopicQueue | None = None

        if use_tool_router:
            logger.info("ResearchPipeline initialized with ToolRouter (unified tool execution)")

    def register_tool(
        self,
        tool_name: str,
        handler: Callable[..., Awaitable[Any]],
        description: str | None = None,
    ) -> None:
        """Register a tool for the research agent.

        Note: When use_tool_router=True (default), tools are automatically
        available via ToolRouter. This method is only needed for custom
        tools not supported by ToolRouter.

        Args:
            tool_name: Name of the tool.
            handler: Async function to handle tool calls.
            description: Optional description.
        """
        if self.use_tool_router:
            logger.info(
                f"Tool '{tool_name}' registered, but ToolRouter is enabled. "
                f"ToolRouter handles: rag_search, web_search, stock_data, "
                f"financials, news_search, youtube, technical_analysis."
            )

        self._tool_handlers[tool_name] = handler
        self._research_agent.register_tool(tool_name, handler, description)

    async def run(
        self,
        topic: str,
        context: str = "",
        symbols: list[str] | None = None,
        market: str = "US",
        skip_rephrase: bool = False,
        output_format: str = "markdown",
    ) -> dict[str, Any]:
        """Run the complete research pipeline.

        Args:
            topic: The research topic.
            context: Additional context.
            symbols: Stock symbols to analyze.
            market: Target market (US, KR, Both).
            skip_rephrase: Skip topic rephrasing.
            output_format: Report format (markdown, json, html).

        Returns:
            Dictionary with all pipeline results.
        """
        start_time = datetime.utcnow()
        self._current_research_id = f"research_{uuid.uuid4().hex[:8]}"

        logger.info(f"Starting research pipeline: {self._current_research_id}")
        logger.info(f"Topic: {topic}")

        results = {
            "research_id": self._current_research_id,
            "original_topic": topic,
            "started_at": start_time.isoformat(),
            "stages": {},
        }

        try:
            # Stage 1: Rephrase
            if skip_rephrase:
                rephrased = {
                    "original_topic": topic,
                    "optimized_topic": topic,
                    "research_objective": topic,
                    "key_questions": [],
                    "suggested_scope": {"market": market},
                    "symbols": symbols or [],
                }
            else:
                rephrased = await self._rephrase_agent.process(
                    topic=topic,
                    context=context,
                    symbols=symbols,
                    market=market,
                )
            results["stages"]["rephrase"] = rephrased
            logger.info(f"Rephrased: {rephrased.get('optimized_topic', topic)[:50]}...")

            # Stage 2: Decompose
            decomposed = await self._decompose_agent.process(
                rephrased_result=rephrased,
                max_subtopics=self.max_topics,
                symbols=symbols,
            )
            results["stages"]["decompose"] = decomposed
            logger.info(f"Decomposed into {len(decomposed.get('sub_topics', []))} topics")

            # Stage 3: Create queue and research
            state_file = None
            if self.state_dir:
                self.state_dir.mkdir(parents=True, exist_ok=True)
                state_file = self.state_dir / f"{self._current_research_id}.json"

            self._queue = self._decompose_agent.create_topic_queue(
                decomposed_result=decomposed,
                research_id=self._current_research_id,
                max_length=self.max_topics * 2,  # Allow dynamic additions
                state_file=str(state_file) if state_file else None,
            )

            # Research loop
            research_results = await self._research_loop(
                queue=self._queue,
                research_objective=rephrased.get("research_objective", topic),
                symbols=symbols,
            )
            results["stages"]["research"] = research_results

            # Stage 4: Create notes
            completed_blocks = self._queue.get_completed_blocks()
            topic_notes = await self._note_agent.create_batch_notes(completed_blocks)
            results["stages"]["notes"] = topic_notes

            # Stage 5: Synthesize notes
            synthesized = await self._note_agent.synthesize_notes(
                all_notes=topic_notes,
                research_objective=rephrased.get("research_objective", topic),
            )
            results["stages"]["synthesis"] = synthesized

            # Stage 6: Generate report
            report = await self._report_agent.process(
                main_topic=rephrased.get("optimized_topic", topic),
                research_objective=rephrased.get("research_objective", topic),
                synthesized_notes=synthesized,
                topic_notes=topic_notes,
                queue_stats=self._queue.get_statistics(),
                output_format=output_format,
            )
            results["report"] = report

            # Final statistics
            end_time = datetime.utcnow()
            results["completed_at"] = end_time.isoformat()
            results["duration_seconds"] = (end_time - start_time).total_seconds()
            results["statistics"] = self._queue.get_statistics()
            results["success"] = True

            logger.info(
                f"Research pipeline completed in {results['duration_seconds']:.1f}s"
            )

        except Exception as e:
            logger.error(f"Research pipeline error: {e}")
            results["error"] = str(e)
            results["success"] = False
            results["completed_at"] = datetime.utcnow().isoformat()

        return results

    async def _research_loop(
        self,
        queue: DynamicTopicQueue,
        research_objective: str,
        symbols: list[str] | None = None,
    ) -> dict[str, Any]:
        """Execute the research loop.

        Args:
            queue: Topic queue to process.
            research_objective: Research objective.
            symbols: Stock symbols.

        Returns:
            Research loop results.
        """
        self._manager_agent.reset_iteration_count()
        self._manager_agent.set_max_iterations(self.max_total_iterations)
        self._research_agent.reset_citation_counter()

        iteration = 0
        topic_results = []

        while True:
            iteration += 1

            # Get current findings
            current_findings = queue.get_all_summaries()

            # Manager evaluates progress
            manager_result = await self._manager_agent.process(
                queue=queue,
                research_objective=research_objective,
                current_findings=current_findings,
            )

            # Check if we should stop
            if not self._manager_agent.should_continue(manager_result):
                logger.info("Manager decided research is sufficient")
                break

            # Get next topic to research
            next_topic = self._manager_agent.get_next_topic(queue)
            if not next_topic:
                logger.info("No more topics to research")
                break

            # Mark as researching
            queue.mark_researching(next_topic.block_id)

            # Execute research
            try:
                research_result = await self._research_agent.process(
                    topic_block=next_topic,
                    context=research_objective,
                    max_iterations=self.max_iterations_per_topic,
                    symbols=symbols,
                )
                topic_results.append(research_result)

                # Mark as completed
                queue.mark_completed(next_topic.block_id)
                logger.info(f"Completed research: {next_topic.sub_topic}")

            except Exception as e:
                logger.error(f"Research failed for {next_topic.sub_topic}: {e}")
                queue.mark_failed(next_topic.block_id)

            # Check for dynamic topic additions
            if manager_result.get("gaps_identified"):
                existing_topics = [b.sub_topic for b in queue.blocks]
                for gap in manager_result["gaps_identified"][:2]:  # Max 2 additions
                    await self._decompose_agent.add_subtopic(
                        queue=queue,
                        context=f"Gap identified: {gap}\n\nCurrent findings:\n{current_findings[:1000]}",
                        existing_topics=existing_topics,
                    )

        return {
            "iterations": iteration,
            "topics_researched": len(topic_results),
            "topic_results": topic_results,
            "final_stats": queue.get_statistics(),
        }

    async def run_streaming(
        self,
        topic: str,
        context: str = "",
        symbols: list[str] | None = None,
        market: str = "US",
    ) -> AsyncIterator[dict[str, Any]]:
        """Run the pipeline with streaming progress updates.

        Args:
            topic: Research topic.
            context: Additional context.
            symbols: Stock symbols.
            market: Target market.

        Yields:
            Progress updates as dictionaries.
        """
        self._current_research_id = f"research_{uuid.uuid4().hex[:8]}"

        yield {
            "event": "started",
            "research_id": self._current_research_id,
            "topic": topic,
        }

        # Rephrase
        yield {"event": "stage_start", "stage": "rephrase"}
        rephrased = await self._rephrase_agent.process(
            topic=topic, context=context, symbols=symbols, market=market
        )
        yield {"event": "stage_complete", "stage": "rephrase", "result": rephrased}

        # Decompose
        yield {"event": "stage_start", "stage": "decompose"}
        decomposed = await self._decompose_agent.process(
            rephrased_result=rephrased, max_subtopics=self.max_topics, symbols=symbols
        )
        yield {
            "event": "stage_complete",
            "stage": "decompose",
            "topics": len(decomposed.get("sub_topics", [])),
        }

        # Create queue
        self._queue = self._decompose_agent.create_topic_queue(
            decomposed_result=decomposed,
            research_id=self._current_research_id,
        )

        # Research loop with progress
        self._manager_agent.reset_iteration_count()
        self._research_agent.reset_citation_counter()

        while True:
            next_topic = self._manager_agent.get_next_topic(self._queue)
            if not next_topic:
                break

            yield {
                "event": "research_start",
                "topic": next_topic.sub_topic,
                "block_id": next_topic.block_id,
            }

            self._queue.mark_researching(next_topic.block_id)

            try:
                result = await self._research_agent.process(
                    topic_block=next_topic,
                    context=rephrased.get("research_objective", topic),
                    symbols=symbols,
                )
                self._queue.mark_completed(next_topic.block_id)

                yield {
                    "event": "research_complete",
                    "topic": next_topic.sub_topic,
                    "findings_count": len(result.get("findings", [])),
                }

            except Exception as e:
                self._queue.mark_failed(next_topic.block_id)
                yield {
                    "event": "research_failed",
                    "topic": next_topic.sub_topic,
                    "error": str(e),
                }

            # Check manager decision
            manager_result = await self._manager_agent.process(
                queue=self._queue,
                research_objective=rephrased.get("research_objective", topic),
                current_findings=self._queue.get_all_summaries(),
            )

            if not self._manager_agent.should_continue(manager_result):
                break

        # Notes and report
        yield {"event": "stage_start", "stage": "notes"}
        completed_blocks = self._queue.get_completed_blocks()
        topic_notes = await self._note_agent.create_batch_notes(completed_blocks)
        synthesized = await self._note_agent.synthesize_notes(
            topic_notes, rephrased.get("research_objective", topic)
        )
        yield {"event": "stage_complete", "stage": "notes"}

        yield {"event": "stage_start", "stage": "report"}
        report = await self._report_agent.process(
            main_topic=rephrased.get("optimized_topic", topic),
            research_objective=rephrased.get("research_objective", topic),
            synthesized_notes=synthesized,
            topic_notes=topic_notes,
            queue_stats=self._queue.get_statistics(),
        )
        yield {"event": "stage_complete", "stage": "report", "report": report}

        yield {
            "event": "completed",
            "research_id": self._current_research_id,
            "statistics": self._queue.get_statistics(),
        }

    def get_current_state(self) -> dict[str, Any] | None:
        """Get the current research state.

        Returns:
            Current state dictionary or None.
        """
        if not self._queue:
            return None

        return {
            "research_id": self._current_research_id,
            "queue": self._queue.to_dict(),
        }

    @classmethod
    def load_state(cls, state_file: str | Path) -> "ResearchPipeline":
        """Load a pipeline from saved state.

        Args:
            state_file: Path to state file.

        Returns:
            ResearchPipeline with restored state.
        """
        pipeline = cls()
        pipeline._queue = DynamicTopicQueue.load_from_json(state_file)
        pipeline._current_research_id = pipeline._queue.research_id
        return pipeline


# Convenience function
async def run_research(
    topic: str,
    symbols: list[str] | None = None,
    market: str = "US",
    tool_handlers: dict[str, Callable[..., Awaitable[Any]]] | None = None,
    **kwargs,
) -> dict[str, Any]:
    """Convenience function to run research.

    Args:
        topic: Research topic.
        symbols: Stock symbols.
        market: Target market.
        tool_handlers: Tool handler functions.
        **kwargs: Additional pipeline arguments.

    Returns:
        Research results.
    """
    pipeline = ResearchPipeline(**kwargs)

    if tool_handlers:
        for name, handler in tool_handlers.items():
            pipeline.register_tool(name, handler)

    return await pipeline.run(topic=topic, symbols=symbols, market=market)
