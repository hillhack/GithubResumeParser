"""
Repo Analyzer using Groq API (Free with higher rate limits)
"""

import os
import json
import requests
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv('../.env')

GROQ_API_KEY = os.getenv('GROQ_API_KEY')  # Add this to your .env
GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET')

# Groq API endpoint
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


def load_github_data(filename='github_data.json'):
    """Load extracted GitHub data"""
    with open(filename, 'r') as f:
        return json.load(f)


def fetch_readme(repo_full_name):
    """Fetch README content from a GitHub repo"""
    url = f"https://api.github.com/repos/{repo_full_name}/readme"
    response = requests.get(url, auth=(GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET))
    
    if response.status_code == 200:
        readme_data = response.json()
        content_url = readme_data.get('download_url')
        if content_url:
            content_response = requests.get(content_url)
            if content_response.status_code == 200:
                return content_response.text
    return None


def analyze_similarity(readme_content, job_description):
    """Use Groq to analyze similarity between README and JD"""
    
    if not readme_content or len(readme_content.strip()) < 50:
        return {
            'score': 0,
            'relevance': 'No Content',
            'reasoning': 'README is too short or empty'
        }
    
    prompt = f"""You are analyzing a GitHub project's README against a job description.

JOB DESCRIPTION:
{job_description}

PROJECT README:
{readme_content[:2000]}

Task: Analyze how relevant this project is to the job requirements.

Provide your response in this exact format:
SCORE: [0-10]
RELEVANCE: [High/Medium/Low/None]
REASONING: [2-3 sentences explaining the match]

Focus on:
- Technologies used (RAG, LLMs, embeddings, vector DBs)
- Project complexity and scope
- Relevant skills demonstrated
"""
    
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 500
        }
        
        response = requests.post(GROQ_API_URL, headers=headers, json=payload)
        
        if response.status_code != 200:
            return {
                'score': 0,
                'relevance': 'API Error',
                'reasoning': f'API returned status {response.status_code}'
            }
        
        result_data = response.json()
        result_text = result_data['choices'][0]['message']['content']
        
        # Parse the response
        lines = result_text.strip().split('\n')
        score = 0
        relevance = 'Unknown'
        reasoning = ''
        
        for line in lines:
            if line.startswith('SCORE:'):
                try:
                    score = int(line.split(':')[1].strip().split('/')[0])
                except:
                    score = 0
            elif line.startswith('RELEVANCE:'):
                relevance = line.split(':')[1].strip()
            elif line.startswith('REASONING:'):
                reasoning = line.split(':', 1)[1].strip()
        
        # Small delay to be respectful
        time.sleep(0.5)
        
        return {
            'score': score,
            'relevance': relevance,
            'reasoning': reasoning,
            'full_response': result_text
        }
    
    except Exception as e:
        print(f"  ⚠️  Groq API error: {str(e)}")
        return {
            'score': 0,
            'relevance': 'Error',
            'reasoning': str(e)
        }


def analyze_all_repos(username, job_description):
    """Analyze non-forked repos against the JD (last 10 only)"""
    
    github_data = load_github_data()
    all_repos = github_data['repositories']
    
    # Filter out forked repos
    own_repos = [repo for repo in all_repos if not repo.get('is_fork', False)]
    repos = own_repos[:10]
    
    print(f"\n🔍 Analyzing last {len(repos)} non-forked repositories for @{username}")
    print(f"   (Using Groq API - much faster!)")
    print("=" * 60)
    
    results = []
    
    for i, repo in enumerate(repos, 1):
        repo_name = repo['name']
        repo_full_name = f"{username}/{repo_name}"
        
        print(f"\n[{i}/{len(repos)}] {repo_name}")
        print(f"  Description: {repo['description'] or 'No description'}")
        
        readme = fetch_readme(repo_full_name)
        
        if readme:
            print(f"  📄 README found ({len(readme)} chars)")
            analysis = analyze_similarity(readme, job_description)
            
            print(f"  ⭐ Score: {analysis['score']}/10")
            print(f"  📊 Relevance: {analysis['relevance']}")
            print(f"  💡 {analysis['reasoning']}")
        else:
            print(f"  ❌ No README found")
            analysis = {
                'score': 0,
                'relevance': 'No README',
                'reasoning': 'Repository has no README file'
            }
        
        results.append({
            'repo_name': repo_name,
            'repo_url': repo['url'],
            'description': repo['description'],
            'stars': repo['stars'],
            'language': repo['language'],
            'is_fork': repo.get('is_fork', False),
            'analysis': analysis
        })
    
    return results


def save_analysis_results(results, filename='repo_analysis.json'):
    """Save analysis results to JSON"""
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Results saved to {filename}")


def print_summary(results):
    """Print top matching repos"""
    print("\n" + "=" * 60)
    print("📈 TOP MATCHING REPOSITORIES")
    print("=" * 60)
    
    sorted_results = sorted(results, key=lambda x: x['analysis']['score'], reverse=True)
    
    print("\n🏆 Top 5 Most Relevant:")
    for i, result in enumerate(sorted_results[:5], 1):
        analysis = result['analysis']
        print(f"\n{i}. {result['repo_name']} - Score: {analysis['score']}/10")
        print(f"   Relevance: {analysis['relevance']}")
        print(f"   Language: {result['language']}")
        print(f"   ⭐ {result['stars']} stars")
        print(f"   {analysis['reasoning'][:100]}...")


if __name__ == "__main__":
    
    JOB_DESCRIPTION = """
    Mesa-LLM Responsibilities:
    
    - RAG Pipeline Development: Design, implement, and optimize Retrieval-Augmented Generation (RAG) 
      pipelines for grounding LLMs with proprietary data. This includes experimenting with various 
      chunking strategies, embedding models, and vector database indexing methods (e.g., Pinecone, 
      Chroma, FAISS). Implementing advanced retrieval techniques like hybrid search (vector + lexical), 
      re-ranking, and document pre-processing.
    
    - Prompt Engineering & Optimization: Develop and refine sophisticated prompting techniques 
      (e.g., Chain-of-Thought, ReAct, Few-Shot) to maximize model accuracy, relevance, and safety 
      across various tasks (summarization, Q&A, reasoning).
    
    - Agentic AI Prototyping: Assist in building and evaluating multi-step, goal-driven AI agents 
      using frameworks like LangChain or LlamaIndex. Focus on implementing tool-use, memory, and 
      reflection capabilities.
    
    - Model Evaluation & Benchmarking: Conduct rigorous quantitative and qualitative evaluations 
      of RAG and LLM outputs to measure performance against key metrics (e.g., hallucination rate, 
      factual accuracy, latency, cost).
    
    - LLM Integration: Integrate proof-of-concept models and RAG components into software stack, 
      often using Python and APIs (e.g., OpenAI, Gemini, or self-hosted models).
    """
    
    github_data = load_github_data()
    username = github_data['profile']['username']
    
    # Check if Groq API key is set
    if not GROQ_API_KEY:
        print("❌ Error: GROQ_API_KEY not found in .env file")
        print("\n📝 To use Groq:")
        print("1. Sign up at https://console.groq.com")
        print("2. Get your API key")
        print("3. Add to .env file: GROQ_API_KEY=your_api_key")
        exit(1)
    
    results = analyze_all_repos(username, JOB_DESCRIPTION)
    save_analysis_results(results)
    print_summary(results)
    
    print("\n✅ Analysis complete!")
