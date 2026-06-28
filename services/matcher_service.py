from models.repository import RepositoryProfile
from models.job_description import JobDescriptionProfile
from models.match_result import MatchResult
from services.llm_service import call_llm
from utils.parser import extract_json_from_llm
import json

def match_repository_to_jd(repo_profile: RepositoryProfile, jd_profile: JobDescriptionProfile, readme_text: str = "", model_choice: str = "Groq") -> MatchResult:
    """Matches a structured RepositoryProfile against a structured JobDescriptionProfile using an LLM, verifying missing skills against the README."""
    if not readme_text:
        readme_text = ""
    
    prompt = f"""Compare the Candidate's Repository Profile against the Job Description Profile.

Candidate Repository Profile:
{repo_profile.model_dump_json()}

Job Description Profile:
{jd_profile.model_dump_json()}

Calculate how well this specific repository demonstrates the requirements of the job. 
Compare the extracted repository profile against BOTH the "Required Skills" and "Preferred Skills" from the Job Description.
Provide an overall score between 0.0 and 1.0 (where 1.0 means the repo perfectly demonstrates the core required skills).
Extract which specific skills from the JD are matched by this repo, and which are missing.
Provide brief evidence sentences for the matches based on the repository data.

CRITICAL RULES FOR SKILL MATCHING:
1. Be extremely strict. A skill from the Job Description should ONLY be listed in `matched_skills` if there is clear, direct evidence in the repository profile or the README that the candidate actually used, implemented, or demonstrated it in this specific project.
2. Do NOT make broad assumptions or loose semantic leaps. For example, do not assume they know "Machine Learning fundamentals and algorithms" just because the project uses an LLM API, or that they have a "research-oriented mindset" without concrete research activities documented.
3. Before finalizing the `missing_skills` array, you MUST verify if the skill is mentioned anywhere in the README snippet. Do NOT list a skill as missing if it exists in the README!

=== README Snippet ===
{(readme_text or "No README provided")[:3000]}
======================

Return ONLY a JSON object:
{{
    "overall_score": 0.85,
    "matched_skills": ["..."],
    "missing_skills": ["..."],
    "matched_libraries": ["..."],
    "matched_frameworks": ["..."],
    "matched_tools": ["..."],
    "matched_domain": "...",
    "matched_keywords": ["..."],
    "evidence": {{"skill_name": "evidence sentence..."}},
    "confidence": "High"
}}
"""
    
    sys_prompt = "You are an expert technical evaluator. Compare the candidate's repository capabilities against the job requirements. Provide a JSON response only."
    
    raw = call_llm(sys_prompt, prompt, model_choice=model_choice)
    parsed = extract_json_from_llm(raw)
    
    matched_skills = parsed.get("matched_skills", [])
    missing_skills = parsed.get("missing_skills", [])
    evidence = parsed.get("evidence", {})
    
    # Ensure all JD skills are evaluated by the fallback mechanism
    all_jd_skills = (
        jd_profile.required_skills + 
        jd_profile.preferred_skills + 
        jd_profile.tools + 
        jd_profile.frameworks + 
        jd_profile.libraries
    )
    for jd_skill in all_jd_skills:
        if jd_skill not in matched_skills and jd_skill not in missing_skills:
            missing_skills.append(jd_skill)

    
    # Post-process to prevent false-negative missing skills
    readme_lower = readme_text.lower()
    profile_sources = []
    for field in ["primary_skills", "secondary_skills", "frameworks", "libraries", "tools", "programming_languages", "apis", "keywords"]:
        val = getattr(repo_profile, field, [])
        if isinstance(val, list):
            profile_sources.extend([str(item).lower() for item in val])
            
    still_missing = []
    for skill in missing_skills:
        skill_lower = skill.lower()
        variations = [skill_lower]
        if "(" in skill_lower and ")" in skill_lower:
            parts = skill_lower.replace(")", "").split("(")
            variations.extend([p.strip() for p in parts if p.strip()])
            
        # Add singular/plural variations and hyphen replacements
        extended_vars = []
        for v in variations:
            if v.endswith("s"):
                extended_vars.append(v[:-1])
            else:
                extended_vars.append(v + "s")
            if "-" in v:
                extended_vars.append(v.replace("-", " "))
        variations.extend(extended_vars)
        variations = list(set(variations))
        
        found_in_readme = any(var in readme_lower for var in variations)
        found_in_profile = any(var in src or src in var for var in variations for src in profile_sources)
        
        if found_in_readme or found_in_profile:
            if skill not in matched_skills:
                matched_skills.append(skill)
            if skill not in evidence:
                if found_in_readme:
                    evidence[skill] = f"The project README references {skill}."
                else:
                    evidence[skill] = f"The project profile lists {skill} in its technical metadata."
        else:
            still_missing.append(skill)
            
    return MatchResult(
        repository_name=repo_profile.name,
        overall_score=float(parsed.get("overall_score", 0.0)),
        matched_skills=matched_skills,
        missing_skills=still_missing,
        matched_libraries=parsed.get("matched_libraries", []),
        matched_frameworks=parsed.get("matched_frameworks", []),
        matched_tools=parsed.get("matched_tools", []),
        matched_domain=str(parsed.get("matched_domain", "")),
        matched_keywords=parsed.get("matched_keywords", []),
        evidence=evidence,
        confidence=str(parsed.get("confidence", ""))
    )
