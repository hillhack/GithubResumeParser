# 🎯 GitHub Resume Parser

> **JD → GitHub → ATS Resume** — AI-powered resume generator that tailors your GitHub profile to any job description.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Groq](https://img.shields.io/badge/Groq-LLaMA_3.3_70B-F55036?style=flat)](https://groq.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🚀 What It Does

Most GitHub resume tools stop at "extract repositories." Recruiters actually care about:

```
Job Description  →  Candidate Evidence  →  Resume Tailored For That Role
```

This tool does exactly that — give it a GitHub username and job description, and it outputs a complete, ATS-friendly resume with ranked projects, skill gap analysis, and LaTeX source.

---

## ✨ Features

| Feature | Description |
|---|---|
| **GitHub Extraction** | Profile, repos, READMEs, languages, stars, topics |
| **JD Analysis** | Extracts required skills, domain, experience level via LLM |
| **Repo Ranking** | Two modes — JD Relevance (LLM-scored) or Popularity (stars/forks) |
| **Resume Generation** | Tailored bullets, professional summary, grouped skills section |
| **Skill Gap Analysis** | Shows exactly what the JD needs vs what your GitHub proves |
| **Project Reordering** | Drag-and-drop style ▲▼ controls — you control final order |
| **LaTeX Export** | 3 templates: ATS Classic, Modern, Research |
| **Markdown Export** | Clean `.md` resume for GitHub/portfolio use |

---

## 🏗️ Architecture

```
Streamlit UI (client.py)
        ↓
GitHub Extraction Agent  ←  github_extractor.py
        ↓
JD Analysis Agent        ←  jd_analyzer.py
        ↓
Repository Ranking Agent ←  repo_ranker.py
        ↓
Resume Generation Agent  ←  resume_generator.py
        ↓
LaTeX Rendering Agent    ←  latex_generator.py
```

---

## 📋 Prerequisites

- Python 3.10+
- [Groq API key](https://console.groq.com) (free tier works)
- GitHub Client ID + Secret (for higher rate limits — optional)

---

## ⚡ Quick Start

```bash
# 1. Clone
git clone https://github.com/hillhack/GithubResumeParser
cd GithubResumeParser

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 4. Run
streamlit run client.py
```

Open **http://localhost:8501** in your browser.

---

## 🔑 Environment Variables

Create a `.env` file in the project root:

```env
# Required
GROQ_API_KEY=gsk_...

# Optional — increases GitHub API rate limit from 60 to 5000 req/hr
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret

# Optional — override default model
# GROQ_MODEL=llama-3.3-70b-versatile
```

---

## 🖥️ User Flow

```
Enter GitHub Username
        ↓
Paste Job Description
        ↓
Choose Resume Style (1-page / 2-page, ATS / Modern / Research)
        ↓
Click 🚀 Generate Resume
        ↓
Review Ranked Projects  →  Reorder with ▲▼
        ↓
Export PDF (via LaTeX) / Markdown
```

---

## 📄 Output Tabs

### 📄 Resume Tab
- Full white-paper resume preview rendered in the browser
- Download as `.tex` (LaTeX) or `.md` (Markdown)

### 🏆 Projects Tab
- All repos scored and ranked against the JD
- Shows match %, matched skills, description, topics
- ▲ / ▼ buttons to reorder
- **Apply Order & Regenerate** to rebuild resume with your custom order

### 🎯 Skills Gap Tab
- **✅ Skills You Have** — JD required skills found in your GitHub
- **❌ Skills to Learn** — Required but not evidenced
- Full tech stack extracted from all your repos

### ⚙️ LaTeX Tab
- Full LaTeX source, syntax-highlighted
- Compile with `pdflatex resume.tex` or paste into [Overleaf](https://overleaf.com)

---

## 📁 Project Structure

```
GithubResumeParser/
├── client.py              # Streamlit UI (main entry point)
├── github_extractor.py    # GitHub REST API data extraction
├── jd_analyzer.py         # LLM-based job description parsing
├── repo_ranker.py         # JD relevance + popularity ranking
├── resume_generator.py    # Bullet points, summary, skills generation
├── latex_generator.py     # LaTeX templates (ATS, Modern, Research)
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variable template
└── README.md
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| LLM | Groq + LLaMA 3.3 70B |
| Data Source | GitHub REST API v3 |
| Resume Rendering | LaTeX (pdflatex / Overleaf) |
| Language | Python 3.10+ |

---

## 🗺️ Roadmap

- [ ] PDF compilation via `pdflatex` subprocess
- [ ] PostgreSQL persistence (users, resumes, history)
- [ ] LinkedIn profile import
- [ ] Cover letter generation
- [ ] Resume scoring against JD (0–100)
- [ ] Interview question generation
- [ ] LeetCode + Kaggle profile import
- [ ] Multi-agent evaluation layer

---

## 📝 License

MIT — see [LICENSE](LICENSE).
