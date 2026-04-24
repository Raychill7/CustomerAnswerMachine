import asyncio
import logging
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class DeepSeekError(Exception):
    pass


class DeepSeekClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_url = self.settings.deepseek_base_url.rstrip("/")
        self.api_key = self.settings.deepseek_api_key
        self.model = self.settings.deepseek_model
        self.timeout_seconds = self.settings.deepseek_timeout_seconds
        self.max_retries = self.settings.deepseek_max_retries

    async def chat(self, messages: list[dict[str, str]], temperature: float = 0.2) -> dict[str, Any]:
        if not self.api_key:
            raise DeepSeekError("Missing DEEPSEEK_API_KEY")

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.base_url}/chat/completions"

        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.post(url, headers=headers, json=payload)
                if response.status_code >= 400:
                    raise DeepSeekError(f"DeepSeek HTTP {response.status_code}: {response.text}")
                return response.json()
            except Exception as exc:
                if attempt >= self.max_retries:
                    logger.exception("deepseek_call_failed")
                    raise DeepSeekError(str(exc)) from exc
                await asyncio.sleep(2 ** attempt)
        raise DeepSeekError("Unexpected retry flow")
