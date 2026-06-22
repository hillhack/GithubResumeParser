# 🎯 GitHub Resume Parser

> **JD → GitHub → ATS Resume** — AI-powered resume generator that tailors your GitHub profile to any job description, using a full **Model Context Protocol (MCP)** multi-agent architecture.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Groq](https://img.shields.io/badge/Groq-LLaMA_3.3_70B-F55036?style=flat)](https://groq.com)
[![MCP](https://img.shields.io/badge/MCP-FastMCP-6366F1?style=flat)](https://github.com/jlowin/fastmcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🚀 What It Does

Most GitHub resume tools stop at "extract repositories." Recruiters actually care about:

```
Job Description  →  Candidate Evidence  →  Resume Tailored For That Role
```

This tool does exactly that — give it a GitHub username and a job description, and it outputs a complete, ATS-friendly resume with **LLM-scored project rankings**, skill gap analysis, and LaTeX/Markdown export.

---

## ✨ Features

| Feature | Description |
|---|---|
| **MCP Agent Architecture** | 4 FastMCP tools communicate over JSON-RPC — cleanly decoupled |
| **GitHub Extraction** | Profile, repos, READMEs, languages, stars, topics via GitHub REST API |
| **JD Analysis** | Extracts required skills, domain, and experience level via LLM |
| **Smart Repo Ranking** | LLM scoring + keyword-overlap fallback — no repo ever shows 0% unfairly |
| **Resume Generation** | Tailored action-verb bullets, professional summary, grouped skills section |
| **Skill Gap Analysis** | Shows exactly what the JD needs vs. what your GitHub proves |
| **LaTeX Export** | 3 templates: ATS Classic, Modern, Research |

---

## 🏗️ Architecture

```
Streamlit Frontend  (dashboard.py)
        ↓  JSON-RPC over stdio
MCP Client Wrapper  (client.py)
        ↓
FastMCP Server      (server.py)
  ├── 🔧 Tool: extract_github_profile
  ├── 🔧 Tool: analyze_job_description
  ├── 🔧 Tool: score_repositories
  └── 🔧 Tool: generate_resume_content
        ↓
LaTeX Generator     (latex.py)
```

The Streamlit frontend **never** calls GitHub or Groq directly. Every operation is a structured MCP tool call to the server, which runs as a subprocess communicating over `stdio`.

---

## 📁 Project Structure

```
GithubResumeParser/
├── dashboard.py      # Streamlit UI — renders tabs, calls MCP client
├── client.py         # MCP Client — asyncio stdio wrapper, sync interface
├── server.py         # FastMCP Server — GitHub API + Groq LLM tools
├── latex.py          # LaTeX templates (ATS Classic, Modern, Research)
├── requirements.txt  # Python dependencies
├── .env.example      # Environment variable template
└── README.md
```

---

## 📋 Prerequisites

- Python 3.10+
- [Groq API key](https://console.groq.com) — free tier works fine
- GitHub Client ID + Secret — optional, raises rate limit from 60 → 5000 req/hr

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
# Edit .env — add your GROQ_API_KEY

# 4. Run
streamlit run dashboard.py
```

Open **http://localhost:8501** in your browser.

---

## 🔑 Environment Variables

```env
# Required
GROQ_API_KEY=gsk_...

# Optional — increases GitHub API rate limit from 60 to 5000 req/hr
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret
```

---

## 🖥️ User Flow

```
Enter GitHub Username
        ↓
Paste Job Description
        ↓
Choose Resume Style  (1-page / 2-page · ATS / Modern / Research)
        ↓
Click 🚀 Generate Resume
        ↓
Review Ranked Projects with real match %
        ↓
Export .tex → compile on Overleaf or locally
```

---

## 📄 Output Tabs

### 📄 Resume Tab
- Full white-paper resume preview rendered in the browser
- Download as `.tex` (LaTeX)

### 🏆 Projects Tab
- All repos scored by LLM relevance against the JD
- Real match % with matched skill badges
- ▲ / ▼ reorder controls

### 🎯 Skills Gap Tab
- **✅ Skills You Have** — JD-required skills evidenced in your GitHub
- **❌ Skills to Learn** — Required but not found in your repos
- Full candidate tech stack extracted from all repos

### ⚙️ LaTeX Tab
- Full LaTeX source, syntax-highlighted
- Compile with `pdflatex resume.tex` or upload to [Overleaf](https://overleaf.com)

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Agent Protocol | MCP / FastMCP (JSON-RPC over stdio) |
| LLM | Groq + LLaMA 3.3 70B |
| Data Source | GitHub REST API v3 |
| Export | LaTeX (pdflatex / Overleaf) |
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
- [ ] MCP Resources — expose generated resumes as downloadable resources
- [ ] MCP Prompts — recruiter & candidate persona prompt templates

---

## 📝 License

MIT — see [LICENSE](LICENSE).
