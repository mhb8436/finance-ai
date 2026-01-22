"""Type definitions for LLM service."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    AZURE = "azure"  # Azure OpenAI
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    GROQ = "groq"
    LOCAL = "local"


@dataclass
class LLMConfig:
    """Configuration for LLM provider."""

    model: str
    api_key: str
    base_url: str
    provider: LLMProvider | None = None  # Auto-detected if None
    temperature: float = 0.3
    max_tokens: int = 4096

    # Azure OpenAI specific fields
    azure_deployment: str | None = None  # Azure deployment name
    azure_api_version: str = "2024-02-01"  # Azure API version


@dataclass
class ToolParameter:
    """Parameter definition for a tool."""

    name: str
    type: str
    description: str
    required: bool = True
    enum: list[str] | None = None


@dataclass
class ToolDefinition:
    """Unified tool definition format."""

    name: str
    description: str
    parameters: list[ToolParameter]

    def to_openai_format(self) -> dict[str, Any]:
        """Convert to OpenAI function calling format."""
        properties = {}
        required = []

        for param in self.parameters:
            prop = {"type": param.type, "description": param.description}
            if param.enum:
                prop["enum"] = param.enum
            properties[param.name] = prop
            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

    def to_anthropic_format(self) -> dict[str, Any]:
        """Convert to Anthropic tool format."""
        properties = {}
        required = []

        for param in self.parameters:
            prop = {"type": param.type, "description": param.description}
            if param.enum:
                prop["enum"] = param.enum
            properties[param.name] = prop
            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }


@dataclass
class ToolCall:
    """Unified tool call result."""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class LLMResponse:
    """Unified LLM response."""

    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    finish_reason: str = "stop"
    usage: dict[str, int] | None = None
    raw_response: Any = None


@dataclass
class Message:
    """Unified message format."""

    role: str  # "system", "user", "assistant", "tool"
    content: str
    tool_call_id: str | None = None  # For tool responses
    tool_calls: list[ToolCall] | None = None  # For assistant messages with tool calls

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result: dict[str, Any] = {"role": self.role, "content": self.content}
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id
        return result


def parse_openai_tool_definitions(tools: list[dict[str, Any]]) -> list[ToolDefinition]:
    """Parse OpenAI-format tool definitions into unified format."""
    result = []
    for tool in tools:
        if tool.get("type") != "function":
            continue

        func = tool["function"]
        params = []

        properties = func.get("parameters", {}).get("properties", {})
        required = func.get("parameters", {}).get("required", [])

        for param_name, param_def in properties.items():
            params.append(
                ToolParameter(
                    name=param_name,
                    type=param_def.get("type", "string"),
                    description=param_def.get("description", ""),
                    required=param_name in required,
                    enum=param_def.get("enum"),
                )
            )

        result.append(
            ToolDefinition(
                name=func["name"],
                description=func.get("description", ""),
                parameters=params,
            )
        )

    return result
