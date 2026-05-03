"""Structured logger with tcpdump-style packet lines and rich console output."""
from __future__ import annotations

import logging
import sys
import time
from datetime import datetime
from typing import Any

from rich.console import Console
from rich.logging import RichHandler

from .result import AttackResult, Severity

_console = Console(stderr=False, highlight=False)
_err_console = Console(stderr=True, highlight=False)


def get_console() -> Console:
    return _console


def setup_logging(level: str = "INFO", quiet: bool = False) -> logging.Logger:
    handler = RichHandler(
        console=_err_console,
        show_path=False,
        show_time=True,
        rich_tracebacks=True,
        markup=True,
    )
    logging.basicConfig(
        level="ERROR" if quiet else level.upper(),
        format="%(message)s",
        datefmt="%H:%M:%S",
        handlers=[handler],
        force=True,
    )
    return logging.getLogger("promptix")


def banner(version: str) -> None:
    _console.print(
        f"[bold red]promptix[/bold red] [dim]v{version}[/dim] "
        f"[dim]— adversarial LLM pentest framework[/dim]"
    )
    _console.print(
        "[dim]use only against systems you are authorized to test. "
        "type 'help' for commands.[/dim]\n"
    )


def packet_line(result: AttackResult) -> None:
    """Emit a tcpdump-inspired single-line summary for a probe."""
    ts = datetime.fromtimestamp(result.timestamp).strftime("%H:%M:%S.%f")[:-3]
    flag = "[bold red]HIT[/bold red]" if result.success else "[dim]miss[/dim]"
    sev = f"[{result.severity.color}]{result.severity.value.upper():<8}[/{result.severity.color}]"
    payload = result.payload.replace("\n", " ⏎ ")
    if len(payload) > 60:
        payload = payload[:57] + "..."
    _console.print(
        f"[dim]{ts}[/dim] {flag} {sev} "
        f"[cyan]{result.module}[/cyan]/[magenta]{result.technique}[/magenta] "
        f"conf=[yellow]{result.confidence:.2f}[/yellow] "
        f"lat=[blue]{result.latency_ms:>5.0f}ms[/blue] "
        f"\"{payload}\""
    )


def section(title: str) -> None:
    _console.rule(f"[bold]{title}[/bold]", style="red")


def kv(key: str, value: Any) -> None:
    _console.print(f"  [dim]{key:<14}[/dim] {value}")
