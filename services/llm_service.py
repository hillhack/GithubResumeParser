"""llm_service.py — thin dispatch layer.

All provider-specific logic lives in providers/. This module is a single entry point
so the rest of the codebase doesn't need to know which provider is active.
"""

import logging
from providers import get_provider

log = logging.getLogger(__name__)


def call_llm(sys_prompt: str, user_prompt: str, model_choice: str = "Groq", temperature: float = 0.1) -> str:
    """Dispatch an LLM request to the appropriate provider.

    Args:
        sys_prompt:   System / instruction prompt.
        user_prompt:  User / task prompt.
        model_choice: Provider label from the UI dropdown.
        temperature:  Sampling temperature.

    Returns:
        Raw response string (expected to be JSON).
    """
    provider = get_provider(model_choice)
    return provider.generate(sys_prompt, user_prompt, temperature)
