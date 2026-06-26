import os
from dotenv import load_dotenv
load_dotenv()

GITHUB_API_URL = "https://api.github.com"
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".alldone_cache")

# Important repository files for deterministic extraction
IMPORTANT_FILES = [
    "README.md",
    "requirements.txt",
    "package.json",
    "pyproject.toml",
    "Cargo.toml",
    "pom.xml",
    "build.gradle",
    "Dockerfile",
    "docker-compose.yml",
    "Makefile",
    "environment.yml",
    "setup.py",
    "composer.json",
    "Gemfile",
    "pubspec.yaml",
    "go.mod",
    "package-lock.json",
    ".github/workflows",
    "app.py",
    "main.py",
    "server.py",
    "index.js",
    "index.ts"
]
