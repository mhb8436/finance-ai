"""LLM Service Module.

Provides multi-provider LLM support for FinanceAI.

Supported Providers:
- OpenAI (gpt-4o, gpt-4-turbo, etc.)
- Anthropic (claude-3-5-sonnet, claude-3-opus, etc.)
- DeepSeek (deepseek-chat, deepseek-coder)
- Groq (llama, mixtral)
- Local (Ollama, vLLM, LM Studio)

Basic Usage:
    from src.services.llm import complete, stream

    # Simple completion
    response = await complete([
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ])
    print(response.content)

    # Streaming
    async for chunk in stream([{"role": "user", "content": "Hello!"}]):
        print(chunk, end="")

With Tools:
    from src.services.llm import complete

    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_stock_price",
                "description": "Get current stock price",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string"}
                    },
                    "required": ["symbol"]
                }
            }
        }
    ]

    response = await complete(messages, tools=tools)
    if response.tool_calls:
        for tc in response.tool_calls:
            print(f"Tool: {tc.name}, Args: {tc.arguments}")
"""

from .factory import clear_cache, complete, get_provider, stream
from .types import (
    LLMConfig,
    LLMProvider,
    LLMResponse,
    Message,
    ToolCall,
    ToolDefinition,
    ToolParameter,
    parse_openai_tool_definitions,
)
from .errors import (
    LLMError,
    LLMAuthenticationError,
    LLMConfigError,
    LLMConnectionError,
    LLMContextLengthError,
    LLMModelNotFoundError,
    LLMProviderNotSupportedError,
    LLMRateLimitError,
    LLMToolCallError,
)
from .capabilities import get_model_capabilities, ModelCapabilities

__all__ = [
    # Factory functions
    "complete",
    "stream",
    "get_provider",
    "clear_cache",
    # Types
    "LLMConfig",
    "LLMProvider",
    "LLMResponse",
    "Message",
    "ToolCall",
    "ToolDefinition",
    "ToolParameter",
    "parse_openai_tool_definitions",
    # Errors
    "LLMError",
    "LLMAuthenticationError",
    "LLMConfigError",
    "LLMConnectionError",
    "LLMContextLengthError",
    "LLMModelNotFoundError",
    "LLMProviderNotSupportedError",
    "LLMRateLimitError",
    "LLMToolCallError",
    # Capabilities
    "get_model_capabilities",
    "ModelCapabilities",
]
