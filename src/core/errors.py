"""Custom exceptions for FinanceAI."""


class FinanceAIError(Exception):
    """Base exception for FinanceAI."""

    pass


class ConfigError(FinanceAIError):
    """Configuration related errors."""

    pass


class DataFetchError(FinanceAIError):
    """Data fetching related errors."""

    pass


class AnalysisError(FinanceAIError):
    """Analysis related errors."""

    pass


class AgentError(FinanceAIError):
    """Agent execution related errors."""

    pass
