class FAQBotException(Exception):
    """Base exception for FAQ bot."""
    pass


class OpenAIServiceError(FAQBotException):
    """Exception raised for OpenAI service errors."""
    pass


class FAQNotFoundError(FAQBotException):
    """Exception raised when FAQ content is not found."""
    pass


class ConfigurationError(FAQBotException):
    """Exception raised for configuration errors."""
    pass 