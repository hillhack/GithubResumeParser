"""Abstract base class for all LLM providers."""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Every provider must implement generate() and return a raw string (expected to be JSON)."""

    @abstractmethod
    def generate(self, sys_prompt: str, user_prompt: str, temperature: float = 0.1) -> str:
        """
        Call the provider's API and return the raw response string.

        Args:
            sys_prompt:   System / instruction prompt.
            user_prompt:  User / task prompt.
            temperature:  Sampling temperature (lower = more deterministic).

        Returns:
            Raw response string, expected to contain JSON for downstream parsing.
        """
        ...
