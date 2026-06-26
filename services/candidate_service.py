from models.candidate import CandidateProfile
from services.llm_service import call_llm
from utils.parser import extract_json_from_llm
from typing import List, Dict

def analyze_candidate_profile(profile: CandidateProfile, raw_repos: List[dict], model_choice: str = "Groq") -> CandidateProfile:
    """Uses an LLM to analyze the candidate's raw GitHub profile and repositories to infer technical skills and domains."""
    
    repo_summaries = []
    for r in raw_repos[:50]: # Send up to 50 repos for context
        meta = r.get("metadata", {})
        repo_summaries.append({
            "name": meta.get("name"),
            "description": meta.get("description"),
            "languages": list(meta.get("languages", {}).keys()) or [meta.get("default_language")],
            "topics": meta.get("topics", [])
        })
        
    prompt = f"""Analyze the following GitHub candidate profile and their repository history to extract deep technical insights.

Candidate Profile:
Name: {profile.name}
Bio: {profile.bio}
Company/Orgs: {profile.organizations}
Location: {profile.location}
Website: {profile.website}

Repositories Summary:
{repo_summaries}

Extract any social links (LinkedIn, Twitter/X, Portfolio) from their website or bio.
Identify their primary technical domains (e.g. Frontend, Data Science, DevOps).
Consolidate their programming languages, frameworks, tools, databases, cloud, and AI/ML technologies based on their bio and repository topics/languages.

Return ONLY a JSON object:
{{
    "linkedin_url": "...",
    "portfolio_url": "...",
    "primary_domains": ["..."],
    "programming_languages": ["..."],
    "frameworks": ["..."],
    "tools_and_platforms": ["..."],
    "databases": ["..."],
    "cloud_technologies": ["..."],
    "ai_ml_technologies": ["..."],
    "other_skills": ["..."]
}}
"""
    sys_prompt = "You are an expert technical recruiter analyzing a GitHub profile to extract structured skill data. Output ONLY valid JSON."
    
    raw = call_llm(sys_prompt, prompt, model_choice)
    parsed = extract_json_from_llm(raw)
    
    # Update profile with analyzed data
    if parsed.get("linkedin_url"):
        profile.linkedin_url = parsed.get("linkedin_url", "")
    if parsed.get("portfolio_url") and not profile.website:
        profile.website = parsed.get("portfolio_url", "")
        
    profile.primary_domains = parsed.get("primary_domains", [])
    profile.programming_languages = parsed.get("programming_languages", [])
    profile.frameworks = parsed.get("frameworks", [])
    profile.tools_and_platforms = parsed.get("tools_and_platforms", [])
    profile.databases = parsed.get("databases", [])
    profile.cloud_technologies = parsed.get("cloud_technologies", [])
    profile.ai_ml_technologies = parsed.get("ai_ml_technologies", [])
    profile.other_skills = parsed.get("other_skills", [])
    
    return profile
