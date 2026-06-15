#!/usr/bin/env python3

import os
import json
import re
import requests

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# ENVIRONMENT VARIABLES

load_dotenv()

GITHUB_AUTH = (
    os.getenv("GITHUB_CLIENT_ID"),
    os.getenv("GITHUB_CLIENT_SECRET")
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# MCP SERVER

mcp = FastMCP("GitHubResumeParser")

# TOOL 1

@mcp.tool()
def get_github_profile(username: str):
    """
    Get basic GitHub profile information.
    """

    url = f"https://api.github.com/users/{username}"

    data = requests.get(
        url,
        auth=GITHUB_AUTH
    ).json()

    return {
        "name": data.get("name"),
        "username": data.get("login"),
        "bio": data.get("bio"),
        "followers": data.get("followers"),
        "following": data.get("following"),
        "public_repos": data.get("public_repos"),
        "location": data.get("location"),
    }


# TOOL 2

@mcp.tool()
def get_repo_count(username: str):
    """
    Return repository count.
    """

    url = f"https://api.github.com/users/{username}"

    data = requests.get(
        url,
        auth=GITHUB_AUTH
    ).json()

    return {
        "username": username,
        "public_repos": data.get("public_repos", 0)
    }


# TOOL 3

@mcp.tool()
def list_repositories(username: str):
    """
    Return repository names.
    """

    repos = requests.get(
        f"https://api.github.com/users/{username}/repos",
        auth=GITHUB_AUTH
    ).json()

    return [
        repo["name"]
        for repo in repos
        if "name" in repo
    ]


# TOOL 4

@mcp.tool()
def extract_languages(username: str):
    """
    Count language usage across repositories.
    """

    repos = requests.get(
        f"https://api.github.com/users/{username}/repos",
        auth=GITHUB_AUTH
    ).json()

    languages = {}

    for repo in repos:

        language = repo.get("language")

        if language:

            languages[language] = (
                languages.get(language, 0) + 1
            )

    return languages


# TOOL COMPOSITION

@mcp.tool()
def extract_github_data(username: str):
    """
    Combine multiple tools into one skill.
    """

    profile = get_github_profile(username)

    repo_count = get_repo_count(username)

    repositories = list_repositories(username)

    languages = extract_languages(username)

    return {
        "profile": profile,
        "repo_count": repo_count,
        "repositories": repositories,
        "languages": languages
    }

# RESOURCES

@mcp.resource("github://profile/{username}")
def github_profile_resource(username: str):
    """
    Resource containing GitHub profile information.
    """

    data = requests.get(
        f"https://api.github.com/users/{username}",
        auth=GITHUB_AUTH
    ).json()

    return f"""
Name: {data.get("name")}
Username: {data.get("login")}
Followers: {data.get("followers")}
Repositories: {data.get("public_repos")}
Location: {data.get("location")}
"""


@mcp.resource("github://repos/{username}")
def github_repos_resource(username: str):
    """
    Resource containing repository names.
    """

    repos = requests.get(
        f"https://api.github.com/users/{username}/repos",
        auth=GITHUB_AUTH
    ).json()

    repo_names = []

    for repo in repos:

        if "name" in repo:
            repo_names.append(repo["name"])

    return "\n".join(repo_names)


# PROMPTS

@mcp.prompt()
def github_profile_analysis(username: str):
    """
    Prompt template for profile analysis.
    """

    return f"""
Analyze the GitHub profile of {username}.

Focus on:

1. Programming Skills
2. Repository Quality
3. Experience Level
4. Open Source Activity
5. Career Recommendations

Generate a concise report.
"""


@mcp.prompt()
def github_resume_prompt(username: str):
    """
    Prompt template for resume generation.
    """

    return f"""
Generate professional resume bullet points
for GitHub user {username}.

Focus on:

- Technical Skills
- Projects
- Contributions
- Impact
- Leadership

Return ATS-friendly bullet points.
"""

# DATA AGGREGATION

# Instead of only collecting repository names,
# we now collect detailed repository information.
#
# This data will later be used by an LLM.
#
# ==========================================================

def get_github_raw(username: str):
    """
    Collect profile information,
    detailed repositories,
    and language statistics.
    """

    # --------------------------
    # Profile
    # --------------------------

    user = requests.get(
        f"https://api.github.com/users/{username}",
        auth=GITHUB_AUTH
    ).json()

    # --------------------------
    # Repositories
    # --------------------------

    repos_data = requests.get(
        f"https://api.github.com/users/{username}/repos",
        params={
            "per_page": 100,
            "sort": "updated"
        },
        auth=GITHUB_AUTH
    ).json()

    detailed_repositories = []

    languages = {}

    for repo in repos_data:

        if not isinstance(repo, dict):
            continue

        # Store repository details

        detailed_repositories.append({

            "name":
                repo.get("name"),

            "description":
                repo.get("description"),

            "stars":
                repo.get("stargazers_count", 0),

            "language":
                repo.get("language"),

            "url":
                repo.get("html_url"),

            "is_fork":
                repo.get("fork", False)
        })

        # ----------------------
        # Language Breakdown
        # ----------------------

        lang_url = repo.get("languages_url")

        if lang_url:

            try:

                repo_languages = requests.get(
                    lang_url,
                    auth=GITHUB_AUTH
                ).json()

                for language, count in repo_languages.items():

                    languages[language] = (
                        languages.get(language, 0)
                        + count
                    )

            except Exception:
                pass

    # --------------------------
    # Final Structured Output
    # --------------------------

    return {

        "profile": {

            "name":
                user.get("name"),

            "username":
                user.get("login"),

            "bio":
                user.get("bio"),

            "followers":
                user.get("followers"),

            "public_repos":
                user.get("public_repos"),

            "location":
                user.get("location")
        },

        "repositories":
            detailed_repositories,

        "languages":
            languages
    }
# GROQ INTEGRATION
#
# Goal:
#
# GitHub Data
#      ↓
# Groq Llama 3.3
#      ↓
# Repo Ranking
#      ↓
# Resume Bullet Points
#
# ==========================================================

def ai_rank_repos(
    repositories,
    job_description,
    groq_client
):
    """
    Use Groq Llama to rank repositories
    against a job description.
    """

    if not groq_client:

        return [
            {
                **repo,
                "relevance_score": None,
                "ai_summary": None,
                "resume_bullets": []
            }
            for repo in repositories
        ]

    # Analyze top repositories by stars

    repositories.sort(
        key=lambda x: x.get("stars", 0),
        reverse=True
    )

    top_repositories = repositories[:5]

    ranked_repositories = []

    for repo in top_repositories:

        prompt = f"""
Job Description:
{job_description}

Repository Name:
{repo.get("name")}

Description:
{repo.get("description")}

Primary Language:
{repo.get("language")}

Stars:
{repo.get("stars")}

Analyze the repository and return ONLY JSON:

{{
  "relevance_score": 0.0,
  "ai_summary": "",
  "resume_bullets": []
}}
"""

        try:

            response = (
                groq_client
                .chat
                .completions
                .create(

                    model="llama-3.3-70b-versatile",

                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],

                    temperature=0.2,

                    max_tokens=300
                )
            )

            raw_response = (
                response
                .choices[0]
                .message
                .content
                .strip()
            )

            json_response = re.sub(
                r'^```json\s*|\s*```$',
                '',
                raw_response,
                flags=re.IGNORECASE
            ).strip()

            parsed = json.loads(
                json_response
            )

        except Exception:

            parsed = {

                "relevance_score": 0,

                "ai_summary":
                    "Analysis Failed",

                "resume_bullets": []
            }

        ranked_repositories.append({

            **repo,

            "relevance_score":
                parsed.get(
                    "relevance_score",
                    0
                ),

            "ai_summary":
                parsed.get(
                    "ai_summary",
                    ""
                ),

            "resume_bullets":
                parsed.get(
                    "resume_bullets",
                    []
                )
        })

    ranked_repositories.sort(
        key=lambda x: x["relevance_score"],
        reverse=True
    )

    return ranked_repositories


# MAIN MCP TOOL
# GITHUB RESUME GENERATOR

@mcp.tool()
def generate_resume(
    github_username: str,
    job_description: str
):
    """
    Generate AI-powered resume insights
    from GitHub repositories.
    """

    # -----------------------------------
    # STEP 1
    # Collect GitHub Data
    # -----------------------------------

    raw_data = get_github_raw(
        github_username
    )

    # -----------------------------------
    # STEP 2
    # Create Groq Client
    # -----------------------------------

    groq_client = None

    if GROQ_API_KEY:

        from groq import Groq

        groq_client = Groq(
            api_key=GROQ_API_KEY
        )

    # -----------------------------------
    # STEP 3
    # Rank Repositories
    # -----------------------------------

    ranked_repositories = ai_rank_repos(

        raw_data["repositories"],

        job_description,

        groq_client
    )

    # -----------------------------------
    # STEP 4
    # Return Structured Resume Data
    # -----------------------------------

    return {

        "profile":
            raw_data["profile"],

        "languages":
            raw_data["languages"],

        "repositories_ranked":
            ranked_repositories,

        "note":
            "AI analysis powered by Groq Llama 3.3"
    }


# ==========================================================
# LOCAL TESTING
# ==========================================================

if __name__ == "__main__":

    print("=" * 60)
    print("GITHUB RESUME PARSER MCP")
    print("LECTURE 4")
    print("=" * 60)

    # Optional Local Test

    # Uncomment for testing

    result = generate_resume(
        github_username="hillhack",
        job_description="""
        Machine Learning Engineer
        Python
        RAG
        LLM
        Vector Databases
        """
    )

    print(
        json.dumps(
            result,
            indent=2
        )
    )

    print("\nStarting MCP Server...")

    mcp.run(
        transport="sse"
    )