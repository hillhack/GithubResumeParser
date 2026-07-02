"""
LLM provider adapters for the JD Skill Extractor.
Supports: Google Gemini (via google-generativeai) and HuggingFace Inference API.
"""

import requests
import contextvars

# ─── Context Variables for Secure Key Management ───────────────────────────────
gemini_key_ctx = contextvars.ContextVar("gemini_key", default="")
hf_token_ctx   = contextvars.ContextVar("hf_token", default="")
groq_key_ctx   = contextvars.ContextVar("groq_key", default="")

# ─── Groq ────────────────────────────────────────────────────────────────────

def get_groq_response(model: str, prompt: str) -> str:
    """
    Call the Groq REST API (OpenAI compatible).

    Args:
        model:   Model name, e.g. 'llama3-70b-8192'.
        prompt:  Full prompt string.

    Returns:
        Raw text response from the model.
    """
    api_key = groq_key_ctx.get()
    if not api_key:
        raise ValueError("Groq API key not found in context.")

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an expert HR analyst. "
                    "Always respond with valid JSON only, no markdown, no explanations."
                )
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    if not resp.ok:
        raise ValueError(f"Groq API error [{resp.status_code}]: {resp.text}")
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def get_gemini_response(model: str, prompt: str) -> str:
    """
    Call the Google Gemini API using the google-generativeai SDK.

    Args:
        model:   Model name, e.g. 'gemini-1.5-flash'.
        prompt:  Full prompt string.

    Returns:
        Raw text response from the model.
    """
    import google.generativeai as genai  # type: ignore

    api_key = gemini_key_ctx.get()
    if not api_key:
        raise ValueError("Gemini API key not found in context.")

    genai.configure(api_key=api_key)
    model_obj = genai.GenerativeModel(
        model_name=model,
        generation_config={
            "temperature": 0.2,
            "max_output_tokens": 4096,
        },
    )
    response = model_obj.generate_content(prompt)
    return response.text


# ─── HuggingFace Inference API ───────────────────────────────────────────────

HF_API_BASE = "https://api-inference.huggingface.co/models"

# Chat-style models that support the /v1/chat/completions endpoint
CHAT_MODELS = {
    "mistralai/Mixtral-8x7B-Instruct-v0.1",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "meta-llama/Meta-Llama-3-8B-Instruct",
    "HuggingFaceH4/zephyr-7b-beta",
}


def get_huggingface_response(model: str, prompt: str) -> str:
    """
    Call the HuggingFace Inference API.

    Uses the /v1/chat/completions endpoint for instruction-tuned models,
    and falls back to the text-generation endpoint for others.

    Args:
        model:  Full model ID, e.g. 'mistralai/Mixtral-8x7B-Instruct-v0.1'.
        prompt: Full prompt string.

    Returns:
        Raw text response from the model.
    """
    token = hf_token_ctx.get()
    if not token:
        raise ValueError("HuggingFace token not found in context.")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    if model in CHAT_MODELS:
        return _hf_chat(headers, model, prompt)
    return _hf_text_generation(headers, model, prompt)


def _hf_chat(headers: dict, model: str, prompt: str) -> str:
    """Use the OpenAI-compatible /v1/chat/completions endpoint."""
    url = f"https://api-inference.huggingface.co/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an expert HR analyst. "
                    "Always respond with valid JSON only, no markdown, no explanations."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 4096,
        "temperature": 0.2,
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    _raise_for_hf_error(resp)
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def _hf_text_generation(headers: dict, model: str, prompt: str) -> str:
    """Use the standard text-generation endpoint."""
    url = f"{HF_API_BASE}/{model}"
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 4096,
            "temperature": 0.2,
            "return_full_text": False,
        },
        "options": {"wait_for_model": True},
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    _raise_for_hf_error(resp)
    data = resp.json()

    if isinstance(data, list):
        return data[0].get("generated_text", "")
    return data.get("generated_text", str(data))


def _raise_for_hf_error(resp: requests.Response) -> None:
    """Raise a readable error for HuggingFace API failures."""
    if resp.status_code == 401:
        raise ValueError(
            "HuggingFace token is invalid or expired. "
            "Please check your token at https://huggingface.co/settings/tokens"
        )
    if resp.status_code == 403:
        raise ValueError(
            f"Access denied to this model. "
            "You may need to accept the model's license on HuggingFace."
        )
    if resp.status_code == 503:
        raise ValueError(
            "Model is loading on HuggingFace servers. Please retry in 30-60 seconds."
        )
    if not resp.ok:
        try:
            msg = resp.json().get("error", resp.text)
        except Exception:
            msg = resp.text
        raise ValueError(f"HuggingFace API error [{resp.status_code}]: {msg}")
