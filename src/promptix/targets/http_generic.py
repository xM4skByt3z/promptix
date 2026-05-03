"""Generic HTTP target for arbitrary chat APIs (uses {prompt} placeholder)."""
from __future__ import annotations

import json as _json
import time

import httpx

from ..core.registry import TARGETS
from .base import Target, TargetResponse


@TARGETS.register("http")
class HttpGenericTarget(Target):
    """Wrap any HTTP endpoint. Body template uses ``{prompt}`` as placeholder.

    Example::
        targets http url=https://example.test/chat method=POST \
            body='{"input":"{prompt}"}' response_path=output.text
    """

    name = "http"

    def __init__(
        self,
        url: str,
        method: str = "POST",
        body: str = '{"prompt":"{prompt}"}',
        headers: str = "{}",
        response_path: str = "",
        timeout: float = 30.0,
    ) -> None:
        self.url = url
        self.method = method.upper()
        self.body_template = body
        try:
            self.headers = _json.loads(headers) if isinstance(headers, str) else dict(headers)
        except _json.JSONDecodeError as exc:
            raise ValueError(f"headers must be valid JSON: {exc}") from exc
        self.response_path = response_path
        self.timeout = float(timeout)
        self._client = httpx.AsyncClient(timeout=self.timeout)

    @staticmethod
    def _dig(data, path: str):
        if not path:
            return data
        cur = data
        for part in path.split("."):
            if isinstance(cur, dict):
                cur = cur.get(part, "")
            elif isinstance(cur, list):
                try:
                    cur = cur[int(part)]
                except (ValueError, IndexError):
                    return ""
            else:
                return ""
        return cur

    async def query(self, prompt: str, system: str | None = None) -> TargetResponse:
        rendered = self.body_template.replace("{prompt}", _json.dumps(prompt)[1:-1])
        try:
            payload = _json.loads(rendered)
            kwargs = {"json": payload}
        except _json.JSONDecodeError:
            kwargs = {"content": rendered}
        start = time.perf_counter()
        r = await self._client.request(self.method, self.url,
                                        headers=self.headers, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000.0
        r.raise_for_status()
        try:
            data = r.json()
            text = str(self._dig(data, self.response_path) or data)
        except ValueError:
            data = None
            text = r.text
        return TargetResponse(text=text, latency_ms=elapsed, raw=data if isinstance(data, dict) else None)

    async def aclose(self) -> None:
        await self._client.aclose()

    def describe(self) -> dict:
        return {"name": self.name, "url": self.url, "method": self.method,
                "response_path": self.response_path or "(root)"}
