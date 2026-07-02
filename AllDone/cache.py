"""
cache.py — Disk-based JSON cache with TTL for GitHub API responses.

Usage:
    from cache import disk_cache, get_cached, set_cached

    @disk_cache("repos", ttl_hours=24)
    def fetch_repos(username): ...
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Optional

CACHE_DIR = Path.home() / ".alldone_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_TTL_HOURS = 24


def _cache_path(namespace: str, key: str) -> Path:
    hashed = hashlib.md5(key.encode()).hexdigest()
    ns_dir = CACHE_DIR / namespace
    ns_dir.mkdir(exist_ok=True)
    return ns_dir / f"{hashed}.json"


def get_cached(namespace: str, key: str, ttl_hours: float = DEFAULT_TTL_HOURS) -> Optional[Any]:
    """Return cached value if it exists and has not expired. Otherwise None."""
    path = _cache_path(namespace, key)
    if not path.exists():
        return None
    try:
        entry = json.loads(path.read_text(encoding="utf-8"))
        age_hours = (time.time() - entry["ts"]) / 3600
        if age_hours > ttl_hours:
            path.unlink(missing_ok=True)
            return None
        return entry["data"]
    except Exception:
        return None


def set_cached(namespace: str, key: str, data: Any) -> None:
    """Persist data to disk cache."""
    path = _cache_path(namespace, key)
    try:
        path.write_text(
            json.dumps({"ts": time.time(), "data": data}, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
    except Exception:
        pass  # Cache write failure is non-fatal


def disk_cache(namespace: str, ttl_hours: float = DEFAULT_TTL_HOURS):
    """Decorator: caches the return value of a function keyed by its arguments."""
    def decorator(fn):
        def wrapper(*args, **kwargs):
            key = json.dumps({"args": args, "kwargs": kwargs}, default=str)
            cached = get_cached(namespace, key, ttl_hours)
            if cached is not None:
                return cached
            result = fn(*args, **kwargs)
            set_cached(namespace, key, result)
            return result
        wrapper.__wrapped__ = fn
        return wrapper
    return decorator


def cache_stats() -> dict:
    """Return a summary of cache usage."""
    total_files = total_bytes = 0
    for f in CACHE_DIR.rglob("*.json"):
        total_files += 1
        total_bytes += f.stat().st_size
    return {"files": total_files, "size_kb": round(total_bytes / 1024, 1), "dir": str(CACHE_DIR)}


def clear_namespace(namespace: str) -> int:
    """Delete all cache files for a given namespace. Returns count deleted."""
    ns_dir = CACHE_DIR / namespace
    count = 0
    if ns_dir.exists():
        for f in ns_dir.glob("*.json"):
            f.unlink()
            count += 1
    return count
