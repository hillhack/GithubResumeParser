"""Provider factory — returns the correct LLMProvider instance based on model_choice string."""

from providers.base import LLMProvider


def get_provider(model_choice: str) -> LLMProvider:
    """Return an LLMProvider instance matching the given model_choice label."""
    if "Groq" in model_choice:
        from providers.groq_provider import GroqProvider
        return GroqProvider()
    elif "Gemini" in model_choice or "Google" in model_choice:
        from providers.gemini_provider import GeminiProvider
        return GeminiProvider()
    elif "Hugging" in model_choice or "HuggingFace" in model_choice or "HF" in model_choice:
        from providers.huggingface_provider import HuggingFaceProvider
        return HuggingFaceProvider()
    else:
        # Default to Groq
        from providers.groq_provider import GroqProvider
        return GroqProvider()
