"""GitHub Data Extractor - Minimal"""
import os, json, requests
from dotenv import load_dotenv

load_dotenv()
GITHUB_AUTH = (os.getenv('GITHUB_CLIENT_ID'), os.getenv('GITHUB_CLIENT_SECRET'))

def extract_github_data(username):
    """Extract all GitHub data"""
    print(f"Extracting data for: {username}")
    
    # Get user profile
    user = requests.get(f"https://api.github.com/users/{username}", auth=GITHUB_AUTH).json()
    
    # Get repos
    repos = requests.get(f"https://api.github.com/users/{username}/repos", 
                        params={'per_page': 100, 'sort': 'updated'}, 
                        auth=GITHUB_AUTH).json()
    
    # Get languages
    languages = {}
    for repo in repos:
        if lang_url := repo.get('languages_url'):
            repo_langs = requests.get(lang_url, auth=GITHUB_AUTH).json()
            for lang, count in repo_langs.items():
                languages[lang] = languages.get(lang, 0) + count
    
    # Return data
    return {
        'profile': {
            'name': user.get('name'),
            'username': user.get('login'),
            'bio': user.get('bio'),
            'location': user.get('location'),
            'followers': user.get('followers'),
            'public_repos': user.get('public_repos'),
        },
        'repositories': [{
            'name': r.get('name'),
            'description': r.get('description'),
            'stars': r.get('stargazers_count'),
            'language': r.get('language'),
            'url': r.get('html_url'),
            'is_fork': r.get('fork', False),
        } for r in repos],
        'languages': languages,
    }

if __name__ == "__main__":
    username = input("Enter GitHub username: ").strip()
    data = extract_github_data(username)
    
    with open('github_data.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✅ Done! Extracted {len(data['repositories'])} repos")
    print(f"Languages: {', '.join(list(data['languages'].keys())[:5])}")
