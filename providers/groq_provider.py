"""Groq provider — Llama 3.3 70B via Groq API."""

import os
import time
import logging
from providers.base import LLMProvider

log = logging.getLogger(__name__)

_MODEL = "llama-3.3-70b-versatile"
_MAX_RETRIES = 3
_BASE_WAIT = 15


class GroqProvider(LLMProvider):
    """Calls Groq's chat completions API with automatic retry on rate limits."""

    def generate(self, sys_prompt: str, user_prompt: str, temperature: float = 0.1) -> str:
        from groq import Groq
        import groq as groq_module
        from utils.keys import api_keys_ctx

        keys = api_keys_ctx.get()
        api_key = keys.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set. Please add it in the sidebar or .env file.")

        client = Groq(api_key=api_key)

        for attempt in range(_MAX_RETRIES):
            try:
                resp = client.chat.completions.create(
                    model=_MODEL,
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temperature,
                    response_format={"type": "json_object"},
                )
                return resp.choices[0].message.content or "{}"

            except groq_module.RateLimitError as e:
                err = str(e)
                if "tokens per day" in err or "TPD" in err or "per_day" in err:
                    log.error("Groq daily token limit exhausted.")
                    raise
                wait = _BASE_WAIT * (2 ** attempt)
                if attempt < _MAX_RETRIES - 1:
                    log.warning(f"Groq 429 — retrying in {wait}s ({attempt + 1}/{_MAX_RETRIES - 1})")
                    time.sleep(wait)
                else:
                    raise

            except (groq_module.InternalServerError, groq_module.APIStatusError) as e:
                wait = _BASE_WAIT * (2 ** attempt)
                if attempt < _MAX_RETRIES - 1:
                    log.warning(f"Groq API error — retrying in {wait}s: {e}")
                    time.sleep(wait)
                else:
                    raise

        return "{}"
