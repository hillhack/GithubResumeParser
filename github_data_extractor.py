"""
Minimal GitHub Data Extractor
Extracts user data from GitHub API for resume building
"""

import os
import requests
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET')


def get_user_data(username):
    """Fetch basic user data from GitHub"""
    url = f"https://api.github.com/users/{username}"
    response = requests.get(url, auth=(GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET))
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching user data: {response.status_code}")
        return None


def get_user_repos(username):
    """Fetch all repositories for a user"""
    url = f"https://api.github.com/users/{username}/repos"
    params = {'per_page': 100, 'sort': 'updated'}
    response = requests.get(url, params=params, auth=(GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET))
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching repos: {response.status_code}")
        return []


def get_languages_from_repos(repos):
    """Extract languages used across all repos"""
    languages = {}
    
    for repo in repos:
        lang_url = repo.get('languages_url')
        if lang_url:
            response = requests.get(lang_url, auth=(GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET))
            if response.status_code == 200:
                repo_languages = response.json()
                for lang, bytes_count in repo_languages.items():
                    languages[lang] = languages.get(lang, 0) + bytes_count
    
    return languages


def extract_github_data(username):
    """Main function to extract all GitHub data"""
    print(f"Extracting data for GitHub user: {username}")
    
    # Get user profile
    user_data = get_user_data(username)
    if not user_data:
        return None
    
    # Get repositories
    repos = get_user_repos(username)
    
    # Get languages
    languages = get_languages_from_repos(repos)
    
    # Compile data
    extracted_data = {
        'profile': {
            'name': user_data.get('name'),
            'username': user_data.get('login'),
            'bio': user_data.get('bio'),
            'location': user_data.get('location'),
            'email': user_data.get('email'),
            'blog': user_data.get('blog'),
            'company': user_data.get('company'),
            'followers': user_data.get('followers'),
            'following': user_data.get('following'),
            'public_repos': user_data.get('public_repos'),
            'avatar_url': user_data.get('avatar_url'),
            'created_at': user_data.get('created_at'),
        },
        'repositories': [
            {
                'name': repo.get('name'),
                'description': repo.get('description'),
                'stars': repo.get('stargazers_count'),
                'forks': repo.get('forks_count'),
                'language': repo.get('language'),
                'url': repo.get('html_url'),
                'created_at': repo.get('created_at'),
                'updated_at': repo.get('updated_at'),
                'is_fork': repo.get('fork', False),
            }
            for repo in repos
        ],
        'languages': languages,
        'stats': {
            'total_repos': len(repos),
            'total_stars': sum(repo.get('stargazers_count', 0) for repo in repos),
            'total_forks': sum(repo.get('forks_count', 0) for repo in repos),
        }
    }
    
    return extracted_data


def save_data(data, filename='github_data.json'):
    """Save extracted data to JSON file"""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Data saved to {filename}")


if __name__ == "__main__":
    # Get username from user
    username = input("Enter GitHub username: ").strip()
    
    # Extract data
    data = extract_github_data(username)
    
    if data:
        # Save to file
        save_data(data)
        print("\n✅ Data extraction complete!")
        print(f"Profile: {data['profile']['name']} (@{data['profile']['username']})")
        print(f"Repos: {data['stats']['total_repos']}")
        print(f"Stars: {data['stats']['total_stars']}")
        print(f"Languages: {', '.join(list(data['languages'].keys())[:5])}")
    else:
        print("❌ Failed to extract data")
