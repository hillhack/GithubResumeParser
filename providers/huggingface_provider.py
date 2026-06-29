"""HuggingFace provider — uses huggingface_hub InferenceClient.

An HF token is optional. Without one, the anonymous free tier is used (rate limited).
With a token, rate limits are significantly higher.
"""

import os
import time
import logging
import json
from providers.base import LLMProvider

log = logging.getLogger(__name__)

_DEFAULT_MODEL = "Qwen/Qwen2.5-72B-Instruct"
_FALLBACK_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"
_MAX_RETRIES = 3
_BASE_WAIT = 20


class HuggingFaceProvider(LLMProvider):
    """Calls HuggingFace Inference API. Token is optional but recommended."""

    def generate(self, sys_prompt: str, user_prompt: str, temperature: float = 0.1) -> str:
        try:
            from huggingface_hub import InferenceClient
        except ImportError:
            raise ImportError("huggingface_hub is not installed. Run: pip install huggingface_hub")
        from utils.keys import api_keys_ctx

        keys = api_keys_ctx.get()
        token = keys.get("HF_TOKEN") or None
        model = _DEFAULT_MODEL

        client = InferenceClient(model=model, token=token)

        messages = [
            {"role": "system", "content": sys_prompt + "\n\nIMPORTANT: Always respond with valid JSON only. No markdown, no code fences."},
            {"role": "user", "content": user_prompt},
        ]

        for attempt in range(_MAX_RETRIES):
            try:
                response = client.chat_completion(
                    messages=messages,
                    max_tokens=4096,
                    temperature=max(temperature, 0.01),  # HF requires > 0
                )
                content = response.choices[0].message.content or "{}"
                # Strip any accidental markdown fences
                content = content.strip()
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                return content.strip()

            except ValueError as e:
                if "api_key" in str(e) or "hf auth login" in str(e):
                    raise RuntimeError(
                        "Hugging Face now requires a free token to use their API. "
                        "Please get one from huggingface.co/settings/tokens and enter it in the sidebar, "
                        "or switch to Google Gemini (which has a large free tier)."
                    ) from e
                raise
            except Exception as e:
                err = str(e)
                if "429" in err or "rate limit" in err.lower():
                    wait = _BASE_WAIT * (2 ** attempt)
                    if attempt < _MAX_RETRIES - 1:
                        log.warning(f"HuggingFace rate limit — retrying in {wait}s. Add HF_TOKEN for higher limits.")
                        time.sleep(wait)
                    else:
                        raise RuntimeError(
                            "HuggingFace rate limit exceeded. "
                            "Add your HF_TOKEN in the sidebar for more requests, "
                            "or switch to Groq or Gemini."
                        ) from e
                else:
                    # Try fallback model on first attempt errors
                    if attempt == 0 and model == _DEFAULT_MODEL:
                        log.warning(f"HF primary model error, trying fallback: {e}")
                        model = _FALLBACK_MODEL
                        client = InferenceClient(model=model, token=token)
                    elif attempt < _MAX_RETRIES - 1:
                        wait = _BASE_WAIT * (2 ** attempt)
                        log.warning(f"HF API error — retrying in {wait}s: {e}")
                        time.sleep(wait)
                    else:
                        raise

        return "{}"
