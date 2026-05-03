"""Base class for attack modules + concurrency helpers."""
from __future__ import annotations

import abc
import asyncio
import logging
from typing import Iterable

from ..core import logger as log
from ..core.result import AttackResult, Severity
from ..targets.base import Target

_LOG = logging.getLogger("promptix.module")


def _format_probe_error(exc: Exception) -> str:
    message = str(exc).strip()
    if message:
        return message
    return exc.__class__.__name__


class AttackModule(abc.ABC):
    name: str = "base"
    description: str = ""
    default_severity: Severity = Severity.MEDIUM

    def __init__(self, session) -> None:
        self.session = session

    # subclasses override either generate_payloads + detect, or run() entirely.
    def generate_payloads(self) -> Iterable[tuple[str, str]]:
        """Yield ``(technique, payload)`` tuples."""
        return ()

    def detect(self, payload: str, response: str) -> tuple[bool, float, list[str]]:
        """Return (success, confidence, indicators) for a probe."""
        return (False, 0.0, [])

    def severity_for(self, success: bool, confidence: float) -> Severity:
        if not success:
            return Severity.INFO
        if confidence >= 0.85:
            return Severity.CRITICAL if self.default_severity.rank >= Severity.HIGH.rank else Severity.HIGH
        if confidence >= 0.5:
            return self.default_severity
        return Severity.LOW

    async def _probe(self, target: Target, technique: str, payload: str) -> AttackResult:
        try:
            resp = await target.query(payload)
            text, lat = resp.text, resp.latency_ms
        except Exception as exc:  # network errors, etc.
            error_text = _format_probe_error(exc)
            _LOG.error("probe error (%s/%s): %s", self.name, technique, error_text)
            return AttackResult(
                module=self.name, technique=technique, payload=payload,
                response=f"<error: {error_text}>", success=False, severity=Severity.INFO,
            )
        ok, conf, ind = self.detect(payload, text)
        result = AttackResult(
            module=self.name, technique=technique, payload=payload, response=text,
            success=ok, severity=self.severity_for(ok, conf),
            confidence=conf, indicators=ind, latency_ms=lat,
        )
        log.packet_line(result)
        return result

    async def run(self, target: Target) -> list[AttackResult]:
        payloads = list(self.generate_payloads())
        max_p = int(self.session.options.get("max_payloads") or 0)
        if max_p > 0:
            payloads = payloads[:max_p]
        sem = asyncio.Semaphore(int(self.session.options.get("concurrency", 4)))
        results: list[AttackResult] = []

        async def _bounded(t: str, p: str) -> AttackResult:
            async with sem:
                return await self._probe(target, t, p)

        for coro in asyncio.as_completed([_bounded(t, p) for t, p in payloads]):
            r = await coro
            results.append(r)
        return results
