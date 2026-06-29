from models.repository import RepositoryProfile
from models.job_description import JobDescriptionProfile
from models.match_result import MatchResult
from services.llm_service import call_llm
from utils.parser import extract_json_from_llm
import json

def skill_matches_jd(item_name: str, jd_items: list) -> bool:
    item_lower = item_name.lower().strip()
    if not item_lower:
        return False
        
    synonyms = {
        "ml": ["machine learning"],
        "machine learning": ["ml"],
        "ai": ["artificial intelligence"],
        "artificial intelligence": ["ai"],
    }
    
    variations = {item_lower}
    if item_lower in synonyms:
        variations.update(synonyms[item_lower])
        
    if "(" in item_lower and ")" in item_lower:
        parts = item_lower.replace(")", "").split("(")
        for p in parts:
            p_strip = p.strip()
            if p_strip:
                variations.add(p_strip)
                if p_strip in synonyms:
                    variations.update(synonyms[p_strip])
                    
    extended = set()
    for v in variations:
        if v.endswith("s"):
            extended.add(v[:-1])
        else:
            extended.add(v + "s")
        if "-" in v:
            extended.add(v.replace("-", " "))
            extended.add(v.replace("-", ""))
        if " " in v:
            extended.add(v.replace(" ", "-"))
            extended.add(v.replace(" ", ""))
    variations.update(extended)
    
    for jd_item in jd_items:
        jd_lower = jd_item.lower().strip()
        jd_variations = {jd_lower}
        if jd_lower in synonyms:
            jd_variations.update(synonyms[jd_lower])
        if "(" in jd_lower and ")" in jd_lower:
            parts = jd_lower.replace(")", "").split("(")
            for p in parts:
                p_strip = p.strip()
                if p_strip:
                    jd_variations.add(p_strip)
                    if p_strip in synonyms:
                        jd_variations.update(synonyms[p_strip])
                        
        jd_extended = set()
        for jv in jd_variations:
            if jv.endswith("s"):
                jd_extended.add(jv[:-1])
            else:
                jd_extended.add(jv + "s")
            if "-" in jv:
                jd_extended.add(jv.replace("-", " "))
                jd_extended.add(jv.replace("-", ""))
            if " " in jv:
                jd_extended.add(jv.replace(" ", "-"))
                jd_extended.add(jv.replace(" ", ""))
        jd_variations.update(jd_extended)
        
        if variations.intersection(jd_variations):
            return True
            
    return False

def calculate_overall_score(matched_skills: list, missing_skills: list, jd: JobDescriptionProfile, repo_profile: RepositoryProfile, matched_libraries: list, matched_frameworks: list, matched_tools: list, matched_keywords: list, matched_domain: str) -> float:
    # 1. Skill Match
    total_skills = len(matched_skills) + len(missing_skills)
    skill_score = len(matched_skills) / max(1, total_skills)
    
    # 2. Domain Match
    jd_domain = jd.domain.lower().strip()
    repo_domain = repo_profile.domain.lower().strip()
    
    domain_matched = False
    if jd_domain and repo_domain:
        if repo_domain in jd_domain or jd_domain in repo_domain:
            domain_matched = True
            
    if matched_domain:
        domain_matched = True
        
    domain_score = 1.0 if domain_matched else 0.5
    
    # 3. Technology Match
    jd_tech = jd.tools + jd.frameworks + jd.libraries
    repo_tech = matched_libraries + matched_frameworks + matched_tools
    
    has_tech_req = len(jd_tech) > 0
    tech_score = len(repo_tech) / len(jd_tech) if has_tech_req else 1.0
    
    # 4. Keyword Match
    has_keyword_req = len(jd.keywords) > 0
    keyword_score = len(matched_keywords) / len(jd.keywords) if has_keyword_req else 1.0
    
    # Weights definition - Prioritizing Domain Match first (40%), then Skills (30%), Tech (15%), Keywords (15%)
    weights = {
        "domain": 0.4,
        "skill": 0.3,
        "tech": 0.15 if has_tech_req else 0.0,
        "keyword": 0.15 if has_keyword_req else 0.0
    }
    
    total_weight = sum(weights.values())
    for k in weights:
        weights[k] /= total_weight
        
    overall = (
        domain_score * weights["domain"] +
        skill_score * weights["skill"] +
        tech_score * weights.get("tech", 0.0) +
        keyword_score * weights.get("keyword", 0.0)
    )
    
    return float(overall)

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
2. Do NOT make broad assumptions (e.g., using an LLM API does not mean they know ML algorithms from scratch). HOWEVER, you MUST recognize standard industry synonyms and specific implementations (e.g., building 'agents' or using 'Model Context Protocol' is direct evidence of 'Agentic AI systems'; using 'React' is evidence of 'Frontend Development').
3. Before finalizing the `missing_skills` array, you MUST verify if the skill or its direct synonyms are mentioned anywhere in the README snippet. Do NOT list a skill as missing if it exists in the README!

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
        jd_profile.required_skills
        + jd_profile.preferred_skills
        + jd_profile.programming_languages
        + jd_profile.technologies
        + jd_profile.tools
        + jd_profile.frameworks
        + jd_profile.libraries
        + jd_profile.methodologies
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
            
    # Filter final outputs to strictly match exact skills from the JD
    final_matched = [s for s in matched_skills if skill_matches_jd(s, all_jd_skills)]
    final_missing = [s for s in still_missing if skill_matches_jd(s, all_jd_skills)]
    
    # Ensure every single jd skill is in either final_matched or final_missing
    for jd_skill in all_jd_skills:
        is_matched = any(skill_matches_jd(jd_skill, [m]) for m in final_matched)
        is_missing = any(skill_matches_jd(jd_skill, [mis]) for mis in final_missing)
        if not is_matched and not is_missing:
            final_missing.append(jd_skill)
            
    # Filter lists of specific categories
    final_libraries = [l for l in parsed.get("matched_libraries", []) if skill_matches_jd(l, jd_profile.libraries)]
    final_frameworks = [f for f in parsed.get("matched_frameworks", []) if skill_matches_jd(f, jd_profile.frameworks)]
    final_tools = [t for t in parsed.get("matched_tools", []) if skill_matches_jd(t, jd_profile.tools)]
    final_keywords = [k for k in parsed.get("matched_keywords", []) if skill_matches_jd(k, jd_profile.keywords)]
    
    # Also filter the evidence dictionary keys
    final_evidence = {k: v for k, v in evidence.items() if skill_matches_jd(k, all_jd_skills)}
    
    # Calculate overall score programmatically for consistency
    overall_score = calculate_overall_score(
        final_matched, 
        final_missing, 
        jd_profile, 
        repo_profile, 
        final_libraries, 
        final_frameworks, 
        final_tools, 
        final_keywords, 
        str(parsed.get("matched_domain", ""))
    )
            
    return MatchResult(
        repository_name=repo_profile.name,
        overall_score=overall_score,
        matched_skills=final_matched,
        missing_skills=final_missing,
        matched_libraries=final_libraries,
        matched_frameworks=final_frameworks,
        matched_tools=final_tools,
        matched_domain=str(parsed.get("matched_domain", "")),
        matched_keywords=final_keywords,
        evidence=final_evidence,
        confidence=str(parsed.get("confidence", ""))
    )
