import asyncio
import logging
from typing import Any, Dict, List, Mapping, Optional
from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError

logger = logging.getLogger(__name__)


class LLMClient:
    _max_retries = 3

    def __init__(self, settings: Any):
        self._model = settings.llm_model
        self._client = AsyncOpenAI(
            api_key=settings.llm_api_key or "EMPTY_KEY",
            base_url=settings.llm_base_url,
            timeout=settings.llm_timeout_sec,
        )

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
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        logger.debug(f"Calling LLM with {len(messages)} messages")

        async def _call():
            resp = await self._client.chat.completions.create(**kwargs)
            return resp.choices[0].message

        return await self._retry_with_backoff(_call)
