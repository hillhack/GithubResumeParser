import json
import re

def extract_json_from_llm(text: str) -> dict:
    """Extracts JSON from an LLM response that might be wrapped in markdown or have extra text."""
    text = text.strip()
    
    # Try direct parse first
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict): return parsed
        if isinstance(parsed, list) and len(parsed) > 0 and isinstance(parsed[0], dict): return parsed[0]
    except json.JSONDecodeError:
        pass
        
    # Look for ```json ... ``` block
    match = re.search(r'```(?:json)?\s*(\{.*\}|\[.*\])\s*```', text, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(1))
            if isinstance(parsed, dict): return parsed
            if isinstance(parsed, list) and len(parsed) > 0 and isinstance(parsed[0], dict): return parsed[0]
        except json.JSONDecodeError:
            pass
            
    # Try finding the first { and last }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            parsed = json.loads(text[start:end+1])
            if isinstance(parsed, dict): return parsed
            if isinstance(parsed, list) and len(parsed) > 0 and isinstance(parsed[0], dict): return parsed[0]
        except json.JSONDecodeError:
            pass
            
    # As a final fallback, try to extract a list if it's a list
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            parsed = json.loads(text[start:end+1])
            if isinstance(parsed, list) and len(parsed) > 0 and isinstance(parsed[0], dict): return parsed[0]
        except json.JSONDecodeError:
            pass
            
    return {}
