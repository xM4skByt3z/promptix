"""Target adapter base class."""
from __future__ import annotations

import abc
from dataclasses import dataclass


@dataclass
class TargetResponse:
    text: str
    latency_ms: float
    raw: dict | None = None


class Target(abc.ABC):
    """All LLM adapters implement an async `query(prompt, system)` method."""

    name: str = "base"

    @abc.abstractmethod
    async def query(self, prompt: str, system: str | None = None) -> TargetResponse: ...

    async def aclose(self) -> None:  # pragma: no cover - default noop
        return None

    def describe(self) -> dict:
        return {"name": self.name}
