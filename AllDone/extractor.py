"""
extractor.py — Backend logic for JD skill extraction.
Handles prompt construction, LLM dispatch, and JSON parsing.
"""

from __future__ import annotations
import json
import re

from llm_providers import get_gemini_response, get_huggingface_response, get_groq_response


# ─── Prompt ──────────────────────────────────────────────────────────────────

EXTRACTION_PROMPT = """You are an expert HR analyst and skills taxonomy specialist.

Analyze the following Job Description(s) carefully and extract a comprehensive, structured breakdown.

{{
  "job_title": "string",
  "company_or_project": "string or null",
  "domain": ["list of domain areas, e.g. Data Science, IoT, Manufacturing"],
  "technical_skills": ["list of hard technical skills"],
  "tools_and_technologies": ["list of specific tools, libraries, frameworks, platforms"],
  "programming_languages": ["list of programming languages"],
  "domain_knowledge": ["list of domain-specific knowledge areas"],
  "key_responsibilities": ["top 5-7 responsibilities as short bullets"],
  "nice_to_have": ["optional/preferred skills"],
  "summary": "2-3 sentence plain-language summary of what this role needs"
}}

Rules:
- EXHAUSTIVE EXTRACTION: Do not miss ANY technical term mentioned or implied.
- INFER IMPLIED SKILLS: If the JD mentions "high-frequency sensor data" infer ["Time Series Analysis", "Signal Processing"]. If it mentions "failure modes" infer ["Root Cause Analysis", "Anomaly Detection"]. If it mentions "quality control" infer ["Statistical Process Control"]. Use domain knowledge to surface implicit requirements.
- ATOMIC KEYWORDS ONLY: Break every sentence and list into single words or short 1-3 word phrases.
- NO FULL SENTENCES in any list field.
- Distribute "Preferred/Nice to have" as atomic keywords into `nice_to_have`.
- FILTER NOISE: Ignore document metadata such as "Google Docs", "Updated automatically", "Report abuse", "Published using", dates, and URLs.
- Separate tools (Pandas, Power BI) from general skills (Machine Learning, Statistical Modeling).
- Do not duplicate items across arrays.
- Use clean labels (e.g. "Python" not "Python programming", "MLOps" not "Basic understanding of MLOps").

Examples of GOOD atomic extraction from "Familiarity with Python libraries such as NumPy, Pandas, Scikit-learn":
  tools_and_technologies: ["NumPy", "Pandas", "Scikit-learn"]

Examples of GOOD inference from "analyze audio files of friction and vibration":
  technical_skills: ["Audio Analysis", "Vibration Analysis", "Signal Processing"]


JD TEXT:
{jd_text}
"""


# ─── JSON Parser ─────────────────────────────────────────────────────────────

def parse_llm_json(raw: str) -> dict:
    """
    Robustly extract a JSON object from an LLM response.
    Handles markdown code fences and leading/trailing text.

    Args:
        raw: Raw string response from the LLM.

    Returns:
        Parsed Python dict.

    Raises:
        json.JSONDecodeError: If no valid JSON block is found.
    """
    raw = raw.strip()

    # Strip ```json ... ``` or ``` ... ``` fences
    fenced = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", raw)
    if fenced:
        raw = fenced.group(1)

    # Find the outermost { ... } block
    start = raw.find("{")
    end   = raw.rfind("}") + 1
    if start != -1 and end > start:
        raw = raw[start:end]

    return json.loads(raw)


# ─── Extraction Orchestrator ──────────────────────────────────────────────────

def extract_skills(
    jd_text: str,
    provider: str,
    model: str | None = None,
) -> dict:
    """
    Build the prompt, call the selected LLM, and return parsed results.
    Note: API keys must be set in the respective contextvars before calling this.

    Args:
        jd_text:  Raw job description text (one or multiple JDs).
        provider: "Gemini", "HuggingFace", or "Groq".
        model:    Model name for the selected provider.

    Returns:
        Dict matching the extraction schema.

    Raises:
        ValueError:          On missing credentials or unsupported provider.
        json.JSONDecodeError: If the LLM response cannot be parsed.
        Exception:           On LLM API errors (propagated from llm_providers).
    """
    if not jd_text.strip():
        raise ValueError("JD text is empty.")

    prompt = EXTRACTION_PROMPT.format(jd_text=jd_text)

    if provider == "Gemini":
        raw = get_gemini_response(model, prompt)

    elif provider == "HuggingFace":
        raw = get_huggingface_response(model, prompt)

    elif provider == "Groq":
        raw = get_groq_response(model, prompt)

    else:
        raise ValueError(f"Unsupported provider: {provider}")

    return parse_llm_json(raw), raw  # return (parsed_dict, raw_text)
