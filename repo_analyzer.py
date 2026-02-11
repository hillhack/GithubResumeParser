"""
Minimal Repo Analyzer
Analyzes GitHub repos against a job description using Gemini API
"""

import os
import json
import requests
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv('../.env')

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET')

# Gemini API endpoint (using gemini-2.0-flash)
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"


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
        # Get the raw content
        content_url = readme_data.get('download_url')
        if content_url:
            content_response = requests.get(content_url)
            if content_response.status_code == 200:
                return content_response.text
    return None


def analyze_similarity(readme_content, job_description):
    """Use Gemini to analyze similarity between README and JD"""
    
    if not readme_content or len(readme_content.strip()) < 50:
        return {
            'score': 0,
            'relevance': 'No Content',
            'reasoning': 'README is too short or empty'
        }
    
    prompt = f"""
You are analyzing a GitHub project's README against a job description.

JOB DESCRIPTION:
{job_description}

PROJECT README:
{readme_content[:2000]}  # Limit to first 2000 chars

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
        # Make REST API call to Gemini with retry logic
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        
        # Retry up to 3 times for rate limiting
        max_retries = 3
        for attempt in range(max_retries):
            response = requests.post(GEMINI_API_URL, json=payload)
            
            if response.status_code == 200:
                break
            elif response.status_code == 429:
                # Rate limited, wait and retry
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 3  # 3, 6, 9 seconds
                    print(f"  ⏳ Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    return {
                        'score': 0,
                        'relevance': 'Rate Limited',
                        'reasoning': 'API rate limit exceeded after retries'
                    }
            else:
                return {
                    'score': 0,
                    'relevance': 'API Error',
                    'reasoning': f'API returned status {response.status_code}'
                }
        
        result_data = response.json()
        result_text = result_data['candidates'][0]['content']['parts'][0]['text']
        
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
        
        # Add small delay between requests to avoid rate limiting
        time.sleep(2)
        
        return {
            'score': score,
            'relevance': relevance,
            'reasoning': reasoning,
            'full_response': result_text
        }
    
    except Exception as e:
        print(f"  ⚠️  Gemini API error: {str(e)}")
        return {
            'score': 0,
            'relevance': 'Error',
            'reasoning': str(e)
        }


def analyze_all_repos(username, job_description):
    """Analyze all repos against the JD"""
    
    # Load GitHub data
    github_data = load_github_data()
    repos = github_data['repositories']
    
    print(f"\n🔍 Analyzing {len(repos)} repositories for @{username}")
    print("=" * 60)
    
    results = []
    
    for i, repo in enumerate(repos, 1):
        repo_name = repo['name']
        repo_full_name = f"{username}/{repo_name}"
        
        print(f"\n[{i}/{len(repos)}] {repo_name}")
        print(f"  Description: {repo['description'] or 'No description'}")
        
        # Fetch README
        readme = fetch_readme(repo_full_name)
        
        if readme:
            print(f"  📄 README found ({len(readme)} chars)")
            
            # Analyze with Gemini
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
    
    # Sort by score
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
    
    # Job Description
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
    
    # Get username from github_data.json
    github_data = load_github_data()
    username = github_data['profile']['username']
    
    # Analyze all repos
    results = analyze_all_repos(username, JOB_DESCRIPTION)
    
    # Save results
    save_analysis_results(results)
    
    # Print summary
    print_summary(results)
    
    print("\n✅ Analysis complete!")
