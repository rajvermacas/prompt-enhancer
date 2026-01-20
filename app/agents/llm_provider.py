from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from app.config import Settings


class LLMConfigurationError(Exception):
    """Raised when LLM is not properly configured."""

    pass


def get_llm(settings: Settings):
    """Factory function to create LLM based on configuration."""
    if settings.llm_provider == "openrouter":
        if not settings.openrouter_api_key:
            raise LLMConfigurationError("OPENROUTER_API_KEY is required")
        return ChatOpenAI(
            model=settings.openrouter_model,
            openai_api_key=settings.openrouter_api_key,
            openai_api_base="https://openrouter.ai/api/v1",
        )
    elif settings.llm_provider == "azure":
        if not settings.azure_openai_api_key:
            raise LLMConfigurationError("AZURE_OPENAI_API_KEY is required")
        if not settings.azure_openai_endpoint:
            raise LLMConfigurationError("AZURE_OPENAI_ENDPOINT is required")
        if not settings.azure_openai_deployment:
            raise LLMConfigurationError("AZURE_OPENAI_DEPLOYMENT is required")
        return ChatOpenAI(
            model=settings.azure_openai_deployment,
            openai_api_key=settings.azure_openai_api_key,
            openai_api_base=settings.azure_openai_endpoint,
        )
    elif settings.llm_provider == "gemini":
        if not settings.google_api_key:
            raise LLMConfigurationError("GOOGLE_API_KEY is required")
        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.google_api_key,
        )
    else:
        raise LLMConfigurationError(f"Unknown LLM provider: {settings.llm_provider}")
