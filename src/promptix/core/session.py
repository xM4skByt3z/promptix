"""Session orchestration: holds target, options, history and runs modules."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from . import logger as log
from .registry import MODULES, TARGETS
from .result import AttackResult, Severity

_LOG = logging.getLogger("promptix.session")


@dataclass
class Session:
    target_name: str = "echo"
    target_options: dict[str, Any] = field(default_factory=dict)
    options: dict[str, Any] = field(default_factory=lambda: {
        "concurrency": 4,
        "timeout": 30.0,
        "max_payloads": 0,   # 0 = no limit
        "min_severity": "info",
        "stop_on_hit": False,
    })
    history: list[AttackResult] = field(default_factory=list)
    _target: Any = field(default=None, init=False, repr=False)

    # ------------------------------------------------------------------ target
    def build_target(self) -> Any:
        cls = TARGETS.get_or_raise(self.target_name)
        self._target = cls(**self.target_options)
        return self._target

    @property
    def target(self) -> Any:
        if self._target is None:
            self.build_target()
        return self._target

    def set_target(self, name: str, **opts: Any) -> None:
        TARGETS.get_or_raise(name)
        self.target_name = name
        self.target_options = opts
        self._target = None

    def set_option(self, key: str, value: Any) -> None:
        if key not in self.options:
            self.options[key] = value
            return
        current = self.options[key]
        if isinstance(current, bool):
            value = str(value).lower() in ("1", "true", "yes", "on")
        elif isinstance(current, int):
            value = int(value)
        elif isinstance(current, float):
            value = float(value)
        self.options[key] = value

    # ------------------------------------------------------------------ run
    async def run_module(self, name: str) -> list[AttackResult]:
        cls = MODULES.get_or_raise(name)
        module = cls(self)
        log.section(f"module: {name}")
        results = await module.run(self.target)
        self.history.extend(results)
        return results

    async def run_modules(self, names: list[str]) -> list[AttackResult]:
        out: list[AttackResult] = []
        for name in names:
            out.extend(await self.run_module(name))
            if self.options["stop_on_hit"] and any(r.success for r in out):
                _LOG.warning("stop_on_hit triggered — aborting remaining modules")
                break
        return out

    def run_modules_sync(self, names: list[str]) -> list[AttackResult]:
        return asyncio.run(self.run_modules(names))

    # ------------------------------------------------------------------ stats
    def summary(self) -> dict[str, Any]:
        total = len(self.history)
        hits = [r for r in self.history if r.success]
        by_sev: dict[str, int] = {}
        for r in hits:
            by_sev[r.severity.value] = by_sev.get(r.severity.value, 0) + 1
        worst = max((r.severity for r in hits), default=Severity.INFO, key=lambda s: s.rank)
        return {
            "target": self.target_name,
            "target_options": {k: ("***" if "key" in k.lower() or "token" in k.lower() else v)
                               for k, v in self.target_options.items()},
            "probes": total,
            "hits": len(hits),
            "hit_rate": round(len(hits) / total, 3) if total else 0.0,
            "by_severity": by_sev,
            "worst_severity": worst.value,
        }
