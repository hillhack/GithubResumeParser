"""cache.py — Disk-based caching for repository profiles and GitHub API responses.

Supports:
  - @disk_cache(namespace) decorator for pure functions
  - Explicit get/set for repository profiles
  - TTL-based expiry (default 24 hours)
  - Cache invalidation by username or repo
"""

import os
import json
import time
import hashlib
import logging
from functools import wraps
from .constants import CACHE_DIR

log = logging.getLogger(__name__)

os.makedirs(CACHE_DIR, exist_ok=True)

_DEFAULT_TTL_SECONDS = 86400  # 24 hours


def _cache_path(namespace: str, key: str) -> str:
    hashed = hashlib.md5(key.encode("utf-8")).hexdigest()
    return os.path.join(CACHE_DIR, f"{namespace}_{hashed}.json")


def _load(path: str, ttl: int) -> dict | list | None:
    """Load a cached JSON file if it exists and is not expired."""
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        cached_at = payload.get("__cached_at__", 0)
        if ttl > 0 and (time.time() - cached_at) > ttl:
            log.debug(f"Cache expired: {path}")
            return None
        return payload.get("__data__")
    except Exception as e:
        log.debug(f"Cache read error ({path}): {e}")
        return None


def _save(path: str, data) -> None:
    """Write data to a cache file with a timestamp."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"__cached_at__": time.time(), "__data__": data}, f)
    except Exception as e:
        log.debug(f"Cache write error ({path}): {e}")


def disk_cache(namespace: str, ttl: int = _DEFAULT_TTL_SECONDS):
    """Decorator: caches the return value of a function to disk.

    Args:
        namespace: Cache key prefix (e.g. "repo_profile", "github_api").
        ttl:       Time-to-live in seconds. 0 = no expiry.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            skip = kwargs.pop("skip_cache", False)
            cache_key = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
            path = _cache_path(namespace, cache_key)

            if not skip:
                cached = _load(path, ttl)
                if cached is not None:
                    log.debug(f"Cache hit: {namespace}")
                    return cached

            result = func(*args, **kwargs)
            if result is not None:
                _save(path, result)
            return result
        return wrapper
    return decorator


# ── Explicit repo-profile cache helpers ──────────────────────────────────────

def get_repo_profile_cache(username: str, repo_name: str) -> dict | None:
    """Return a cached RepositoryProfile dict or None if not cached / expired."""
    path = _cache_path("repo_profile", f"{username}/{repo_name}")
    return _load(path, _DEFAULT_TTL_SECONDS)


def set_repo_profile_cache(username: str, repo_name: str, profile: dict) -> None:
    """Cache a RepositoryProfile dict for a given repo."""
    path = _cache_path("repo_profile", f"{username}/{repo_name}")
    _save(path, profile)


def clear_repo_cache(username: str) -> int:
    """Delete all cached profiles for a given GitHub username. Returns count deleted."""
    prefix = _cache_path("repo_profile", f"{username}/")
    # We can't enumerate by prefix since we hash the key, so we clear all caches
    count = 0
    for fname in os.listdir(CACHE_DIR):
        if fname.startswith("repo_profile_"):
            os.remove(os.path.join(CACHE_DIR, fname))
            count += 1
    return count


def cache_stats() -> dict:
    """Return basic cache statistics."""
    files = [f for f in os.listdir(CACHE_DIR) if f.endswith(".json")]
    total_size = sum(os.path.getsize(os.path.join(CACHE_DIR, f)) for f in files)
    return {"files": len(files), "size_kb": round(total_size / 1024, 1), "dir": CACHE_DIR}
