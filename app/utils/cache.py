import hashlib
import json
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import pandas as pd

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class DataCache:
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds
        self._hits = 0
        self._misses = 0

    def _make_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        key_parts = [func_name]
        for arg in args:
            if isinstance(arg, pd.DataFrame):
                key_parts.append(f"df_{hash_pandas_dataframe(arg)}")
            elif isinstance(arg, Path):
                key_parts.append(f"file_{arg}_{arg.stat().st_mtime_ns}" if arg.exists() else f"file_{arg}")
            else:
                key_parts.append(str(arg))
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")
        return hashlib.md5("|".join(key_parts).encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            entry = self._cache[key]
            if time.time() - entry["created_at"] < self._ttl_seconds:
                entry["last_accessed"] = time.time()
                entry["access_count"] += 1
                self._hits += 1
                logger.debug("Cache hit: %s", key[:16])
                return entry["value"]
            else:
                del self._cache[key]
                logger.debug("Cache expired: %s", key[:16])
        self._misses += 1
        return None

    def set(self, key: str, value: Any) -> None:
        if len(self._cache) >= self._max_size:
            self._evict_oldest()
        self._cache[key] = {
            "value": value,
            "created_at": time.time(),
            "last_accessed": time.time(),
            "access_count": 0,
        }
        logger.debug("Cache set: %s", key[:16])

    def _evict_oldest(self) -> None:
        if not self._cache:
            return
        oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]["last_accessed"])
        del self._cache[oldest_key]
        logger.debug("Cache evicted: %s", oldest_key[:16])

    def invalidate(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def stats(self) -> Dict[str, Any]:
        total = self._hits + self._misses
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total * 100, 2) if total > 0 else 0,
        }


def hash_pandas_dataframe(df: pd.DataFrame) -> str:
    return hashlib.md5(pd.util.hash_pandas_object(df).values.tobytes()).hexdigest()


def cached_read_file(path: str, allowed_root: str = "data") -> pd.DataFrame:
    from app.tools.data_tools import read_file
    return read_file(path, allowed_root)


def cached_call_api(url: str, method: str = "GET", headers: dict = None, body: dict = None) -> pd.DataFrame:
    from app.tools.data_tools import call_api
    return call_api(url, method, headers, body)


_global_cache: Optional[DataCache] = None


def get_cache() -> DataCache:
    global _global_cache
    if _global_cache is None:
        _global_cache = DataCache()
    return _global_cache


def cache_result(ttl_seconds: int = 3600):
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            cache = get_cache()
            key = cache._make_key(func.__name__, args, kwargs)
            result = cache.get(key)
            if result is not None:
                return result
            result = func(*args, **kwargs)
            cache.set(key, result)
            return result
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator
