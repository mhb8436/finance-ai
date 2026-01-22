"""Error classes for LLM service."""


class LLMError(Exception):
    """Base exception for LLM service errors."""

    def __init__(self, message: str, provider: str | None = None):
        self.provider = provider
        super().__init__(message)


class LLMConfigError(LLMError):
    """Configuration error (invalid API key, model, etc.)."""

    pass


class LLMConnectionError(LLMError):
    """Connection error (network, timeout, etc.)."""

    pass


class LLMRateLimitError(LLMError):
    """Rate limit exceeded error."""

    def __init__(
        self,
        message: str,
        provider: str | None = None,
        retry_after: float | None = None,
    ):
        self.retry_after = retry_after
        super().__init__(message, provider)


class LLMAuthenticationError(LLMError):
    """Authentication error (invalid API key)."""

    pass


class LLMModelNotFoundError(LLMError):
    """Model not found or not available."""

    pass


class LLMContextLengthError(LLMError):
    """Context length exceeded error."""

    def __init__(
        self,
        message: str,
        provider: str | None = None,
        max_tokens: int | None = None,
        requested_tokens: int | None = None,
    ):
        self.max_tokens = max_tokens
        self.requested_tokens = requested_tokens
        super().__init__(message, provider)


class LLMToolCallError(LLMError):
    """Error in tool calling execution."""

    def __init__(
        self,
        message: str,
        provider: str | None = None,
        tool_name: str | None = None,
    ):
        self.tool_name = tool_name
        super().__init__(message, provider)


class LLMProviderNotSupportedError(LLMError):
    """Provider not supported error."""

    pass
