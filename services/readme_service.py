from models.repository import Repository, RepositoryProfile
from services.llm_service import call_llm
from utils.parser import extract_json_from_llm
import json

def generate_repository_profile(repo: Repository, model_choice: str = "Groq") -> RepositoryProfile:
    """Uses LLM to generate a structured RepositoryProfile based on deterministic data."""
    
    files_context = "\n".join([f"=== {k} ===\n{v[:1000]}" for k, v in repo.files.file_contents.items()])
    
    prompt = f"""Analyze this GitHub repository and extract structured knowledge.
Repository Name: {repo.metadata.name}
Description: {repo.metadata.description or "N/A"}
Topics: {', '.join(repo.metadata.topics) or "N/A"}
Detected Languages: {', '.join(repo.metadata.languages.keys()) or "N/A"}
Detected Files: {', '.join(repo.files.detected_files) or "N/A"}

{files_context}

=== README Snippet ===
{(repo.files.readme or "No README")[:3000]}

Extract the technologies, frameworks, domain, and purpose of this repository. Combine what you see in the README with the deterministic files. If a technology is mentioned in the README but not the requirements, include it anyway.

Return a JSON object exactly matching this structure (do not use markdown formatting in strings):
{{
    "one_line_summary": "...",
    "project_purpose": "...",
    "problem_solved": "...",
    "target_users": "...",
    "project_type": "...",
    "domain": "...",
    "key_features": ["..."],
    "architecture_patterns": ["..."],
    "primary_skills": ["..."],
    "secondary_skills": ["..."],
    "frameworks": ["..."],
    "libraries": ["..."],
    "tools": ["..."],
    "programming_languages": ["..."],
    "deployment": ["..."],
    "database": ["..."],
    "cloud": ["..."],
    "ai_models": ["..."],
    "apis": ["..."],
    "visualization": ["..."],
    "research_area": "...",
    "keywords": ["..."],
    "tags": ["..."],
    "evidence_summary": "..."
}}
"""
    
    sys_prompt = "You are an expert technical repository analyzer. Extract knowledge deterministically and infer missing details where logical. Output ONLY JSON."
    
    raw = call_llm(sys_prompt, prompt, model_choice=model_choice)
    parsed = extract_json_from_llm(raw)
    
    # Construct the profile, defaulting to empty strings/lists if keys are missing
    profile = RepositoryProfile(
        name=repo.metadata.name,
        one_line_summary=parsed.get("one_line_summary", ""),
        project_purpose=parsed.get("project_purpose", ""),
        problem_solved=parsed.get("problem_solved", ""),
        target_users=parsed.get("target_users", ""),
        project_type=parsed.get("project_type", ""),
        domain=parsed.get("domain", ""),
        key_features=parsed.get("key_features", []),
        architecture_patterns=parsed.get("architecture_patterns", []),
        primary_skills=parsed.get("primary_skills", []),
        secondary_skills=parsed.get("secondary_skills", []),
        frameworks=parsed.get("frameworks", []),
        libraries=parsed.get("libraries", []),
        tools=parsed.get("tools", []),
        programming_languages=parsed.get("programming_languages", []),
        deployment=parsed.get("deployment", []),
        database=parsed.get("database", []),
        cloud=parsed.get("cloud", []),
        ai_models=parsed.get("ai_models", []),
        apis=parsed.get("apis", []),
        visualization=parsed.get("visualization", []),
        research_area=parsed.get("research_area", ""),
        keywords=parsed.get("keywords", []),
        tags=parsed.get("tags", []),
        evidence_summary=parsed.get("evidence_summary", "")
    )
    
    return profile
