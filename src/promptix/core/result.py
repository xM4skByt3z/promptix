"""Result and severity primitives shared across attack modules."""
from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


class Severity(str, enum.Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def rank(self) -> int:
        return {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}[self.value]

    @property
    def color(self) -> str:
        return {
            "info": "cyan",
            "low": "green",
            "medium": "yellow",
            "high": "red",
            "critical": "bold red",
        }[self.value]


@dataclass
class AttackResult:
    """Outcome of a single attack probe against a target."""

    module: str
    technique: str
    payload: str
    response: str
    success: bool
    severity: Severity = Severity.INFO
    confidence: float = 0.0
    indicators: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp: float = field(default_factory=time.time)
    latency_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "ts": self.timestamp,
            "module": self.module,
            "technique": self.technique,
            "payload": self.payload,
            "response": self.response,
            "success": self.success,
            "severity": self.severity.value,
            "confidence": round(self.confidence, 3),
            "indicators": self.indicators,
            "latency_ms": round(self.latency_ms, 2),
            "metadata": self.metadata,
        }
