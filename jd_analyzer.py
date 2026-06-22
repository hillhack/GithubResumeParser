"""Job Description analysis using Groq LLM."""

import json
import logging
from typing import Any

from groq import Groq

log = logging.getLogger(__name__)

_SYSTEM = """You are an expert technical recruiter. Extract structured information from job descriptions.
Return ONLY valid JSON — no markdown fences, no commentary."""

_JD_PROMPT = """Analyze this job description and return a JSON object with exactly these keys:
{{
  "role_title": "inferred job title",
  "domain": "e.g. Machine Learning, Backend, Frontend, DevOps, Data Science, Full Stack",
  "experience_level": "intern | junior | mid | senior | staff | principal",
  "required_skills": ["skill1", "skill2"],
  "preferred_skills": ["skill1", "skill2"],
  "technologies": ["tech1", "tech2"],
  "keywords": ["important domain keywords"],
  "responsibilities": ["key responsibility 1", "key responsibility 2"]
}}

Job Description:
{jd_text}"""


def analyze_jd(jd_text: str, client: Groq, model: str = "llama-3.3-70b-versatile") -> dict[str, Any]:
    """
    Extract structured requirements from a job description.

    Returns a dict with role_title, domain, required_skills, etc.
    """
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": _JD_PROMPT.format(jd_text=jd_text[:4000])},
            ],
            temperature=0.1,
            max_tokens=1024,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content or "{}"
        result = json.loads(raw)
        # Ensure all expected keys exist
        defaults: dict[str, Any] = {
            "role_title": "Software Engineer",
            "domain": "Software Engineering",
            "experience_level": "mid",
            "required_skills": [],
            "preferred_skills": [],
            "technologies": [],
            "keywords": [],
            "responsibilities": [],
        }
        for key, val in defaults.items():
            result.setdefault(key, val)
        return result
    except Exception as e:
        log.error("JD analysis failed: %s", e)
        return {
            "role_title": "Software Engineer",
            "domain": "Software Engineering",
            "experience_level": "mid",
            "required_skills": [],
            "preferred_skills": [],
            "technologies": [],
            "keywords": [],
            "responsibilities": [],
        }
