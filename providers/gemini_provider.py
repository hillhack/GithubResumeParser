"""Gemini provider — Google Gemini 2.5 Flash."""

import os
import re
import time
import logging
import warnings
from providers.base import LLMProvider

log = logging.getLogger(__name__)

_MODEL = "gemini-2.5-flash"
_MAX_RETRIES = 3
_BASE_WAIT = 15


class GeminiProvider(LLMProvider):
    """Calls Google Gemini API with automatic retry on rate limits."""

    def generate(self, sys_prompt: str, user_prompt: str, temperature: float = 0.1) -> str:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=FutureWarning)
            import google.generativeai as genai
        from google.api_core.exceptions import ResourceExhausted, GoogleAPIError
        from utils.keys import api_keys_ctx

        keys = api_keys_ctx.get()
        api_key = keys.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set. Please add it in the Custom API Keys sidebar.")

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(_MODEL)

        for attempt in range(_MAX_RETRIES):
            try:
                response = model.generate_content(
                    f"System Instruction: {sys_prompt}\n\nUser Request: {user_prompt}",
                    generation_config={
                        "response_mime_type": "application/json",
                        "temperature": temperature,
                    },
                )
                return response.text or "{}"

            except ResourceExhausted as e:
                err = str(e)
                m = re.search(r"retry in ([0-9\.]+)s", err) or re.search(r"seconds:\s*(\d+)", err)
                wait = min(float(m.group(1)) + 1.0 if m else _BASE_WAIT * (2 ** attempt), 65.0)
                if attempt < _MAX_RETRIES - 1:
                    log.warning(f"Gemini 429 — retrying in {wait}s ({attempt + 1}/{_MAX_RETRIES - 1})")
                    time.sleep(wait)
                else:
                    raise

            except GoogleAPIError as e:
                wait = _BASE_WAIT * (2 ** attempt)
                if attempt < _MAX_RETRIES - 1:
                    log.warning(f"Gemini API error — retrying in {wait}s: {e}")
                    time.sleep(wait)
                else:
                    raise

        return "{}"
