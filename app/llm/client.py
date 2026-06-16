import asyncio
import hashlib
import json
import logging
from typing import Any, Dict, List, Mapping, Optional
from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError

logger = logging.getLogger(__name__)


class LLMResponseCache:
    def __init__(self, max_size: int = 200, ttl_seconds: int = 1800):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds
        self._hits = 0
        self._misses = 0

    def _make_key(self, kwargs: Dict[str, Any]) -> str:
        cacheable = {
            "model": kwargs.get("model"),
            "messages": kwargs.get("messages"),
            "temperature": kwargs.get("temperature"),
        }
        if kwargs.get("tools"):
            cacheable["tools"] = kwargs["tools"]
        return hashlib.md5(json.dumps(cacheable, default=str).encode()).hexdigest()

    def get(self, kwargs: Dict[str, Any]) -> Optional[Any]:
        import time
        key = self._make_key(kwargs)
        if key in self._cache:
            entry = self._cache[key]
            if time.time() - entry["created_at"] < self._ttl_seconds:
                entry["access_count"] += 1
                self._hits += 1
                logger.debug("LLM cache hit: %s", key[:16])
                return entry["value"]
            else:
                del self._cache[key]
        self._misses += 1
        return None

    def set(self, kwargs: Dict[str, Any], value: Any) -> None:
        import time
        if len(self._cache) >= self._max_size:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].get("access_count", 0))
            del self._cache[oldest_key]
        self._cache[key := self._make_key(kwargs)] = {
            "value": value,
            "created_at": time.time(),
            "access_count": 0,
        }

    def stats(self) -> Dict[str, Any]:
        total = self._hits + self._misses
        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total * 100, 2) if total > 0 else 0,
        }


class LLMClient:
    _max_retries = 3

    def __init__(self, settings: Any, enable_cache: bool = True):
        self._model = settings.llm_model
        self._client = AsyncOpenAI(
            api_key=settings.llm_api_key or "EMPTY_KEY",
            base_url=settings.llm_base_url,
            timeout=settings.llm_timeout_sec,
        )
        self._cache = LLMResponseCache() if enable_cache else None

    async def _retry_with_backoff(self, func, *args, **kwargs):
        for attempt in range(self._max_retries):
            try:
                return await func(*args, **kwargs)
            except (RateLimitError, APITimeoutError) as e:
                if attempt == self._max_retries - 1:
                    raise
                wait_time = 2 ** attempt
                logger.warning(f"Retry {attempt + 1}/{self._max_retries} after {wait_time}s: {e}")
                await asyncio.sleep(wait_time)
            except APIError as e:
                logger.error(f"API error: {e}")
                raise

    async def chat(
        self,
        messages: List[Mapping[str, str]],
        temperature: float = 0.2,
        model: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
    ) -> Any:
        kwargs: Dict[str, Any] = {
            "model": model or self._model,
            "messages": list(messages),
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        if self._cache and temperature == 0.0:
            cached = self._cache.get(kwargs)
            if cached is not None:
                return cached

        logger.debug(f"Calling LLM with {len(messages)} messages")

        async def _call():
            resp = await self._client.chat.completions.create(**kwargs)
            return resp.choices[0].message

        result = await self._retry_with_backoff(_call)

        if self._cache and temperature == 0.0:
            self._cache.set(kwargs, result)

        return result

    def cache_stats(self) -> Optional[Dict[str, Any]]:
        return self._cache.stats() if self._cache else None
