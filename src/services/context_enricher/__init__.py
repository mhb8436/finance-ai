"""Context Enricher Service.

Pre-fetches relevant data based on query intent analysis.

Example:
    from src.services.context_enricher import get_context_enricher

    enricher = get_context_enricher()
    enriched = await enricher.enrich("삼성전자 주가 알려줘")

    # Get formatted context for LLM
    print(enriched.context_string)

    # Get data sources used
    print(enriched.sources)
"""

from .types import EnrichmentConfig, EnrichedContext
from .enricher import ContextEnricher, get_context_enricher

__all__ = [
    "EnrichmentConfig",
    "EnrichedContext",
    "ContextEnricher",
    "get_context_enricher",
]
