"""Rephrase Agent for optimizing research topics.

Takes a user's raw research topic and produces a clearer,
more focused version suitable for systematic research.
"""

import json
import logging
from typing import Any

from src.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

REPHRASE_SYSTEM_PROMPT = """You are a research topic optimizer specializing in financial analysis.

Your task is to take a user's research topic or question and rephrase it into a clear,
focused research objective that will guide systematic analysis.

Guidelines:
1. Preserve the user's core intent
2. Make the topic specific and actionable
3. Remove ambiguity while keeping scope manageable
4. For stock analysis, include relevant context (market, timeframe, etc.)
5. Consider what data sources would be needed

Output your response as JSON with the following structure:
{
    "optimized_topic": "The refined research topic",
    "research_objective": "Clear statement of what we want to learn",
    "key_questions": ["Question 1", "Question 2", ...],
    "suggested_scope": {
        "market": "US/KR/Both",
        "timeframe": "short-term/medium-term/long-term",
        "analysis_types": ["technical", "fundamental", "news", "etc."]
    },
    "data_needs": ["Type of data needed 1", "Type of data needed 2", ...]
}"""

REPHRASE_USER_TEMPLATE = """Please optimize the following research topic for systematic financial analysis:

Original Topic: {topic}

{context}

Provide a refined version that is clear, specific, and actionable."""


class RephraseAgent(BaseAgent):
    """Agent for rephrasing and optimizing research topics.

    Takes raw user topics and produces structured, optimized
    research objectives with clear scope and data needs.
    """

    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ):
        """Initialize the RephraseAgent.

        Args:
            model: LLM model to use.
            temperature: Lower temperature for consistent output.
            max_tokens: Max tokens for response (increased for reasoning models).
        """
        super().__init__(model=model, temperature=temperature, max_tokens=max_tokens)

    async def process(
        self,
        topic: str,
        context: str = "",
        symbols: list[str] | None = None,
        market: str = "US",
    ) -> dict[str, Any]:
        """Rephrase and optimize a research topic.

        Args:
            topic: The raw research topic from the user.
            context: Additional context about the research.
            symbols: Optional list of stock symbols related to the topic.
            market: Target market (US, KR, or Both).

        Returns:
            Dictionary with optimized topic and metadata.
        """
        # Build context string
        context_parts = []
        if context:
            context_parts.append(f"Additional Context: {context}")
        if symbols:
            context_parts.append(f"Related Symbols: {', '.join(symbols)}")
        if market:
            context_parts.append(f"Target Market: {market}")

        context_str = "\n".join(context_parts) if context_parts else ""

        messages = [
            {"role": "system", "content": REPHRASE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": REPHRASE_USER_TEMPLATE.format(
                    topic=topic,
                    context=context_str,
                ),
            },
        ]

        try:
            response = await self.call_llm(messages)
            result = self._parse_response(response)

            # Add original topic for reference
            result["original_topic"] = topic
            result["market"] = market
            if symbols:
                result["symbols"] = symbols

            logger.info(f"Rephrased topic: {topic[:50]}... -> {result.get('optimized_topic', '')[:50]}...")
            return result

        except Exception as e:
            logger.error(f"Error in RephraseAgent: {e}")
            # Return a fallback structure
            return {
                "original_topic": topic,
                "optimized_topic": topic,
                "research_objective": f"Research and analyze: {topic}",
                "key_questions": [f"What are the key aspects of {topic}?"],
                "suggested_scope": {
                    "market": market,
                    "timeframe": "medium-term",
                    "analysis_types": ["fundamental", "technical"],
                },
                "data_needs": ["stock_data", "financials"],
                "error": str(e),
            }

    def _parse_response(self, response: str) -> dict[str, Any]:
        """Parse the LLM response into structured data.

        Args:
            response: Raw LLM response text.

        Returns:
            Parsed dictionary.
        """
        # Try to extract JSON from the response
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
                # Try to find JSON object
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
                    "optimized_topic": response.strip(),
                    "research_objective": response.strip(),
                    "key_questions": [],
                    "suggested_scope": {},
                    "data_needs": [],
                }
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON response: {response[:100]}...")
            # Return a basic structure
            return {
                "optimized_topic": response.strip(),
                "research_objective": response.strip(),
                "key_questions": [],
                "suggested_scope": {},
                "data_needs": [],
            }

    async def refine_with_feedback(
        self,
        original_topic: str,
        current_optimization: dict[str, Any],
        feedback: str,
    ) -> dict[str, Any]:
        """Refine the topic based on user feedback.

        Args:
            original_topic: The original research topic.
            current_optimization: Current optimized result.
            feedback: User's feedback for refinement.

        Returns:
            Refined optimization result.
        """
        messages = [
            {"role": "system", "content": REPHRASE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Original topic: {original_topic}",
            },
            {
                "role": "assistant",
                "content": json.dumps(current_optimization, ensure_ascii=False),
            },
            {
                "role": "user",
                "content": f"Please refine the optimization based on this feedback:\n{feedback}",
            },
        ]

        response = await self.call_llm(messages)
        result = self._parse_response(response)
        result["original_topic"] = original_topic
        result["refinement_feedback"] = feedback

        return result
