# 🎯 GitHub Resume Parser

**Simple MVP to extract GitHub data and analyze repos using AI**

---

## 📋 What This Does

1. **Extracts** your GitHub profile, repos, languages, and stats
2. **Analyzes** each repo using AI (Gemini or Groq) against job descriptions
3. **Ranks** repos by relevance to help build your resume

---

## 📁 Two Main Files

| File | Purpose | What It Does |
|------|---------|--------------|
| **`github_data_extractor.py`** | Data extraction | Gets all GitHub data via API |
| **`ai_analyzer.py`** | AI/ML analysis | Uses AI to analyze repos vs job description |

---

## 🚀 Quick Start

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Setup API Keys
Add to `.env` file in parent directory (`../`):
```
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret

# Add ONE of these (Groq recommended):
GROQ_API_KEY=your_groq_key          # Fast, high limits (get from console.groq.com)
GEMINI_API_KEY=your_gemini_key      # Slower, low limits
```

### Step 3: Extract GitHub Data
```bash
python3 github_data_extractor.py
```
- Enter any GitHub username
- Creates `github_data.json`

### Step 4: Analyze with AI
```bash
python3 ai_analyzer.py
```
- Reads `github_data.json`
- Analyzes last 10 non-forked repos
- Creates `repo_analysis.json`
- Auto-uses Groq if available, otherwise Gemini

---

## 📊 Example Output

**Data Extraction:**
```
✅ Data extraction complete!
Profile: @hillhack
Repos: 28
Stars: 3
Languages: Python, Jupyter Notebook, Rust
```

**AI Analysis:**
```
🔍 Analyzing last 10 non-forked repositories for @hillhack
   Using: Groq (Fast)
   Filtered: 5 forked repos
============================================================

[1/10] GithubResumeParser
  📄 README found (3528 chars)
  ⭐ Score: 7/10
  📊 Relevance: Medium
  💡 Project demonstrates data extraction and API integration skills...
```

---

## ⚙️ Customization

### Change Job Description
Edit `ai_analyzer.py` line ~280:
```python
JOB_DESCRIPTION = """
Your custom job description here...
"""
```

### Analyze Different Number of Repos
Edit `ai_analyzer.py` line ~225:
```python
repos = own_repos[:10]  # Change 10 to any number
```

---

## 🔧 API Comparison

| API | Speed | Rate Limit | Setup |
|-----|-------|------------|-------|
| **Groq** ⚡ | Fast | 30 req/min | console.groq.com |
| **Gemini** 🐌 | Slow | 1-2 req/min | aistudio.google.com |

**Recommendation**: Use Groq for speed and higher limits!

---

## ⚠️ Troubleshooting

**Issue**: `github_data.json` not found  
**Fix**: Run `github_data_extractor.py` first

**Issue**: Rate limit errors with Gemini  
**Fix**: Switch to Groq API (add `GROQ_API_KEY` to `.env`)

**Issue**: No AI API key found  
**Fix**: Add `GROQ_API_KEY` or `GEMINI_API_KEY` to `.env`

**Issue**: Repos without README get score 0  
**Fix**: Add READMEs to your important projects

---

## 📝 File Structure

```
GithubResumeParser/
├── github_data_extractor.py   # FILE 1: Data extraction
├── ai_analyzer.py              # FILE 2: AI/ML analysis
├── github_data.json            # Generated: Extracted data
├── repo_analysis.json          # Generated: Analysis results
├── requirements.txt            # Dependencies
├── .gitignore                  # Ignore generated files
└── README.md                   # This file
```

---

## 🎯 How It Works

**Step 1: Data Extraction**
- Uses GitHub REST API
- Fetches profile, repos, languages
- Filters out forked repos
- Saves to JSON

**Step 2: AI Analysis**
- Fetches README for each repo
- Sends to AI (Groq or Gemini)
- Gets relevance score 0-10
- Ranks by match with job description

---

## ✅ Features

- ✅ **Simple**: Just 2 Python files
- ✅ **Smart**: Auto-selects best AI API
- ✅ **Fast**: Groq analyzes 10 repos in ~30 seconds
- ✅ **Filtered**: Skips forked repos automatically
- ✅ **Free**: Both APIs have free tiers

---

**Ready to use!** 🚀