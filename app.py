"""Web App for GitHub Resume Parser"""
from flask import Flask, render_template, request, jsonify
import os, json, requests, time

app = Flask(__name__)

def get_readme(username, repo, groq_key):
    """Fetch README from GitHub"""
    url = f"https://api.github.com/repos/{username}/{repo}/readme"
    resp = requests.get(url)
    if resp.status_code == 200:
        download_url = resp.json().get('download_url')
        if download_url:
            return requests.get(download_url).text
    return None

def ask_ai(readme, job_desc, groq_key):
    """Ask Groq AI to analyze"""
    if not readme or len(readme.strip()) < 50:
        return {'score': 0, 'relevance': 'No Content'}
    
    prompt = f"""Analyze this GitHub README against a job description.

JOB: {job_desc}
README: {readme[:2000]}

Respond as:
SCORE: [0-10]
RELEVANCE: [High/Medium/Low]
REASONING: [2-3 sentences]"""
    
    resp = requests.post("https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {groq_key}"},
        json={"model": "llama-3.3-70b-versatile", 
              "messages": [{"role": "user", "content": prompt}],
              "temperature": 0.3, "max_tokens": 500})
    
    if resp.status_code != 200:
        return {'score': 0, 'relevance': 'Error', 'reasoning': f'API error {resp.status_code}'}
    
    text = resp.json()['choices'][0]['message']['content']
    time.sleep(0.5)
    
    # Parse
    score, relevance, reasoning = 0, 'Unknown', ''
    for line in text.split('\n'):
        if 'SCORE:' in line: 
            try: score = int(line.split(':')[1].strip().split('/')[0])
            except: pass
        elif 'RELEVANCE:' in line: relevance = line.split(':')[1].strip()
        elif 'REASONING:' in line: reasoning = line.split(':', 1)[1].strip()
    
    return {'score': score, 'relevance': relevance, 'reasoning': reasoning}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    username = data.get('username')
    groq_key = data.get('groq_key')
    job_desc = data.get('job_desc')
    
    if not all([username, groq_key, job_desc]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Get user repos
    resp = requests.get(f"https://api.github.com/users/{username}/repos",
                       params={'per_page': 100, 'sort': 'updated'})
    
    if resp.status_code != 200:
        return jsonify({'error': f'GitHub API error: {resp.status_code}'}), 400
    
    repos = resp.json()
    
    # Filter non-forked, get last 10
    own_repos = [r for r in repos if not r.get('fork', False)][:10]
    
    results = []
    for repo in own_repos:
        name = repo['name']
        readme = get_readme(username, name, groq_key)
        
        if readme:
            analysis = ask_ai(readme, job_desc, groq_key)
        else:
            analysis = {'score': 0, 'relevance': 'No README', 'reasoning': 'No README found'}
        
        results.append({
            'name': name,
            'url': repo['html_url'],
            'stars': repo['stargazers_count'],
            'language': repo['language'],
            'analysis': analysis
        })
    
    # Sort by score
    results.sort(key=lambda x: x['analysis']['score'], reverse=True)
    
    return jsonify({'results': results})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
