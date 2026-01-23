"""Report Agent for generating research reports.

Takes synthesized notes and generates comprehensive
research reports in various formats.
"""

import json
import logging
from datetime import datetime
from typing import Any

from src.agents.base_agent import BaseAgent
from ..data_structures import DynamicTopicQueue, TopicBlock

logger = logging.getLogger(__name__)

REPORT_SYSTEM_PROMPT_EN = """You are a financial research report writer.

Your task is to create a comprehensive, professional research report.
The report should:
1. Have clear structure with executive summary
2. Present findings with proper citations
3. Include data-driven analysis
4. Provide actionable conclusions
5. Acknowledge limitations and uncertainties

Use citation format [CIT-X-YY] when referencing sources.

Report Structure:
1. Executive Summary
2. Research Overview
3. Key Findings (by topic)
4. Data Analysis
5. Risk Factors & Uncertainties
6. Conclusions & Recommendations

Output the report in markdown format."""

REPORT_SYSTEM_PROMPT_KO = """당신은 금융 리서치 리포트 작성 전문가입니다.

전문적이고 종합적인 리서치 리포트를 작성해야 합니다.
리포트는 다음을 포함해야 합니다:
1. 요약(Executive Summary)이 포함된 명확한 구조
2. 적절한 인용과 함께 제시된 분석 결과
3. 데이터 기반 분석
4. 실행 가능한 결론
5. 한계점 및 불확실성 인정

출처 인용 시 [CIT-X-YY] 형식을 사용하세요.

리포트 구조:
1. 핵심 요약
2. 리서치 개요
3. 주요 발견 (주제별)
4. 데이터 분석
5. 리스크 요인 및 불확실성
6. 결론 및 투자 의견

마크다운 형식으로 한국어로 리포트를 작성하세요."""

REPORT_USER_TEMPLATE_EN = """Please generate a comprehensive research report:

Research Topic: {main_topic}
Research Objective: {objective}

Synthesized Notes:
{synthesized_notes}

Individual Topic Notes:
{topic_notes}

Research Statistics:
- Topics Researched: {topic_count}
- Tool Calls Made: {tool_count}
- Research Duration: {duration}

Generate a professional research report in markdown format."""

REPORT_USER_TEMPLATE_KO = """다음 내용을 바탕으로 종합적인 리서치 리포트를 작성해주세요:

리서치 주제: {main_topic}
리서치 목표: {objective}

종합 요약:
{synthesized_notes}

개별 주제 분석:
{topic_notes}

리서치 통계:
- 분석 주제 수: {topic_count}
- 도구 호출 수: {tool_count}
- 리서치 소요 시간: {duration}

전문적인 리서치 리포트를 마크다운 형식으로 한국어로 작성해주세요."""


class ReportAgent(BaseAgent):
    """Agent for generating research reports.

    Creates comprehensive research reports from synthesized
    notes and topic findings.
    """

    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0.4,
        max_tokens: int = 16000,
    ):
        """Initialize the ReportAgent.

        Args:
            model: LLM model to use.
            temperature: Temperature for generation.
            max_tokens: Max tokens for response (increased for reasoning models like gpt-5).
        """
        super().__init__(model=model, temperature=temperature, max_tokens=max_tokens)

    async def process(
        self,
        main_topic: str,
        research_objective: str,
        synthesized_notes: dict[str, Any],
        topic_notes: list[dict[str, Any]],
        queue_stats: dict[str, Any] | None = None,
        output_format: str = "markdown",
        language: str = "ko",
    ) -> dict[str, Any]:
        """Generate a research report.

        Args:
            main_topic: The main research topic.
            research_objective: The research objective.
            synthesized_notes: Synthesized notes from NoteAgent.
            topic_notes: Individual topic notes.
            queue_stats: Optional queue statistics.
            output_format: Output format (markdown, json, html).
            language: Report language (ko for Korean, en for English).

        Returns:
            Dictionary with report content.
        """
        stats = queue_stats or {}

        # Format synthesized notes
        synth_str = self._format_synthesized_notes(synthesized_notes)

        # Format topic notes
        topics_str = self._format_topic_notes(topic_notes)

        # Calculate duration
        created_at = stats.get("created_at", "")
        updated_at = stats.get("updated_at", "")
        duration = self._calculate_duration(created_at, updated_at)

        # Select prompts based on language
        if language == "ko":
            system_prompt = REPORT_SYSTEM_PROMPT_KO
            user_template = REPORT_USER_TEMPLATE_KO
        else:
            system_prompt = REPORT_SYSTEM_PROMPT_EN
            user_template = REPORT_USER_TEMPLATE_EN

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": user_template.format(
                    main_topic=main_topic,
                    objective=research_objective,
                    synthesized_notes=synth_str,
                    topic_notes=topics_str,
                    topic_count=stats.get("total_blocks", len(topic_notes)),
                    tool_count=stats.get("total_tool_calls", 0),
                    duration=duration,
                ),
            },
        ]

        try:
            response = await self.call_llm(messages)

            result = {
                "main_topic": main_topic,
                "research_objective": research_objective,
                "report_content": response,
                "format": output_format,
                "language": language,
                "generated_at": datetime.utcnow().isoformat(),
                "statistics": {
                    "topics_researched": stats.get("total_blocks", len(topic_notes)),
                    "tool_calls": stats.get("total_tool_calls", 0),
                    "duration": duration,
                },
            }

            # Convert format if needed
            if output_format == "json":
                result["structured_report"] = self._extract_report_structure(response)
            elif output_format == "html":
                result["html_content"] = self._markdown_to_html(response)

            logger.info(f"Generated report for: {main_topic}")
            return result

        except Exception as e:
            logger.error(f"Error in ReportAgent: {e}")
            return {
                "main_topic": main_topic,
                "research_objective": research_objective,
                "report_content": f"Error generating report: {e}",
                "format": output_format,
                "generated_at": datetime.utcnow().isoformat(),
                "error": str(e),
            }

    def _format_synthesized_notes(self, notes: dict[str, Any]) -> str:
        """Format synthesized notes for the prompt.

        Args:
            notes: Synthesized notes dictionary.

        Returns:
            Formatted string.
        """
        parts = [
            f"Overall Summary: {notes.get('overall_summary', 'N/A')}",
            "",
            "Key Themes:",
        ]
        for theme in notes.get("key_themes", []):
            parts.append(f"- {theme}")

        parts.append("\nCross-Topic Insights:")
        for insight in notes.get("cross_topic_insights", []):
            if isinstance(insight, dict):
                parts.append(f"- {insight.get('insight', '')}")
            else:
                parts.append(f"- {insight}")

        parts.append(f"\nConfidence: {notes.get('confidence_assessment', 'medium')}")

        return "\n".join(parts)

    def _format_topic_notes(self, topic_notes: list[dict[str, Any]]) -> str:
        """Format individual topic notes for the prompt.

        Args:
            topic_notes: List of topic notes.

        Returns:
            Formatted string.
        """
        parts = []
        for note in topic_notes:
            topic = note.get("topic", "Unknown Topic")
            summary = note.get("summary", "")
            parts.append(f"\n## {topic}")
            parts.append(summary)

            # Add key insights
            insights = note.get("key_insights", [])
            if insights:
                parts.append("\nKey Insights:")
                for insight in insights[:5]:
                    if isinstance(insight, dict):
                        text = insight.get("insight", "")
                        cites = insight.get("citations", [])
                        cite_str = f" [{', '.join(cites)}]" if cites else ""
                        parts.append(f"- {text}{cite_str}")
                    else:
                        parts.append(f"- {insight}")

            # Add data points
            data_points = note.get("data_points", [])
            if data_points:
                parts.append("\nKey Data:")
                for dp in data_points[:5]:
                    if isinstance(dp, dict):
                        metric = dp.get("metric", "")
                        value = dp.get("value", "")
                        parts.append(f"- {metric}: {value}")

        return "\n".join(parts)

    def _calculate_duration(self, created_at: str, updated_at: str) -> str:
        """Calculate research duration.

        Args:
            created_at: Start timestamp.
            updated_at: End timestamp.

        Returns:
            Human-readable duration string.
        """
        if not created_at or not updated_at:
            return "Unknown"

        try:
            start = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            end = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            delta = end - start

            minutes = delta.total_seconds() / 60
            if minutes < 1:
                return f"{int(delta.total_seconds())} seconds"
            elif minutes < 60:
                return f"{int(minutes)} minutes"
            else:
                hours = minutes / 60
                return f"{hours:.1f} hours"
        except Exception:
            return "Unknown"

    def _extract_report_structure(self, markdown_content: str) -> dict[str, Any]:
        """Extract structure from markdown report.

        Args:
            markdown_content: Markdown report content.

        Returns:
            Structured dictionary.
        """
        structure = {
            "sections": [],
            "executive_summary": "",
            "conclusions": "",
        }

        current_section = None
        current_content = []

        for line in markdown_content.split("\n"):
            if line.startswith("# "):
                if current_section:
                    structure["sections"].append({
                        "title": current_section,
                        "content": "\n".join(current_content),
                    })
                current_section = line[2:].strip()
                current_content = []
            elif line.startswith("## "):
                if current_section:
                    structure["sections"].append({
                        "title": current_section,
                        "content": "\n".join(current_content),
                    })
                current_section = line[3:].strip()
                current_content = []
            else:
                current_content.append(line)

        # Add last section
        if current_section:
            structure["sections"].append({
                "title": current_section,
                "content": "\n".join(current_content),
            })

        # Extract executive summary and conclusions
        for section in structure["sections"]:
            title_lower = section["title"].lower()
            if "executive" in title_lower or "summary" in title_lower:
                structure["executive_summary"] = section["content"]
            elif "conclusion" in title_lower or "recommendation" in title_lower:
                structure["conclusions"] = section["content"]

        return structure

    def _markdown_to_html(self, markdown_content: str) -> str:
        """Convert markdown to basic HTML.

        Args:
            markdown_content: Markdown content.

        Returns:
            HTML content.
        """
        # Basic markdown to HTML conversion
        html_lines = ["<div class='research-report'>"]

        for line in markdown_content.split("\n"):
            if line.startswith("# "):
                html_lines.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith("## "):
                html_lines.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith("### "):
                html_lines.append(f"<h3>{line[4:]}</h3>")
            elif line.startswith("- "):
                html_lines.append(f"<li>{line[2:]}</li>")
            elif line.startswith("**") and line.endswith("**"):
                html_lines.append(f"<strong>{line[2:-2]}</strong>")
            elif line.strip():
                html_lines.append(f"<p>{line}</p>")

        html_lines.append("</div>")
        return "\n".join(html_lines)

    async def generate_executive_summary(
        self,
        main_topic: str,
        synthesized_notes: dict[str, Any],
        max_length: int = 500,
        language: str = "ko",
    ) -> str:
        """Generate a standalone executive summary.

        Args:
            main_topic: The research topic.
            synthesized_notes: Synthesized research notes.
            max_length: Maximum character length.
            language: Summary language (ko or en).

        Returns:
            Executive summary text.
        """
        if language == "ko":
            system_content = f"""금융 리서치 리포트의 핵심 요약을 간결하게 작성하세요 (최대 {max_length}자).
주요 발견사항과 실행 가능한 인사이트에 집중하세요. 한국어로 작성하세요."""
            user_content = f"""주제: {main_topic}

요약: {synthesized_notes.get('overall_summary', '')}

핵심 테마: {', '.join(synthesized_notes.get('key_themes', []))}

신뢰도: {synthesized_notes.get('confidence_assessment', 'medium')}

핵심 요약을 작성하세요:"""
        else:
            system_content = f"""Generate a concise executive summary (max {max_length} characters)
for a financial research report. Focus on key findings and actionable insights."""
            user_content = f"""Topic: {main_topic}

Summary: {synthesized_notes.get('overall_summary', '')}

Key Themes: {', '.join(synthesized_notes.get('key_themes', []))}

Confidence: {synthesized_notes.get('confidence_assessment', 'medium')}

Generate executive summary:"""

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ]

        response = await self.call_llm(messages, max_tokens=300)
        return response[:max_length]
