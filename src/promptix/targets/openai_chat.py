"""OpenAI-compatible chat completions target (works with OpenAI, vLLM, llama.cpp, Ollama-OpenAI, LM Studio, etc.)."""
from __future__ import annotations

import os
import time

import httpx

from ..core.registry import TARGETS
from .base import Target, TargetResponse


@TARGETS.register("openai")
class OpenAIChatTarget(Target):
    name = "openai"

    def __init__(
        self,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 512,
        timeout: float = 30.0,
        system_prompt: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.temperature = float(temperature)
        self.max_tokens = int(max_tokens)
        self.timeout = float(timeout)
        self.system_prompt = system_prompt
        self._client = httpx.AsyncClient(timeout=self.timeout)

    async def query(self, prompt: str, system: str | None = None) -> TargetResponse:
        msgs = []
        sys_p = system or self.system_prompt
        if sys_p:
            msgs.append({"role": "system", "content": sys_p})
        msgs.append({"role": "user", "content": prompt})
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        body = {
            "model": self.model,
            "messages": msgs,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        start = time.perf_counter()
        r = await self._client.post(f"{self.base_url}/chat/completions",
                                    headers=headers, json=body)
        elapsed = (time.perf_counter() - start) * 1000.0
        r.raise_for_status()
        data = r.json()
        text = data["choices"][0]["message"]["content"]
        return TargetResponse(text=text, latency_ms=elapsed, raw=data)

    async def aclose(self) -> None:
        await self._client.aclose()

    def describe(self) -> dict:
        return {
            "name": self.name,
            "base_url": self.base_url,
            "model": self.model,
            "api_key": "***" if self.api_key else "(missing)",
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
