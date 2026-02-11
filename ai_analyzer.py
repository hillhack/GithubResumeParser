"""AI Repo Analyzer - Enhanced with Technical Details Extraction"""
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

def extract_technical_details(readme, job_desc):
    """Extract technical details and analyze against JD using AI"""
    if not readme or len(readme.strip()) < 50:
        return {
            'score': 0,
            'relevance': 'No Content',
            'technical_details': {},
            'reasoning': 'README too short'
        }
    
    prompt = f"""Analyze this GitHub README and extract technical details, then compare against the job description.

JOB DESCRIPTION:
{job_desc}

README:
{readme[:3000]}

Extract and analyze the following in your response:

1. PROBLEM: What problem does this project solve? (1-2 sentences)
2. LLMS_USED: List specific LLMs/models used (e.g., GPT-4, Llama, Claude, Gemini) or "None mentioned"
3. TOOLS: Key frameworks/libraries (e.g., LangChain, LlamaIndex, HuggingFace, OpenAI API)
4. TECHNIQUES: Advanced techniques used:
   - RAG (Retrieval-Augmented Generation): Yes/No
   - Vector Databases: Which ones? (Pinecone, Chroma, FAISS, Weaviate, etc.)
   - Chunking Strategies: Mentioned? (semantic, fixed-size, recursive, etc.)
   - Embeddings: Which models? (OpenAI, Sentence-Transformers, etc.)
   - Hybrid Search: Mentioned? (vector + keyword)
   - Re-ranking: Used? 
5. EVALUATION: Metrics/methods mentioned (accuracy, BLEU, ROUGE, human eval, etc.)
6. HALLUCINATION_CONTROL: Techniques to reduce hallucinations (fact-checking, citations, grounding, etc.)
7. SCORE: Overall relevance to job (0-10)
8. RELEVANCE: High/Medium/Low/None
9. REASONING: Why this score? (2-3 sentences)

Format your response EXACTLY as:
PROBLEM: [answer]
LLMS_USED: [answer]
TOOLS: [answer]
TECHNIQUES_RAG: [Yes/No]
TECHNIQUES_VECTOR_DB: [answer]
TECHNIQUES_CHUNKING: [answer]
TECHNIQUES_EMBEDDINGS: [answer]
TECHNIQUES_HYBRID_SEARCH: [answer]
TECHNIQUES_RERANKING: [answer]
EVALUATION: [answer]
HALLUCINATION_CONTROL: [answer]
SCORE: [0-10]
RELEVANCE: [High/Medium/Low/None]
REASONING: [answer]"""
    
    # Use Groq if available, else Gemini
    if GROQ_KEY:
        resp = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}"},
            json={"model": "llama-3.3-70b-versatile", 
                  "messages": [{"role": "user", "content": prompt}],
                  "temperature": 0.2, "max_tokens": 1000})
        if resp.status_code == 200:
            text = resp.json()['choices'][0]['message']['content']
            time.sleep(0.5)
        else:
            return {'score': 0, 'relevance': 'Error', 'technical_details': {}, 
                   'reasoning': f'API error {resp.status_code}'}
    else:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
        resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
        if resp.status_code == 200:
            text = resp.json()['candidates'][0]['content']['parts'][0]['text']
            time.sleep(2)
        else:
            return {'score': 0, 'relevance': 'Error', 'technical_details': {},
                   'reasoning': f'API error {resp.status_code}'}
    
    # Parse structured response
    details = {
        'problem': '',
        'llms_used': '',
        'tools': '',
        'rag': '',
        'vector_db': '',
        'chunking': '',
        'embeddings': '',
        'hybrid_search': '',
        'reranking': '',
        'evaluation': '',
        'hallucination_control': ''
    }
    
    score, relevance, reasoning = 0, 'Unknown', ''
    
    for line in text.split('\n'):
        line = line.strip()
        if line.startswith('PROBLEM:'): details['problem'] = line.split(':', 1)[1].strip()
        elif line.startswith('LLMS_USED:'): details['llms_used'] = line.split(':', 1)[1].strip()
        elif line.startswith('TOOLS:'): details['tools'] = line.split(':', 1)[1].strip()
        elif line.startswith('TECHNIQUES_RAG:'): details['rag'] = line.split(':', 1)[1].strip()
        elif line.startswith('TECHNIQUES_VECTOR_DB:'): details['vector_db'] = line.split(':', 1)[1].strip()
        elif line.startswith('TECHNIQUES_CHUNKING:'): details['chunking'] = line.split(':', 1)[1].strip()
        elif line.startswith('TECHNIQUES_EMBEDDINGS:'): details['embeddings'] = line.split(':', 1)[1].strip()
        elif line.startswith('TECHNIQUES_HYBRID_SEARCH:'): details['hybrid_search'] = line.split(':', 1)[1].strip()
        elif line.startswith('TECHNIQUES_RERANKING:'): details['reranking'] = line.split(':', 1)[1].strip()
        elif line.startswith('EVALUATION:'): details['evaluation'] = line.split(':', 1)[1].strip()
        elif line.startswith('HALLUCINATION_CONTROL:'): details['hallucination_control'] = line.split(':', 1)[1].strip()
        elif line.startswith('SCORE:'):
            try: score = int(line.split(':')[1].strip().split('/')[0])
            except: pass
        elif line.startswith('RELEVANCE:'): relevance = line.split(':', 1)[1].strip()
        elif line.startswith('REASONING:'): reasoning = line.split(':', 1)[1].strip()
    
    return {
        'score': score,
        'relevance': relevance,
        'reasoning': reasoning,
        'technical_details': details
    }

def analyze_repos(job_desc):
    """Analyze repos with detailed technical extraction"""
    data = json.load(open('github_data.json'))
    username = data['profile']['username']
    
    repos = [r for r in data['repositories'] if not r.get('is_fork', False)][:10]
    
    api_name = "Groq" if GROQ_KEY else "Gemini"
    print(f"\n🔍 Analyzing {len(repos)} repos for @{username} using {api_name}")
    print("=" * 80)
    
    results = []
    for i, repo in enumerate(repos, 1):
        name = repo['name']
        print(f"\n[{i}/{len(repos)}] {name}")
        
        readme = get_readme(f"{username}/{name}")
        if readme:
            print(f"  📄 README ({len(readme)} chars)")
            analysis = extract_technical_details(readme, job_desc)
            
            print(f"  ⭐ Score: {analysis['score']}/10 - {analysis['relevance']}")
            
            # Show key technical details
            tech = analysis['technical_details']
            if tech.get('llms_used') and tech['llms_used'] != 'None mentioned':
                print(f"  🤖 LLMs: {tech['llms_used']}")
            if tech.get('rag') == 'Yes':
                print(f"  🔍 RAG: Yes")
            if tech.get('vector_db') and tech['vector_db'] not in ['None', 'None mentioned', 'Not mentioned']:
                print(f"  💾 Vector DB: {tech['vector_db']}")
        else:
            print(f"  ❌ No README")
            analysis = {
                'score': 0, 
                'relevance': 'No README', 
                'reasoning': 'No README file',
                'technical_details': {}
            }
        
        results.append({
            'repo': name,
            'url': repo['url'],
            'stars': repo['stars'],
            'language': repo['language'],
            'analysis': analysis
        })
    
    # Save detailed results
    json.dump(results, open('repo_analysis_detailed.json', 'w'), indent=2)
    
    # Print summary table
    print("\n" + "=" * 80)
    print("📊 DETAILED ANALYSIS SUMMARY")
    print("=" * 80)
    
    for i, r in enumerate(sorted(results, key=lambda x: x['analysis']['score'], reverse=True)[:10], 1):
        tech = r['analysis'].get('technical_details', {})
        
        print(f"\n{'='*80}")
        print(f"#{i}. {r['repo']} - Score: {r['analysis']['score']}/10 ({r['analysis']['relevance']})")
        print(f"{'='*80}")
        
        if tech.get('problem'):
            print(f"📋 Problem: {tech['problem']}")
        if tech.get('llms_used'):
            print(f"🤖 LLMs: {tech['llms_used']}")
        if tech.get('tools'):
            print(f"🛠️  Tools: {tech['tools']}")
        
        print(f"\n🔬 Techniques:")
        if tech.get('rag'): print(f"  • RAG: {tech['rag']}")
        if tech.get('vector_db'): print(f"  • Vector DB: {tech['vector_db']}")
        if tech.get('chunking'): print(f"  • Chunking: {tech['chunking']}")
        if tech.get('embeddings'): print(f"  • Embeddings: {tech['embeddings']}")
        if tech.get('hybrid_search'): print(f"  • Hybrid Search: {tech['hybrid_search']}")
        if tech.get('reranking'): print(f"  • Re-ranking: {tech['reranking']}")
        
        if tech.get('evaluation'):
            print(f"\n📏 Evaluation: {tech['evaluation']}")
        if tech.get('hallucination_control'):
            print(f"🛡️  Hallucination Control: {tech['hallucination_control']}")
        
        print(f"\n💡 Reasoning: {r['analysis']['reasoning']}")
        print(f"🔗 URL: {r['url']}")
    
    print(f"\n\n✅ Done! Detailed analysis saved to repo_analysis_detailed.json")

if __name__ == "__main__":
    if not GROQ_KEY and not GEMINI_KEY:
        print("❌ Add GROQ_API_KEY or GEMINI_API_KEY to .env")
        exit(1)
    
    # Default JD - edit here if needed
    job_desc = """RAG pipeline development, LLM integration, prompt engineering, 
    vector databases, embeddings, chunking strategies, evaluation metrics"""
    
    print(f"\n📝 Using job description: {job_desc[:80]}...")
    analyze_repos(job_desc)

