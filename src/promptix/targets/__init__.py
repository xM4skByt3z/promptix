"""Target adapters — each speaks to a specific LLM backend."""
from __future__ import annotations

from .base import Target, TargetResponse
from . import echo, openai_chat, http_generic  # noqa: F401  (registers via decorators)

__all__ = ["Target", "TargetResponse"]
