"""technology_normalizer.py — Canonicalizes raw package/library names to standard display names.

Prevents duplicate counting (e.g. "torch", "pytorch", "PyTorch" all become "PyTorch").
"""

from typing import List

# Canonical name map: raw_name_lower → Display Name
NORMALIZATION_MAP: dict[str, str] = {
    # Python / ML
    "torch": "PyTorch",
    "pytorch": "PyTorch",
    "pytorch-lightning": "PyTorch Lightning",
    "lightning": "PyTorch Lightning",
    "tensorflow": "TensorFlow",
    "tensorflow-gpu": "TensorFlow",
    "tensorflow-cpu": "TensorFlow",
    "tf": "TensorFlow",
    "keras": "Keras",
    "sklearn": "scikit-learn",
    "scikit_learn": "scikit-learn",
    "scikit-learn": "scikit-learn",
    "opencv-python": "OpenCV",
    "opencv-python-headless": "OpenCV",
    "cv2": "OpenCV",
    "opencv": "OpenCV",
    "pillow": "Pillow",
    "pil": "Pillow",
    "numpy": "NumPy",
    "pandas": "Pandas",
    "scipy": "SciPy",
    "matplotlib": "Matplotlib",
    "seaborn": "Seaborn",
    "plotly": "Plotly",
    "transformers": "HuggingFace Transformers",
    "huggingface_hub": "HuggingFace Hub",
    "diffusers": "HuggingFace Diffusers",
    "datasets": "HuggingFace Datasets",
    "langchain": "LangChain",
    "langchain-core": "LangChain",
    "langchain-community": "LangChain",
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "google-generativeai": "Google Gemini",
    "groq": "Groq",
    "xgboost": "XGBoost",
    "lightgbm": "LightGBM",
    "catboost": "CatBoost",
    "nltk": "NLTK",
    "spacy": "spaCy",
    "gensim": "Gensim",

    # Web Frameworks
    "fastapi": "FastAPI",
    "flask": "Flask",
    "django": "Django",
    "tornado": "Tornado",
    "starlette": "Starlette",
    "sanic": "Sanic",
    "aiohttp": "aiohttp",
    "express": "Express.js",
    "expressjs": "Express.js",
    "next": "Next.js",
    "nextjs": "Next.js",
    "nuxt": "Nuxt.js",
    "nuxtjs": "Nuxt.js",
    "react": "React",
    "reactjs": "React",
    "vue": "Vue.js",
    "vuejs": "Vue.js",
    "angular": "Angular",
    "svelte": "Svelte",
    "fasthtml": "FastHTML",
    "streamlit": "Streamlit",
    "gradio": "Gradio",
    "dash": "Dash",

    # Databases
    "psycopg2": "PostgreSQL",
    "psycopg2-binary": "PostgreSQL",
    "asyncpg": "PostgreSQL",
    "sqlalchemy": "SQLAlchemy",
    "pymongo": "MongoDB",
    "motor": "MongoDB",
    "redis": "Redis",
    "redis-py": "Redis",
    "aioredis": "Redis",
    "elasticsearch": "Elasticsearch",
    "elasticsearch-py": "Elasticsearch",
    "pymysql": "MySQL",
    "mysql-connector-python": "MySQL",
    "sqlite3": "SQLite",
    "aiosqlite": "SQLite",
    "cassandra-driver": "Cassandra",
    "pinecone-client": "Pinecone",
    "chromadb": "ChromaDB",
    "weaviate-client": "Weaviate",
    "qdrant-client": "Qdrant",

    # Cloud / Infra
    "boto3": "AWS",
    "botocore": "AWS",
    "google-cloud": "GCP",
    "google-cloud-storage": "GCP Storage",
    "google-cloud-bigquery": "BigQuery",
    "azure-sdk": "Azure",
    "azure-storage-blob": "Azure Blob Storage",

    # DevOps / Tools
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "terraform": "Terraform",
    "ansible": "Ansible",
    "pydantic": "Pydantic",
    "celery": "Celery",
    "dramatiq": "Dramatiq",
    "rq": "Redis Queue",
    "httpx": "HTTPX",
    "requests": "Requests",
    "uvicorn": "Uvicorn",
    "gunicorn": "Gunicorn",
    "pytest": "pytest",
    "unittest": "unittest",
    "jest": "Jest",
    "mocha": "Mocha",
    "webpack": "Webpack",
    "vite": "Vite",
    "rollup": "Rollup",

    # Rust crates
    "tokio": "Tokio",
    "serde": "Serde",
    "actix-web": "Actix-web",
    "axum": "Axum",
    "rocket": "Rocket",
    "reqwest": "Reqwest",

    # Go modules
    "gin-gonic/gin": "Gin",
    "gorilla/mux": "Gorilla Mux",
    "gorm.io/gorm": "GORM",
    "cobra": "Cobra",
    "urfave/cli": "CLI",

    # Java / Maven
    "spring-boot": "Spring Boot",
    "spring-framework": "Spring",
    "hibernate": "Hibernate",
    "junit": "JUnit",
}


def normalize(tech: str) -> str:
    """Return the canonical display name for a raw technology string."""
    key = tech.lower().strip().replace("_", "-")
    return NORMALIZATION_MAP.get(key, tech.strip())


def normalize_list(techs: List[str]) -> List[str]:
    """Normalize a list of technology names, deduplicating by canonical name."""
    seen: dict[str, str] = {}  # canonical_lower → display_name
    for t in techs:
        if not t or not t.strip():
            continue
        canonical = normalize(t)
        key = canonical.lower()
        if key not in seen:
            seen[key] = canonical
    return list(seen.values())
