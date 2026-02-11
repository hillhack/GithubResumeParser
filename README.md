# 🎯 GitHub Resume Parser

**Simple MVP to extract GitHub data and analyze repos against job descriptions**

---

## 📋 What This Does

1. **Extracts** your GitHub profile, repos, languages, and stats
2. **Analyzes** each repo's README against a job description using AI
3. **Ranks** repos by relevance to help build your resume

---

## 🚀 Quick Start

### Step 1: Setup (One-Time)
```bash
# Install dependencies
pip install -r requirements.txt
```

Make sure your `.env` file exists in the parent directory (`../`) with:
```
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret
GEMINI_API_KEY=your_gemini_api_key
```

### Step 2: Extract GitHub Data
```bash
python3 github_data_extractor.py
```
- Enter any GitHub username when prompted
- Creates `github_data.json` with all repos and profile info
- **This is the main file you run first!** ✅

### Step 3: Analyze Repos (Optional)
```bash
python3 repo_analyzer.py
```
- Reads `github_data.json` from Step 2
- Analyzes each repo's README against the job description
- Creates `repo_analysis.json` with relevance scores
- ⚠️ **Note:** Free Gemini API has strict rate limits (1-2 req/min)

---

## 📁 Files Explained

### Python Scripts (What You Run)
| File | Purpose | Run Order |
|------|---------|-----------|
| `github_data_extractor.py` | Extracts GitHub data | **Run FIRST** |
| `repo_analyzer.py` | Analyzes repos vs JD | Run second (optional) |

### Output Files (Auto-Generated)
| File | What It Contains |
|------|------------------|
| `github_data.json` | All your GitHub data (profile, repos, languages) |
| `repo_analysis.json` | Repo analysis results with scores 0-10 |

### Config Files
| File | Purpose |
|------|---------|
| `requirements.txt` | Python dependencies |
| `README.md` | This file |

---

## 📊 Example Output

After running `github_data_extractor.py`:
```
✅ Data extraction complete!
Profile: @hillhack
Repos: 28
Stars: 3
Languages: Python, Jupyter Notebook, Shell, Rust, C++
```

After running `repo_analyzer.py`:
```
🏆 Top 5 Most Relevant:
1. mesa-llm - Score: 9/10
   Relevance: High
   Language: Python
   ⭐ 0 stars
```

---

## ⚙️ Customization

### Change the Job Description
Edit `repo_analyzer.py` and modify the `JOB_DESCRIPTION` variable (around line 200):
```python
JOB_DESCRIPTION = """
Your custom job description here...
"""
```

### Analyze Specific Repos Only
Modify line ~165 in `repo_analyzer.py`:
```python
# Analyze only first 5 repos
for i, repo in enumerate(repos[:5], 1):
```

---

## ⚠️ Known Issues

1. **Free Gemini API Rate Limits**: 
   - ~1-2 requests per minute
   - Script includes retry logic but may still fail with many repos
   - **Solutions:**
     - **Option 1**: Wait 24 hours for rate limits to reset
     - **Option 2**: Use `repo_analyzer_groq.py` instead (free Groq API with higher limits)
     - **Option 3**: Upgrade to Gemini paid tier

2. **Using Groq Instead (Recommended)**:
   ```bash
   # 1. Get free API key from https://console.groq.com
   # 2. Add to .env file:
   GROQ_API_KEY=your_groq_api_key
   
   # 3. Run the Groq analyzer:
   python3 repo_analyzer_groq.py
   ```
   - ✅ Much higher rate limits (30 requests/min)
   - ✅ Faster responses
   - ✅ Still completely free

3. **No README = Score 0**: 
   - Repos without READMEs can't be analyzed
   - **Solution**: Add READMEs to your important projects

---

## 🔧 Troubleshooting

**Issue**: `github_data.json` not found  
**Fix**: Run `github_data_extractor.py` first

**Issue**: API rate limit errors (429)  
**Fix**: Wait a few hours or reduce number of repos to analyze

**Issue**: No .env file found  
**Fix**: Create `.env` in parent directory with your API keys

---

## 📝 Summary

- **Main file to run**: `github_data_extractor.py` → extracts GitHub data
- **Optional second file**: `repo_analyzer.py` → analyzes with AI (has rate limits)
- **Output**: Two JSON files with all your data

**Current status after your run:**
✅ Successfully extracted data for @hillhack (28 repos)  
⚠️ Analysis hit API rate limits (can retry later)