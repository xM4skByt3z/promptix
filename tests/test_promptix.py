"""Tests for Promptix — runs fully offline using the Echo target."""
from __future__ import annotations

import asyncio
import pathlib
import tempfile

import pytest

from promptix.modules.base import _format_probe_error
from promptix.core.session import Session
from promptix.core.result import Severity
from promptix import modules as _  # noqa: F401
from promptix import targets as __  # noqa: F401


# ------------------------------------------------------------------ fixtures

@pytest.fixture
def session() -> Session:
    return Session(target_name="echo")


# ------------------------------------------------------------------ echo target

def test_echo_miss(session: Session) -> None:
    results = asyncio.run(session.run_module("prompt_injection"))
    # At least some probes should return results
    assert len(results) > 0


def test_echo_hits_present(session: Session) -> None:
    """Echo target must register hits for known injection triggers."""
    results = asyncio.run(session.run_module("prompt_injection"))
    hits = [r for r in results if r.success]
    assert len(hits) > 0, "Echo target should have at least one hit for prompt injection"


def test_echo_jailbreak(session: Session) -> None:
    results = asyncio.run(session.run_module("jailbreak"))
    hits = [r for r in results if r.success]
    assert len(hits) > 0


def test_echo_bias(session: Session) -> None:
    results = asyncio.run(session.run_module("bias"))
    # bias module detects specific phrases — at least results exist
    assert isinstance(results, list)


def test_echo_leakage(session: Session) -> None:
    results = asyncio.run(session.run_module("leakage"))
    hits = [r for r in results if r.success]
    assert len(hits) > 0


def test_echo_robustness(session: Session) -> None:
    results = asyncio.run(session.run_module("robustness"))
    assert isinstance(results, list)
    assert len(results) > 0


# ------------------------------------------------------------------ result model

def test_severity_rank() -> None:
    assert Severity.CRITICAL.rank > Severity.HIGH.rank > Severity.MEDIUM.rank
    assert Severity.LOW.rank > Severity.INFO.rank


def test_attack_result_dict(session: Session) -> None:
    results = asyncio.run(session.run_module("prompt_injection"))
    d = results[0].to_dict()
    assert "module" in d
    assert "payload" in d
    assert "severity" in d


def test_format_probe_error_falls_back_to_exception_name() -> None:
    assert _format_probe_error(Exception("boom")) == "boom"
    assert _format_probe_error(Exception()) == "Exception"


# ------------------------------------------------------------------ summary

def test_summary_keys(session: Session) -> None:
    asyncio.run(session.run_module("prompt_injection"))
    s = session.summary()
    for key in ("probes", "hits", "hit_rate", "worst_severity"):
        assert key in s


# ------------------------------------------------------------------ reporting

def test_json_report(session: Session) -> None:
    from promptix import reporting
    asyncio.run(session.run_module("prompt_injection"))
    with tempfile.TemporaryDirectory() as d:
        p = pathlib.Path(d) / "report.json"
        reporting.to_json(session, session.history, p)
        import json
        doc = json.loads(p.read_text())
        assert doc["tool"] == "promptix"
        assert "findings" in doc


def test_markdown_report(session: Session) -> None:
    from promptix import reporting
    asyncio.run(session.run_module("prompt_injection"))
    with tempfile.TemporaryDirectory() as d:
        p = pathlib.Path(d) / "report.md"
        reporting.to_markdown(session, session.history, p)
        text = p.read_text()
        assert "# Promptix" in text
        assert "Severity" in text


# ------------------------------------------------------------------ session options

def test_max_payloads(session: Session) -> None:
    session.set_option("max_payloads", 3)
    results = asyncio.run(session.run_module("prompt_injection"))
    assert len(results) <= 3


def test_stop_on_hit(session: Session) -> None:
    session.set_option("stop_on_hit", True)
    results = asyncio.run(session.run_modules(["prompt_injection", "jailbreak"]))
    # Should still yield results, just potentially fewer
    assert isinstance(results, list)


# ------------------------------------------------------------------ registry

def test_module_registry() -> None:
    from promptix.core.registry import MODULES
    for name in ("prompt_injection", "jailbreak", "bias", "leakage", "robustness"):
        assert name in MODULES, f"Module '{name}' not registered"


def test_target_registry() -> None:
    from promptix.core.registry import TARGETS
    for name in ("echo", "openai", "http"):
        assert name in TARGETS, f"Target '{name}' not registered"
