"""Decompose Agent for breaking down research topics.

Takes an optimized research topic and breaks it into manageable
sub-topics that can be researched individually.
"""

import json
import logging
from typing import Any

from src.agents.base_agent import BaseAgent
from ..data_structures import TopicBlock, DynamicTopicQueue

logger = logging.getLogger(__name__)

DECOMPOSE_SYSTEM_PROMPT = """You are a research decomposition expert specializing in financial analysis.

Your task is to break down a research topic into specific, researachable sub-topics.
Each sub-topic should be:
1. Focused and specific enough for detailed research
2. Independent enough to be researched in parallel
3. Together, cover all aspects of the main topic
4. Ordered by logical dependency (fundamentals before technical, context before analysis)

For stock/financial research, consider these categories:
- Company Overview (business model, industry position)
- Financial Health (revenue, profitability, debt)
- Valuation (P/E, P/B, comparisons)
- Technical Analysis (price trends, indicators, patterns)
- Market Context (sector trends, macroeconomic factors)
- News & Sentiment (recent news, analyst opinions)
- Risk Factors (challenges, competitive threats)

Output your response as JSON:
{
    "main_topic": "The main research topic",
    "sub_topics": [
        {
            "title": "Sub-topic title",
            "overview": "What to research and why it matters",
            "priority": 1-5 (1 = highest),
            "dependencies": ["titles of sub-topics this depends on"],
            "tools_needed": ["rag_search", "web_search", "stock_data", "financials", "news_search", "youtube"]
        }
    ],
    "research_strategy": "Brief description of the recommended research approach"
}"""

DECOMPOSE_USER_TEMPLATE = """Please decompose the following research topic into sub-topics:

Main Topic: {topic}
Research Objective: {objective}

Key Questions to Answer:
{questions}

Suggested Scope:
- Market: {market}
- Timeframe: {timeframe}
- Analysis Types: {analysis_types}

{symbols_context}

Break this down into 4-8 specific sub-topics that together will comprehensively address the research objective."""


class DecomposeAgent(BaseAgent):
    """Agent for decomposing research topics into sub-topics.

    Creates a structured breakdown of research topics suitable
    for parallel execution by research agents.
    """

    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 8000,
    ):
        """Initialize the DecomposeAgent.

        Args:
            model: LLM model to use.
            temperature: Lower temperature for consistent decomposition.
            max_tokens: Max tokens for response (increased for reasoning models).
        """
        super().__init__(model=model, temperature=temperature, max_tokens=max_tokens)

    async def process(
        self,
        rephrased_result: dict[str, Any],
        max_subtopics: int = 8,
        symbols: list[str] | None = None,
    ) -> dict[str, Any]:
        """Decompose a rephrased topic into sub-topics.

        Args:
            rephrased_result: Result from RephraseAgent.
            max_subtopics: Maximum number of sub-topics to generate.
            symbols: Optional list of stock symbols.

        Returns:
            Dictionary with decomposed sub-topics.
        """
        topic = rephrased_result.get("optimized_topic", rephrased_result.get("original_topic", ""))
        objective = rephrased_result.get("research_objective", topic)
        key_questions = rephrased_result.get("key_questions", [])
        scope = rephrased_result.get("suggested_scope", {})

        # Build questions string
        questions_str = "\n".join(f"- {q}" for q in key_questions) if key_questions else "- No specific questions provided"

        # Build symbols context
        symbols = symbols or rephrased_result.get("symbols", [])
        symbols_context = f"Target Symbols: {', '.join(symbols)}" if symbols else ""

        messages = [
            {"role": "system", "content": DECOMPOSE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": DECOMPOSE_USER_TEMPLATE.format(
                    topic=topic,
                    objective=objective,
                    questions=questions_str,
                    market=scope.get("market", "US"),
                    timeframe=scope.get("timeframe", "medium-term"),
                    analysis_types=", ".join(scope.get("analysis_types", ["fundamental", "technical"])),
                    symbols_context=symbols_context,
                ),
            },
        ]

        try:
            response = await self.call_llm(messages)
            result = self._parse_response(response)

            # Limit sub-topics
            if "sub_topics" in result and len(result["sub_topics"]) > max_subtopics:
                result["sub_topics"] = result["sub_topics"][:max_subtopics]

            # Add metadata
            result["rephrased_result"] = rephrased_result
            result["symbols"] = symbols

            logger.info(f"Decomposed topic into {len(result.get('sub_topics', []))} sub-topics")
            return result

        except Exception as e:
            logger.error(f"Error in DecomposeAgent: {e}")
            # Return a basic decomposition
            return {
                "main_topic": topic,
                "sub_topics": [
                    {
                        "title": "General Research",
                        "overview": f"Research the main aspects of: {topic}",
                        "priority": 1,
                        "dependencies": [],
                        "tools_needed": ["web_search", "stock_data"],
                    }
                ],
                "research_strategy": "Basic research approach",
                "error": str(e),
            }

    def _parse_response(self, response: str) -> dict[str, Any]:
        """Parse the LLM response into structured data.

        Args:
            response: Raw LLM response text.

        Returns:
            Parsed dictionary.
        """
        try:
            # Handle markdown code blocks
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
                    "main_topic": "",
                    "sub_topics": [],
                    "research_strategy": response.strip(),
                }
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON response: {response[:100]}...")
            return {
                "main_topic": "",
                "sub_topics": [],
                "research_strategy": response.strip(),
            }

    def create_topic_queue(
        self,
        decomposed_result: dict[str, Any],
        research_id: str,
        max_length: int = 50,
        state_file: str | None = None,
    ) -> DynamicTopicQueue:
        """Create a DynamicTopicQueue from decomposed results.

        Args:
            decomposed_result: Result from decompose().
            research_id: Unique identifier for this research.
            max_length: Maximum queue length.
            state_file: Optional path for state persistence.

        Returns:
            Initialized DynamicTopicQueue.
        """
        queue = DynamicTopicQueue(
            research_id=research_id,
            max_length=max_length,
            state_file=state_file,
        )

        sub_topics = decomposed_result.get("sub_topics", [])
        symbols = decomposed_result.get("symbols", [])

        # Sort by priority
        sorted_topics = sorted(sub_topics, key=lambda x: x.get("priority", 5))

        for topic in sorted_topics:
            queue.add_block(
                sub_topic=topic.get("title", ""),
                overview=topic.get("overview", ""),
                metadata={
                    "priority": topic.get("priority", 5),
                    "dependencies": topic.get("dependencies", []),
                    "tools_needed": topic.get("tools_needed", []),
                    "symbols": symbols,
                },
            )

        logger.info(f"Created topic queue with {len(queue)} blocks")
        return queue

    async def add_subtopic(
        self,
        queue: DynamicTopicQueue,
        context: str,
        existing_topics: list[str],
    ) -> TopicBlock | None:
        """Dynamically add a new sub-topic based on research findings.

        Args:
            queue: The topic queue to add to.
            context: Context from current research findings.
            existing_topics: List of existing topic titles.

        Returns:
            New TopicBlock if added, None otherwise.
        """
        messages = [
            {
                "role": "system",
                "content": """Based on research findings, suggest ONE additional sub-topic
that would enhance the analysis. Output JSON:
{
    "should_add": true/false,
    "title": "Sub-topic title",
    "overview": "What to research",
    "priority": 1-5,
    "tools_needed": ["tool1", "tool2"]
}
Only suggest if genuinely valuable and not already covered.""",
            },
            {
                "role": "user",
                "content": f"""Current research context:
{context}

Existing topics:
{chr(10).join('- ' + t for t in existing_topics)}

Should we add another sub-topic?""",
            },
        ]

        try:
            response = await self.call_llm(messages)
            result = self._parse_response(response)

            if result.get("should_add") and result.get("title"):
                block = queue.add_block(
                    sub_topic=result["title"],
                    overview=result.get("overview", ""),
                    metadata={
                        "priority": result.get("priority", 5),
                        "tools_needed": result.get("tools_needed", []),
                        "dynamically_added": True,
                    },
                )
                if block:
                    logger.info(f"Dynamically added sub-topic: {result['title']}")
                return block

        except Exception as e:
            logger.error(f"Error adding sub-topic: {e}")

        return None
