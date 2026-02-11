"""AI Repo Analyzer - Minimal"""
import os, json, requests, time
from dotenv import load_dotenv

load_dotenv('../.env')

GROQ_KEY = os.getenv('GROQ_API_KEY')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')
GITHUB_AUTH = (os.getenv('GITHUB_CLIENT_ID'), os.getenv('GITHUB_CLIENT_SECRET'))

def get_readme(repo_full_name):
    """Fetch README from GitHub"""
    url = f"https://api.github.com/repos/{repo_full_name}/readme"
    resp = requests.get(url, auth=GITHUB_AUTH)
    if resp.status_code == 200:
        download_url = resp.json().get('download_url')
        if download_url:
            return requests.get(download_url).text
    return None

def ask_ai(readme, job_desc):
    """Ask AI to analyze README vs job description"""
    if not readme or len(readme.strip()) < 50:
        return {'score': 0, 'relevance': 'No Content', 'reasoning': 'README too short'}
    
    prompt = f"""Analyze this GitHub README against a job description.

JOB: {job_desc}
README: {readme[:2000]}

Respond EXACTLY as:
SCORE: [0-10]
RELEVANCE: [High/Medium/Low/None]
REASONING: [2-3 sentences]"""
    
    # Use Groq if available (faster), else Gemini
    if GROQ_KEY:
        resp = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}"},
            json={"model": "llama-3.3-70b-versatile", 
                  "messages": [{"role": "user", "content": prompt}],
                  "temperature": 0.3, "max_tokens": 500})
        if resp.status_code == 200:
            text = resp.json()['choices'][0]['message']['content']
            time.sleep(0.5)
        else:
            return {'score': 0, 'relevance': 'Error', 'reasoning': f'API error {resp.status_code}'}
    else:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
        resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
        if resp.status_code == 200:
            text = resp.json()['candidates'][0]['content']['parts'][0]['text']
            time.sleep(2)
        else:
            return {'score': 0, 'relevance': 'Error', 'reasoning': f'API error {resp.status_code}'}
    
    # Parse response
    score, relevance, reasoning = 0, 'Unknown', ''
    for line in text.split('\n'):
        if line.startswith('SCORE:'): score = int(line.split(':')[1].strip().split('/')[0])
        elif line.startswith('RELEVANCE:'): relevance = line.split(':')[1].strip()
        elif line.startswith('REASONING:'): reasoning = line.split(':', 1)[1].strip()
    
    return {'score': score, 'relevance': relevance, 'reasoning': reasoning}

def analyze_repos(job_desc):
    """Analyze repos against job description"""
    data = json.load(open('github_data.json'))
    username = data['profile']['username']
    
    # Filter: non-forked repos only, last 10
    repos = [r for r in data['repositories'] if not r.get('is_fork', False)][:10]
    
    api_name = "Groq" if GROQ_KEY else "Gemini"
    print(f"\n🔍 Analyzing {len(repos)} repos for @{username} using {api_name}")
    print("=" * 60)
    
    results = []
    for i, repo in enumerate(repos, 1):
        name = repo['name']
        print(f"\n[{i}/{len(repos)}] {name}")
        
        readme = get_readme(f"{username}/{name}")
        if readme:
            print(f"  📄 README ({len(readme)} chars)")
            analysis = ask_ai(readme, job_desc)
            print(f"  ⭐ {analysis['score']}/10 - {analysis['relevance']}")
        else:
            print(f"  ❌ No README")
            analysis = {'score': 0, 'relevance': 'No README', 'reasoning': 'No README file'}
        
        results.append({
            'repo': name,
            'url': repo['url'],
            'stars': repo['stars'],
            'language': repo['language'],
            'analysis': analysis
        })
    
    # Save and show top 5
    json.dump(results, open('repo_analysis.json', 'w'), indent=2)
    
    print("\n" + "=" * 60)
    print("🏆 TOP 5 MATCHES:")
    for i, r in enumerate(sorted(results, key=lambda x: x['analysis']['score'], reverse=True)[:5], 1):
        print(f"\n{i}. {r['repo']} - {r['analysis']['score']}/10")
        print(f"   {r['analysis']['reasoning'][:80]}...")
    
    print("\n✅ Done! Saved to repo_analysis.json")

if __name__ == "__main__":
    if not GROQ_KEY and not GEMINI_KEY:
        print("❌ Add GROQ_API_KEY or GEMINI_API_KEY to .env")
        exit(1)
    
    # Get job description from user
    print("\n📝 Enter the job description (paste and press Ctrl+D or Ctrl+Z when done):")
    print("=" * 60)
    
    jd_lines = []
    try:
        while True:
            line = input()
            jd_lines.append(line)
    except EOFError:
        pass
    
    job_desc = '\n'.join(jd_lines).strip()
    
    if not job_desc:
        print("\n⚠️  No job description provided. Using default Mesa-LLM JD...")
        job_desc = """Mesa-LLM: RAG pipeline development, prompt engineering, agentic AI with 
        LangChain/LlamaIndex, model evaluation, LLM integration with Python APIs."""
    
    analyze_repos(job_desc)
