import os
import logging
import time

log = logging.getLogger(__name__)

def call_llm(sys_prompt: str, user_prompt: str, model_choice: str = "Groq", temperature: float = 0.1) -> str:
    """Dispatches request to appropriate LLM API. Retries on 429 rate-limit errors."""
    max_retries = 3
    base_wait = 15  # seconds

    if "Groq" in model_choice:
        from groq import Groq
        import groq as groq_module
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        for attempt in range(max_retries):
            try:
                resp = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_prompt}],
                    temperature=temperature, response_format={"type": "json_object"}
                )
                return resp.choices[0].message.content or "{}"
            except groq_module.RateLimitError as e:
                err_str = str(e)
                is_daily_limit = ("tokens per day" in err_str or "TPD" in err_str or "per_day" in err_str)
                if is_daily_limit:
                    log.error(f"Groq DAILY token limit exhausted. Will use keyword fallback. {e}")
                    raise
                if attempt < max_retries - 1:
                    wait = base_wait * (2 ** attempt)
                    log.warning(f"Groq 429 rate limit — waiting {wait}s before retry {attempt+1}/{max_retries-1}")
                    time.sleep(wait)
                else:
                    log.error(f"Groq rate limit exhausted after {max_retries} attempts: {e}")
                    raise
            except (groq_module.InternalServerError, groq_module.APIStatusError) as e:
                if attempt < max_retries - 1:
                    wait = base_wait * (2 ** attempt)
                    log.warning(f"Groq 503/API error — waiting {wait}s before retry {attempt+1}/{max_retries-1}: {e}")
                    time.sleep(wait)
                else:
                    log.error(f"Groq API error exhausted after {max_retries} attempts: {e}")
                    raise
    else:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=FutureWarning)
            import google.generativeai as genai
        from google.api_core.exceptions import ResourceExhausted, GoogleAPIError
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-2.5-flash')
        for attempt in range(max_retries):
            try:
                response = model.generate_content(
                    f"System Instruction: {sys_prompt}\n\nUser Request: {user_prompt}",
                    generation_config={"response_mime_type": "application/json", "temperature": temperature}
                )
                return response.text or "{}"
            except ResourceExhausted as e:
                err_str = str(e)
                import re
                seconds_match = re.search(r"retry in ([0-9\.]+)s", err_str)
                if not seconds_match:
                    seconds_match = re.search(r"seconds:\s*(\d+)", err_str)
                
                wait = float(seconds_match.group(1)) + 1.0 if seconds_match else base_wait * (2 ** attempt)
                wait = min(wait, 65.0)
                
                if attempt < max_retries - 1:
                    log.warning(f"Gemini 429 rate limit — waiting {wait}s before retry {attempt+1}/{max_retries-1}")
                    time.sleep(wait)
                else:
                    log.error(f"Gemini rate limit exhausted after {max_retries} attempts: {e}")
                    raise
            except GoogleAPIError as e:
                if attempt < max_retries - 1:
                    wait = base_wait * (2 ** attempt)
                    log.warning(f"Gemini API error — waiting {wait}s before retry {attempt+1}/{max_retries-1}: {e}")
                    time.sleep(wait)
                else:
                    log.error(f"Gemini API error exhausted after {max_retries} attempts: {e}")
                    raise
    return "{}"
