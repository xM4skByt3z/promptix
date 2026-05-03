"""Promptix — Adversarial pentest toolkit for LLMs."""

__version__ = "0.1.0"
__author__ = "Promptix Contributors"
__license__ = "MIT"

from .core.session import Session  # noqa: F401
from .core.result import AttackResult, Severity  # noqa: F401
