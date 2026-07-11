import os
import json
import re
from typing import Dict, List

from extractor import extract_skills, parse_llm_json
from github_api import enrich_repo, fetch_user_contributions
from llm_providers import gemini_key_ctx, hf_token_ctx, groq_key_ctx

def extract_jd_skills_tool(jd_text: str, provider: str = "Groq", model: str = "llama-3.3-70b-versatile") -> Dict:
    """
    Extracts atomic technical skills, domains, and tools from a Job Description text.
    Returns a structured JSON dictionary of categorized skills.
    """
    token_set, _ = _set_ctx(provider)
    try:
        parsed_data, _raw_text = extract_skills(jd_text, provider=provider, model=model)
        return parsed_data
    finally:
        _reset_ctx(token_set, provider)


# ─── Hybrid Repo Analyser ────────────────────────────────────────────────────

README_PROMPT = """Analyze each repository using a two-stage pipeline.

Stage 1 (Deterministic Analysis) has already been performed. We have extracted the languages, dependencies, and verifiable metadata.

Stage 2: LLM Analysis
* Use the extracted metadata, repository contents, README, and relevant source files to infer the project's purpose, architecture, key features, and technical implementation.
* Analyze the repository in the context of the provided Job Description (JD), identifying the skills, technologies, and experiences that best align with the role.
* Extract only the information that is relevant to the JD, rather than producing a generic project summary.

=== Repository: {repo_name} ===
Deterministic Metadata (Languages, Dependencies, Topics):
{deterministic_data}

README:
{readme}

=== JD Required Skills (for reference only) ===
{jd_skills}

Project Overview
Generate a structured overview containing ONLY your personal contributions (not forked or contributed code), formatted exactly as the following JSON object (no markdown, no extra text):
{{
  "project_title": "Project title",
  "objective": "Project objective",
  "domain": ["List of domain areas"],
  "skills": ["List of technical skills used in the project"],
  "tools": ["List of tools used"],
  "libraries": ["List of libraries/frameworks used"],
  "technologies": ["List of programming languages or core technologies"],
  "key_features": ["Key features and implementation details"],
  "demonstrated": ["Relevant skills and experiences that match the JD"],
  "relevance": "A concise explanation of why the project is relevant to the target role",
  "highlights": ["References to the most relevant code files, functions, classes, or code snippets that support these conclusions so the user can verify the extracted information"],
  "missing_skills": ["JD skills with no concrete evidence in the README"],
  "llm_score": <integer 0-100 score of alignment with JD>
}}
"""



def _call_llm(provider: str, model: str, prompt: str) -> str:
    """Route an LLM call through the appropriate provider with automatic rate limit retries."""
    import time
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            if provider == "Groq":
                from llm_providers import get_groq_response
                return get_groq_response(model, prompt)
            elif provider == "Gemini":
                from llm_providers import get_gemini_response
                return get_gemini_response(model, prompt)
            else:
                from llm_providers import get_huggingface_response
                return get_huggingface_response(model, prompt)
                
        except Exception as e:
            err_msg = str(e).lower()
            if attempt < max_retries - 1 and ("429" in err_msg or "quota" in err_msg or "rate limit" in err_msg or "resource exhausted" in err_msg):
                sleep_time = (attempt + 1) * 8  # 8s, 16s, 24s
                print(f"Rate limit hit on {provider}. Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
                continue
            raise


def _set_ctx(provider: str):
    """Set the correct contextvar from env and return the token."""
    if provider == "Groq":
        key = os.environ.get("GROQ_API_KEY")
        if not key: raise ValueError("GROQ_API_KEY not found.")
        return groq_key_ctx.set(key), provider
    elif provider == "Gemini":
        key = os.environ.get("GEMINI_API_KEY")
        if not key: raise ValueError("GEMINI_API_KEY not found.")
        return gemini_key_ctx.set(key), provider
    elif provider == "HuggingFace":
        key = os.environ.get("HF_TOKEN")
        if not key: raise ValueError("HF_TOKEN not found.")
        return hf_token_ctx.set(key), provider
    raise ValueError(f"Unknown provider: {provider}")


def _reset_ctx(token_set, provider: str):
    if token_set is None: return
    if provider == "Groq":       groq_key_ctx.reset(token_set)
    elif provider == "Gemini":   gemini_key_ctx.reset(token_set)
    elif provider == "HuggingFace": hf_token_ctx.reset(token_set)


def _normalize(s: str) -> str:
    """Normalize a skill string for fuzzy comparison."""
    s = s.lower().strip()
    # Remove trailing plurals: 'apis' -> 'api', 'libraries' -> 'librar', etc.
    # Simple: strip trailing 's' only if word is longer than 4 chars
    s = re.sub(r'\s+', ' ', s)           # collapse whitespace
    s = s.replace('-', ' ')              # rest-api -> rest api
    s = s.rstrip('s') if len(s) > 4 else s   # 'apis' -> 'api'
    return s


def _is_skill_match(skill_norm: str, candidate_tokens: set) -> bool:
    """
    Fuzzy skill matching with normalization:
    - Normalize both sides (lowercase, collapse spaces, strip trailing plural s)
    - Exact match always allowed.
    - Substring match only when both sides are >= 4 chars.
    """
    sn = _normalize(skill_norm)
    for tok in candidate_tokens:
        tn = _normalize(tok)
        if sn == tn:
            return True
        if len(sn) >= 4 and len(tn) >= 4:
            if sn in tn or tn in sn:
                return True
    return False


def _deterministic_score(enriched: dict, jd_skills_lower: set) -> dict:
    """
    Ground-truth-first scoring: start from what the repo ACTUALLY HAS
    (languages, dependencies, topics), then check which of those happen
    to appear in the JD — not the other way around.

    Returns:
        dict with det_score (0-100), matched_skills, missing_skills, evidence list.
    """
    # ── Step 1: Build a map of repo's real tokens → their display label ────────
    # token (lowercase) → canonical display name
    repo_tokens: dict[str, str] = {}

    for lang in enriched.get("languages", {}).keys():
        repo_tokens[lang.lower()] = lang  # e.g. "python" → "Python"

    for topic in enriched.get("topics", []):
        repo_tokens[topic.lower().replace("-", " ")] = topic
        repo_tokens[topic.lower()] = topic

    for dep in enriched.get("dependencies", []):
        repo_tokens[dep.lower()] = dep  # e.g. "streamlit" → "streamlit"

    # ── Step 2: Find which repo tokens match any JD skill ──────────────────────
    # For each real token in the repo, check if the JD asks for it.
    matched: List[str] = []
    matched_lower: set = set()

    for token, display in repo_tokens.items():
        for jd_skill in jd_skills_lower:
            # Use same strict matching logic (no short-token substring games)
            if _is_skill_match(token, {jd_skill}):
                if jd_skill not in matched_lower:
                    matched_lower.add(jd_skill)
                    # Display the JD's canonical name for the skill
                    matched.append(jd_skill)
                break

    # ── Step 3: Everything in the JD not found in the repo is missing ──────────
    missing = [s for s in jd_skills_lower if s not in matched_lower]

    # ── Step 4: Build evidence bullets from real repo data ────────────────────
    evidence: List[str] = []
    lang_list = list(enriched.get("languages", {}).keys())
    if lang_list:
        evidence.append(f"Languages in repo: {', '.join(lang_list)}")
    deps = enriched.get("dependencies", [])
    if deps:
        evidence.append(f"Packages found: {', '.join(deps[:15])}{'...' if len(deps) > 15 else ''}")
    if enriched.get("topics"):
        evidence.append(f"GitHub topics: {', '.join(enriched['topics'])}")

    # Score = what fraction of the JD skills are genuinely covered
    total_skills = len(jd_skills_lower) or 1
    det_score = min(100, int((len(matched) / total_skills) * 100))

    return {
        "det_score":      det_score,
        "matched_skills": matched,
        "missing_skills": missing,
        "evidence":       evidence,
    }



def analyse_repos_tool(
    repos: list,
    jd_data: dict,
    github_username: str,
    provider: str = "Groq",
    model: str = "llama-3.3-70b-versatile",
) -> list:
    """
    Hybrid two-pass repo analyser.

    Pass 1 (Deterministic): Fetch languages, topics, dependency files from GitHub.
                            Compute keyword overlap score against JD skills.
    Pass 2 (LLM):          Fetch README. Ask LLM to score semantic relevance and
                            generate highlights.
    Final Score = 0.6 x det_score + 0.4 x llm_score

    Args:
        repos:            Selected repo dicts (name, url, description).
        jd_data:          Extracted JD skills dict.
        github_username:  GitHub username (needed for enrichment API calls).
        provider:         LLM provider.
        model:            Model name.

    Returns:
        List of result dicts sorted by final_score descending.
    """
    # Flatten all JD skill lists for matching
    skill_keys = ["skills", "tools", "libraries", "technologies", "domain_knowledge", "nice_to_have", "programming_languages", "technical_skills", "tools_and_technologies"]
    all_skills = []
    for key in skill_keys:
        all_skills.extend(jd_data.get(key, []))

    jd_skills_lower = {s.lower() for s in all_skills if isinstance(s, str)}
    results = []

    from concurrent.futures import ThreadPoolExecutor, as_completed

    # Capture the key NOW in the main thread so workers can read it
    _env_key_map = {
        "Groq":        ("GROQ_API_KEY",   os.environ.get("GROQ_API_KEY", "")),
        "Gemini":      ("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", "")),
        "HuggingFace": ("HF_TOKEN",       os.environ.get("HF_TOKEN", "")),
    }

    def _analyse_single_repo(repo: dict) -> dict:
        # Each thread sets the env var + ctx so the LLM provider finds the key
        env_var, env_val = _env_key_map.get(provider, (None, None))
        if env_var and env_val:
            os.environ[env_var] = env_val
        _set_ctx(provider)

        repo_name = repo["name"]

        # Pass 1: Deterministic (cached, fast)
        enriched = enrich_repo(github_username, repo_name)
        det_data = _deterministic_score(enriched, jd_skills_lower)
        det_score = det_data["det_score"]
        matched_skills = det_data["matched_skills"]
        evidence = det_data["evidence"]

        # Pass 2: LLM
        readme = enriched.get("readme_text", "")
        deterministic_data = json.dumps({
            "languages": list(enriched.get("languages", {}).keys()),
            "dependencies": enriched.get("dependencies", []),
            "topics": enriched.get("topics", [])
        })
        prompt = README_PROMPT.format(
            jd_skills=", ".join(all_skills),
            repo_name=repo_name,
            readme=readme[:5000],
            deterministic_data=deterministic_data
        )

        llm_score = 0
        highlights = []
        llm_missing: List[str] = []
        llm_demonstrated: List[str] = []
        project_title = repo_name
        objective = ""
        domain = []
        skills = []
        tools_list = []
        libraries = []
        technologies = []
        key_features = []
        relevance = ""
        llm_error = None

        try:
            raw = _call_llm(provider, model, prompt)
            llm_data = parse_llm_json(raw)
            llm_score = int(llm_data.get("llm_score", 0))
            highlights = llm_data.get("highlights", [])
            llm_missing = llm_data.get("missing_skills", [])
            llm_demonstrated = llm_data.get("demonstrated", [])
            project_title = llm_data.get("project_title", repo_name)
            objective = llm_data.get("objective", "")
            domain = llm_data.get("domain", [])
            skills = llm_data.get("skills", [])
            tools_list = llm_data.get("tools", [])
            libraries = llm_data.get("libraries", [])
            technologies = llm_data.get("technologies", [])
            key_features = llm_data.get("key_features", [])
            relevance = llm_data.get("relevance", "")
        except Exception as e:
            llm_error = str(e)

        # Final score: 40% deterministic + 60% LLM
        final_score = int(0.4 * det_score + 0.6 * llm_score)

        # Build final matched skills
        llm_demo_lower = {s.lower() for s in llm_demonstrated}
        final_matched_lower: set = set()
        final_matched: List[str] = []
        for skill in matched_skills:
            k = skill.lower()
            if k not in final_matched_lower:
                final_matched_lower.add(k)
                final_matched.append(skill)

        # Anti-hallucination: LLM-claimed skills must appear verbatim in repo text
        _all_repo_text = (readme + " " + " ".join(
            list(enriched.get("languages", {}).keys()) +
            enriched.get("dependencies", []) +
            enriched.get("topics", [])
        )).lower()

        for skill in llm_demonstrated:
            k = skill.lower().strip()
            if k not in final_matched_lower:
                pattern = r'\b' + re.escape(k) + r'\b'
                if re.search(pattern, _all_repo_text):
                    final_matched_lower.add(k)
                    final_matched.append(skill)

        # Build final missing skills
        merged_missing_lower: set = set()
        merged_missing: List[str] = []
        for skill in llm_missing:
            k = skill.lower()
            if k in llm_demo_lower or k in final_matched_lower:
                continue
            if k not in merged_missing_lower:
                merged_missing_lower.add(k)
                merged_missing.append(skill)

        return {
            "name":           repo_name,
            "url":            repo.get("url", ""),
            "match_score":    final_score,
            "matched_skills": final_matched,
            "missing_skills": merged_missing,
            "highlights":     highlights if highlights else evidence,
            "project_title":  project_title,
            "objective":      objective,
            "domain":         domain,
            "skills":         skills,
            "tools":          tools_list,
            "libraries":      libraries,
            "technologies":   technologies,
            "key_features":   key_features,
            "relevance":      relevance,
            "llm_error":      llm_error,
        }

    # Analyse all repos sequentially to prevent LLM rate limits on free-tier keys
    with ThreadPoolExecutor(max_workers=1) as ex:
        futures = {ex.submit(_analyse_single_repo, repo): repo for repo in repos}
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                repo = futures[future]
                results.append({"name": repo["name"], "url": repo.get("url", ""),
                                "match_score": 0, "matched_skills": [], "missing_skills": [],
                                "highlights": [], "llm_error": str(e)})

    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results



# ─── Resume Generator ─────────────────────────────────────────────────────────

RESUME_PROMPT = """You are an expert ATS Resume Writer.
You are writing a resume for a candidate based strictly on their actual GitHub work.

Candidate GitHub Username: {username}

=== VERIFIED SKILLS (the ONLY skills you may include in the resume) ===
These have been deterministically confirmed to exist in the candidate's repositories.
Do NOT add any other skill — not from the JD, not from your training data.
{verified_skills}

=== Projects with Evidence ===
{projects_context}

=== Open-Source / Forked Contributions ===
{contributions_context}

=== Custom Instructions ===
{instructions}

STRICT RULES:
1. The skills_section must contain ONLY skills from the "VERIFIED SKILLS" list above. Do not add R, SQL, AWS, or any other skill not in that list.
2. Categorize the verified skills sensibly (Languages / Frameworks / Tools / Other).
3. Write a professional 2-3 sentence summary based on what the candidate ACTUALLY built.
4. For each project, rewrite the bullets to align with the target JD while remaining faithful to the cached project metadata. Emphasize the technologies, skills, and experiences most relevant to the job without inventing or exaggerating any information. Use the following format for bullets:
   - Bullet point describing the user's first major contribution.
   - Bullet point describing the second contribution.
   - Bullet point highlighting technical implementation, optimizations, or measurable impact.
5. Output ONLY valid JSON matching the schema below.

Output ONLY this JSON (no markdown, no extra text):
{{
  "profile": {{
    "name": "{username}",
    "username": "{username}",
    "email": "",
    "github_url": "https://github.com/{username}",
    "linkedin_url": "",
    "website": "",
    "location": "",
    "organizations": []
  }},
  "summary": "...",
  "skills_section": {{
    "Languages": ["only from verified list"],
    "Frameworks": ["only from verified list"],
    "Tools": ["only from verified list"]
  }},
  "projects": [
    {{
      "name": "ProjectName",
      "url": "https://github.com/{username}/ProjectName",
      "tech_stack": ["only real tech from this project"],
      "one_liner": "One sentence describing what this project does",
      "bullets": ["Bullet 1", "Bullet 2"]
    }}
  ],
  "contributions": [
    {{
      "repo": "RepoName",
      "url": "https://github.com/...",
      "summary": "Short description of the contribution"
    }}
  ]
}}
"""

def generate_resume_tool(
    github_username: str, 
    match_results: list, 
    jd_data: dict, 
    instructions: str = "",
    provider: str = "Groq", 
    model: str = "llama-3.3-70b-versatile",
    forked_repos: list = None
) -> dict:
    # ── Collect ALL genuinely verified skills across all top repos ──
    verified_skills_set: set = set()
    for r in match_results:
        # Include JD-matched skills...
        for skill in r.get("matched_skills", []):
            verified_skills_set.add(skill.strip())
        # ...AND all other skills the LLM extracted from the repo evidence
        for key in ["skills", "tools", "libraries", "technologies"]:
            for item in r.get(key, []):
                verified_skills_set.add(item.strip())
    
    verified_skills_list = sorted(verified_skills_set)

    # Build projects context from evidence highlights
    projects_context = ""
    for r in match_results:
        projects_context += (
            f"\nProject Name: {r.get('project_title', r['name'])} ({r['name']})"
            f"\nURL: {r.get('url', '')}"
            f"\nObjective: {r.get('objective', '')}"
            f"\nDomain: {r.get('domain', [])}"
            f"\nSkills: {r.get('skills', [])}"
            f"\nTools: {r.get('tools', [])}"
            f"\nLibraries: {r.get('libraries', [])}"
            f"\nTechnologies: {r.get('technologies', [])}"
            f"\nKey Features: {r.get('key_features', [])}"
            f"\nRelevance to JD: {r.get('relevance', '')}"
            f"\nVerified Matched Skills: {r.get('matched_skills', [])}"
            f"\nCode Highlights/Contributions: {r.get('highlights', [])}"
            f"\n"
        )
        
    contrib_context = ""
    if forked_repos:
        for fr in forked_repos[:5]: # limit to top 5
            contrib_context += f"- Repo: {fr.get('name')}, Desc: {fr.get('description', '')}, URL: {fr.get('url', '')}\n"
    else:
        contrib_context = "No open-source contributions to highlight."

    prompt = RESUME_PROMPT.format(
        username=github_username,
        verified_skills=", ".join(verified_skills_list) if verified_skills_list else "None verified — use only what is explicitly mentioned in the project highlights.",
        projects_context=projects_context,
        contributions_context=contrib_context,
        instructions=instructions or "Write an honest, evidence-based resume."
    )
    
    token_set = None
    try:
        token_set, _ = _set_ctx(provider)
        raw = _call_llm(provider, model, prompt)
        result = parse_llm_json(raw)

        # ── Post-filter: strip any skill the LLM hallucinated ──────────────
        # Even if the LLM ignores the prompt, enforce the verified set here.
        if verified_skills_set:
            verified_lower = {s.lower() for s in verified_skills_set}
            skills_section = result.get("skills_section", {})
            filtered_skills: dict = {}
            for cat, items in skills_section.items():
                kept = [s for s in items if s.lower() in verified_lower]
                if kept:
                    filtered_skills[cat] = kept
            result["skills_section"] = filtered_skills

        # ── Inject REAL contributions via GitHub API ────────────────────
        real_contribs = []
        for c in fetch_user_contributions(github_username)[:10]:
            real_contribs.append({
                "repo":    c.get("repo", ""),
                "url":     c.get("pr_url") or c.get("repo_url", ""),
                "type":    c.get("type", ""),
                "title":   c.get("title", ""),
                "summary": f"{c.get('type', '')}: {c.get('title', '')[:100]}"
            })
        result["contributions"] = real_contribs

        return result
    except Exception as e:
        raise ValueError(f"Resume generation failed: {str(e)}")
    finally:
        _reset_ctx(token_set, provider)
