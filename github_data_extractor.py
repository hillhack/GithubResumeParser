from mcp.server.fastmcp import FastMCP
import requests

# MCP SERVER

mcp = FastMCP("GitHubSkill")

# TOOLS

@mcp.tool()
def get_github_profile(username: str):
    """
    Get basic GitHub profile information.
    """

    url = f"https://api.github.com/users/{username}"
    data = requests.get(url).json()

    return {
        "name": data.get("name"),
        "username": data.get("login"),
        "followers": data.get("followers"),
        "public_repos": data.get("public_repos"),
        "location": data.get("location"),
    }


@mcp.tool()
def get_repo_count(username: str):
    """
    Get number of public repositories.
    """

    url = f"https://api.github.com/users/{username}"
    data = requests.get(url).json()

    return {
        "username": username,
        "public_repos": data.get("public_repos")
    }


@mcp.tool()
def list_repositories(username: str):
    """
    Return repository names.
    """

    repos = requests.get(
        f"https://api.github.com/users/{username}/repos"
    ).json()

    return [
        repo["name"]
        for repo in repos
        if "name" in repo
    ]


@mcp.tool()
def extract_languages(username: str):
    """
    Count language usage across repositories.
    """

    repos = requests.get(
        f"https://api.github.com/users/{username}/repos"
    ).json()

    languages = {}

    for repo in repos:

        language = repo.get("language")

        if language:
            languages[language] = (
                languages.get(language, 0) + 1
            )

    return languages

# RESOURCES

@mcp.resource("github://profile/{username}")
def github_profile_resource(username: str):

    url = f"https://api.github.com/users/{username}"
    data = requests.get(url).json()

    return f"""
Name: {data.get("name")}
Username: {data.get("login")}
Followers: {data.get("followers")}
Repositories: {data.get("public_repos")}
Location: {data.get("location")}
"""


@mcp.resource("github://repos/{username}")
def github_repos_resource(username: str):

    repos = requests.get(
        f"https://api.github.com/users/{username}/repos"
    ).json()

    repo_names = []

    for repo in repos:
        if "name" in repo:
            repo_names.append(repo["name"])

    return "\n".join(repo_names)

# PROMPTS

@mcp.prompt()
def github_profile_analysis(username: str):

    return f"""
Analyze the GitHub profile of {username}.

Focus on:

1. Programming skills
2. Repository quality
3. Experience level
4. Open source activity
5. Career recommendations

Generate a concise report.
"""


@mcp.prompt()
def github_resume_prompt(username: str):

    return f"""
Generate professional resume bullet points
for GitHub user {username}.

Focus on:

- Technical skills
- Projects
- Contributions
- Impact
- Leadership

Return ATS-friendly bullet points.
"""


# BUILDING A PRACTICAL MCP SKILL
# Instead of calling tools individually,
# we combine them into a higher-level skill.
#
# get_github_profile()
# get_repo_count()
# list_repositories()
# extract_languages()
#
# extract_github_data()

@mcp.tool()
def extract_github_data(username: str):
    """
    Combine multiple GitHub tools into a
    single structured developer profile.
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


# LOCAL TESTING

if __name__ == "__main__":

    USERNAME = "hillhack"


    result = extract_github_data(USERNAME)

    print(result)

    print("\nStarting MCP Server...")

    mcp.run()