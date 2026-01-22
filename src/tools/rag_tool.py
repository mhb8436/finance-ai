"""RAG Tool for Agent Usage.

Provides tool functions and OpenAI-compatible tool definitions for
RAG operations in the chat agent.
"""

from typing import Any

from src.services.rag import get_rag_service, SearchResult


# Tool definitions for OpenAI function calling
RAG_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": (
                "Search the knowledge base for information relevant to the query. "
                "Use this when the user asks questions that might be answered by "
                "documents in the knowledge base."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find relevant information.",
                    },
                    "kb_name": {
                        "type": "string",
                        "description": "Name of the knowledge base to search. Use 'default' if not specified.",
                        "default": "default",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to retrieve.",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_knowledge_bases",
            "description": (
                "List all available knowledge bases and their statistics."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]


async def search_knowledge_base(
    query: str,
    kb_name: str = "default",
    top_k: int = 5,
) -> dict[str, Any]:
    """Search the knowledge base for relevant information.

    Args:
        query: Search query.
        kb_name: Name of the knowledge base to search.
        top_k: Number of results to retrieve.

    Returns:
        Dictionary containing search results.
    """
    try:
        service = get_rag_service()
        result: SearchResult = await service.search(
            query=query,
            kb_name=kb_name,
            top_k=top_k,
            generate_answer=True,
        )

        return {
            "success": True,
            "answer": result.answer,
            "sources": [
                {
                    "content": chunk.content[:500],  # Truncate for tool response
                    "source": chunk.metadata.get("source", "Unknown"),
                    "relevance": chunk.metadata.get("relevance_score", 0),
                }
                for chunk in result.chunks
            ],
            "num_results": len(result.chunks),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def list_knowledge_bases() -> dict[str, Any]:
    """List all available knowledge bases.

    Returns:
        Dictionary containing list of knowledge bases.
    """
    try:
        service = get_rag_service()
        kb_list = service.list_knowledge_bases()

        return {
            "success": True,
            "knowledge_bases": kb_list,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


# Tool function mapping for chat agent
RAG_TOOL_FUNCTIONS = {
    "search_knowledge_base": search_knowledge_base,
    "list_knowledge_bases": list_knowledge_bases,
}


async def execute_rag_tool(
    tool_name: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Execute a RAG tool by name.

    Args:
        tool_name: Name of the tool to execute.
        arguments: Tool arguments.

    Returns:
        Tool execution result.
    """
    if tool_name not in RAG_TOOL_FUNCTIONS:
        return {
            "success": False,
            "error": f"Unknown RAG tool: {tool_name}",
        }

    func = RAG_TOOL_FUNCTIONS[tool_name]
    return await func(**arguments)
