import os
import json
import hashlib
from functools import wraps
from .constants import CACHE_DIR

os.makedirs(CACHE_DIR, exist_ok=True)

def _generate_cache_key(namespace: str, *args, **kwargs) -> str:
    key_dict = {"args": args, "kwargs": kwargs}
    key_str = json.dumps(key_dict, sort_keys=True, default=str)
    hashed = hashlib.md5(key_str.encode("utf-8")).hexdigest()
    return f"{namespace}_{hashed}.json"

def disk_cache(namespace: str):
    """Simple disk cache decorator for pure functions returning JSON-serializable data."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            skip_cache = kwargs.get("skip_cache", False)
            if "skip_cache" in kwargs:
                kwargs_copy = dict(kwargs)
                del kwargs_copy["skip_cache"]
            else:
                kwargs_copy = kwargs
                
            cache_file = os.path.join(CACHE_DIR, _generate_cache_key(namespace, *args, **kwargs_copy))
            if not skip_cache and os.path.exists(cache_file):
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    pass # Fallback to computing
            
            result = func(*args, **kwargs_copy)
            
            if result is not None:
                try:
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(result, f)
                except Exception:
                    pass
            return result
        return wrapper
    return decorator
