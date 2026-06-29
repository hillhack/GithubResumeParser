"""readme_service.py — LLM-based README understanding.

The LLM receives pre-extracted deterministic context (detected technologies,
languages, topics, stars) alongside the README text. This significantly
improves summary and bullet quality while reducing hallucinations.
"""

from models.repository import Repository, RepositoryProfile
from services.llm_service import call_llm
from utils.parser import extract_json_from_llm


def generate_repository_profile(repo: Repository, model_choice: str = "Groq") -> RepositoryProfile:
    """Use an LLM to generate a structured RepositoryProfile enriched with deterministic context."""

    detected = repo.files.detected_technologies
    languages = list(repo.metadata.languages.keys())
    topics = repo.metadata.topics

    # Build a concise context block from dependency files
    dep_files_summary = []
    for fname, content in repo.files.file_contents.items():
        dep_files_summary.append(f"=== {fname} (first 800 chars) ===\n{content[:800]}")
    dep_context = "\n".join(dep_files_summary) if dep_files_summary else "No dependency files found."

    prompt = f"""Analyze this GitHub repository and extract structured knowledge for a resume.

Repository: {repo.metadata.name}
Description: {repo.metadata.description or "N/A"}
Stars: {repo.metadata.stars}
Topics: {', '.join(topics) or "N/A"}
Languages: {', '.join(languages) or "N/A"}
Detected Technologies (parsed from dependency files): {', '.join(detected) or "None"}
Dependency Files:
{dep_context}

README:
{(repo.files.readme or "No README provided")[:3000]}

Using ALL the above context, extract structured knowledge.
The detected technologies from dependency files are ground truth — do not contradict them.
Infer hidden skills that the README or files imply but don't name explicitly.

Return a JSON object exactly matching this structure:
{{
    "one_line_summary": "<15-20 word sentence describing purpose and architecture>",
    "project_purpose": "<what this project does>",
    "problem_solved": "<specific problem it addresses>",
    "target_users": "<who would use this>",
    "project_type": "<e.g. API, CLI, Web App, ML Model, Research, Library>",
    "domain": "<primary domain, e.g. Computer Vision, FinTech, DevOps, NLP>",
    "key_features": ["<feature 1>", "<feature 2>", "<feature 3>"],
    "architecture_patterns": ["<e.g. REST API, Microservices, Event-driven>"],
    "primary_skills": ["<top 5-8 skills demonstrated>"],
    "secondary_skills": ["<supporting skills>"],
    "hidden_skills": ["<inferred skills not explicitly named, e.g. 'API design', 'data pipeline engineering'>"],
    "frameworks": ["<frameworks used>"],
    "libraries": ["<libraries used>"],
    "tools": ["<tools used>"],
    "programming_languages": ["<languages>"],
    "deployment": ["<deployment method, e.g. Docker, Heroku, AWS Lambda>"],
    "database": ["<databases>"],
    "cloud": ["<cloud services>"],
    "ai_models": ["<AI/ML models>"],
    "apis": ["<external APIs consumed>"],
    "visualization": ["<visualization tools>"],
    "research_area": "<if academic/research, the area; else empty>",
    "keywords": ["<technical keywords>"],
    "tags": ["<searchable tags>"],
    "impact": "<one sentence describing the project's value or impact>",
    "resume_bullets": [
        "<Bullet 1: action verb, specific feature, ≤ 20 words>",
        "<Bullet 2: action verb, specific feature, ≤ 20 words>",
        "<Bullet 3: action verb, specific feature, ≤ 20 words>"
    ],
    "evidence_summary": "<one sentence summarizing evidence quality>"
}}
"""

    sys_prompt = (
        "You are an expert technical repository analyst and resume writer. "
        "Extract facts from the provided context only. Do not hallucinate. "
        "Output ONLY valid JSON."
    )

    raw = call_llm(sys_prompt, prompt, model_choice=model_choice)
    parsed = extract_json_from_llm(raw)

    # Merge deterministic tech into LLM output — deterministic data takes precedence
    llm_primary = parsed.get("primary_skills", [])
    merged_primary = list(dict.fromkeys(detected[:10] + llm_primary))  # deduplicate, det first

    profile = RepositoryProfile(
        name=repo.metadata.name,
        one_line_summary=parsed.get("one_line_summary", repo.metadata.description or ""),
        project_purpose=parsed.get("project_purpose", ""),
        problem_solved=parsed.get("problem_solved", ""),
        target_users=parsed.get("target_users", ""),
        project_type=parsed.get("project_type", ""),
        domain=parsed.get("domain", ""),
        key_features=parsed.get("key_features", []),
        architecture_patterns=parsed.get("architecture_patterns", []),
        primary_skills=merged_primary,
        secondary_skills=parsed.get("secondary_skills", []) + parsed.get("hidden_skills", []),
        frameworks=parsed.get("frameworks", []),
        libraries=parsed.get("libraries", []),
        tools=parsed.get("tools", []),
        programming_languages=parsed.get("programming_languages", []) or languages,
        deployment=parsed.get("deployment", []),
        database=parsed.get("database", []),
        cloud=parsed.get("cloud", []),
        ai_models=parsed.get("ai_models", []),
        apis=parsed.get("apis", []),
        visualization=parsed.get("visualization", []),
        research_area=parsed.get("research_area", ""),
        keywords=parsed.get("keywords", []),
        tags=parsed.get("tags", topics),
        evidence_summary=parsed.get("evidence_summary", ""),
        resume_bullets=parsed.get("resume_bullets", []),
        impact=parsed.get("impact", ""),
    )

    return profile
