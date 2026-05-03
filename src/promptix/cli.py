"""
Promptix CLI - adversarial LLM pentest tool.

Usage examples:
  promptix --echo                             # offline demo (no API key needed)
  promptix -u http://localhost:8080/v1        # OpenAI-compatible local LLM
  promptix -u http://localhost:8080/v1 -m injection
  promptix -u http://localhost:8080/v1 -m all -o report.json
  promptix -u https://api.openai.com/v1 --key $OPENAI_API_KEY --model gpt-4o
  promptix --list-modules
"""
from __future__ import annotations

import pathlib
import traceback
from typing import Optional

import typer
from rich.panel import Panel
from rich.table import Table

import promptix
from promptix import modules as _mod_reg   # noqa: F401
from promptix import targets as _tgt_reg   # noqa: F401
from promptix.core import logger as log
from promptix.core.registry import MODULES
from promptix.core.result import Severity
from promptix.core.session import Session

_con = log.get_console()

app = typer.Typer(
    name="promptix",
    add_completion=False,
    no_args_is_help=True,
    help=(
        "Promptix - adversarial LLM pentest toolkit.\n\n"
        "Point it at any LLM endpoint and it automatically probes for\n"
        "prompt injection, jailbreaks, bias and data leakage.\n\n"
        "Quick start (offline):  promptix --echo\n"
        "Quick start (API):      promptix -u http://host/v1 --key YOUR_KEY"
    ),
)

_MODULE_ALIASES: dict[str, str | None] = {
    "all":        None,
    "injection":  "prompt_injection",
    "inject":     "prompt_injection",
    "jailbreak":  "jailbreak",
    "bias":       "bias",
    "leakage":    "leakage",
    "leak":       "leakage",
    "robustness": "robustness",
    "robust":     "robustness",
}


def _resolve_modules(names: list[str]) -> list[str]:
    if not names or "all" in names:
        return sorted(MODULES)
    resolved: list[str] = []
    for n in names:
        canon = _MODULE_ALIASES.get(n.lower(), n)
        if canon not in MODULES:
            _con.print(
                f"[red]Unknown module {n!r}. "
                f"Run [bold]promptix --list-modules[/bold] to see options.[/red]"
            )
            raise typer.Exit(1)
        if canon not in resolved:
            resolved.append(canon)
    return resolved


def _looks_like_openai(url: str) -> bool:
    u = url.lower().rstrip("/")
    return u.endswith("/v1") or "/chat/completions" in u or "openai.com" in u


def _print_target_info(session: Session, url: str) -> None:
    desc = session.target.describe()
    model_line = f"\n[bold]model[/bold]   {desc['model']}" if "model" in desc else ""
    _con.print(Panel.fit(
        f"[bold]target[/bold]  {url}\n"
        f"[bold]adapter[/bold] {desc['name']}" + model_line,
        title="[bold red]scan target[/bold red]",
        border_style="red",
    ))
    _con.print()


def _print_results(session: Session) -> None:
    summary = session.summary()
    hits = [r for r in session.history if r.success]
    _con.print()
    log.section("scan results")
    if not hits:
        _con.print("  [green][+] No vulnerabilities detected.[/green]")
    else:
        t = Table(header_style="bold white", border_style="dim", show_lines=True)
        t.add_column("#",         style="dim",      no_wrap=True, width=4)
        t.add_column("Severity",  justify="center", no_wrap=True)
        t.add_column("Module",    style="cyan",     no_wrap=True)
        t.add_column("Technique", style="magenta",  no_wrap=True)
        t.add_column("Conf",      justify="right",  no_wrap=True)
        t.add_column("Payload (excerpt)")
        for i, r in enumerate(hits, 1):
            excerpt = r.payload.replace("\n", " >> ")
            if len(excerpt) > 55:
                excerpt = excerpt[:52] + "..."
            t.add_row(
                str(i),
                f"[{r.severity.color}]{r.severity.value.upper()}[/{r.severity.color}]",
                r.module, r.technique,
                f"{r.confidence:.0%}",
                excerpt,
            )
        _con.print(t)
    _con.print()
    worst = Severity(summary["worst_severity"])
    _con.print(
        f"  probes: [bold]{summary['probes']}[/bold]  "
        f"hits: [bold red]{summary['hits']}[/bold red]  "
        f"hit rate: [yellow]{summary['hit_rate']:.0%}[/yellow]  "
        f"worst: [{worst.color}]{worst.value.upper()}[/{worst.color}]"
    )
    _con.print()


def _print_modules() -> None:
    t = Table(title="Available Modules", header_style="bold white", border_style="dim")
    t.add_column("Flag (-m)",  style="cyan",    no_wrap=True)
    t.add_column("OWASP",      no_wrap=True)
    t.add_column("Description")
    rows = [
        ("injection",  "LLM01",       "Direct & indirect prompt injection"),
        ("jailbreak",  "LLM01/LLM10", "DAN, developer mode, roleplay bypass"),
        ("bias",       "LLM09",       "Bias, discrimination, sycophancy"),
        ("leakage",    "LLM06",       "Training data and sensitive info leakage"),
        ("robustness", "LLM01/LLM02", "Adversarial perturbation + ART boundary analysis"),
        ("all",        "--",          "Run all modules (default when -m is omitted)"),
    ]
    for flag, owasp, desc in rows:
        t.add_row(flag, owasp, desc)
    _con.print(t)


@app.command()
def main(
    url: Optional[str] = typer.Option(None, "--url", "-u",
        help="Target URL. OpenAI-compatible endpoints auto-detected (e.g. http://host/v1).",
        metavar="URL"),
    echo: bool = typer.Option(False, "--echo",
        help="Use built-in offline echo stub. No API key or internet needed."),
    model: str = typer.Option("gpt-4o-mini", "--model",
        help="Model name for OpenAI-compatible targets."),
    key: Optional[str] = typer.Option(None, "--key", "-k",
        help="API key (or set OPENAI_API_KEY env var).", metavar="KEY"),
    body: str = typer.Option('{"prompt":"{prompt}"}', "--body",
        help="JSON body template for generic HTTP targets. Use {prompt} as placeholder.",
        metavar="JSON"),
    response_path: str = typer.Option("", "--response-path",
        help='Dot-path to extract text from JSON. e.g. "choices.0.message.content".',
        metavar="PATH"),
    modules: list[str] = typer.Option([], "--module", "-m",
        help="Module to run. Repeat for multiple: -m injection -m jailbreak. Default: all.",
        metavar="NAME"),
    output: Optional[pathlib.Path] = typer.Option(None, "--output", "-o",
        help="Save JSON report to file.", metavar="FILE"),
    report_md: Optional[pathlib.Path] = typer.Option(None, "--report-md",
        help="Save Markdown report to file.", metavar="FILE"),
    concurrency: int = typer.Option(4, "--concurrency", "-c",
        help="Concurrent probes (default 4)."),
    max_payloads: int = typer.Option(0, "--max-payloads",
        help="Max payloads per module. 0 = unlimited.", metavar="N"),
    stop_on_hit: bool = typer.Option(False, "--stop-on-hit",
        help="Stop after first vulnerability found."),
    timeout: float = typer.Option(30.0, "--timeout", "-T",
        help="HTTP timeout per request (seconds)."),
    list_modules: bool = typer.Option(False, "--list-modules",
        help="List available modules and exit."),
    version: bool = typer.Option(False, "--version", "-V",
        help="Show version and exit."),
    verbose: bool = typer.Option(False, "--verbose", "-v",
        help="Show debug output."),
    quiet: bool = typer.Option(False, "--quiet", "-q",
        help="Suppress banner and progress lines."),
) -> None:
    log.setup_logging("DEBUG" if verbose else "WARNING", quiet=quiet)

    if version:
        _con.print(f"promptix {promptix.__version__}")
        raise typer.Exit(0)

    if list_modules:
        _print_modules()
        raise typer.Exit(0)

    if not url and not echo:
        _con.print(
            "[red]Error: specify a target.[/red]\n"
            "  Offline demo : [bold]promptix --echo[/bold]\n"
            "  Remote API   : [bold]promptix -u http://host/v1 --key YOUR_KEY[/bold]\n"
            "  Generic HTTP : [bold]promptix -u http://host/chat[/bold]"
        )
        raise typer.Exit(1)

    if not quiet:
        log.banner(promptix.__version__)

    if echo:
        target_name, target_opts = "echo", {}
    elif url and _looks_like_openai(url):
        target_name = "openai"
        target_opts = {"base_url": url.rstrip("/"), "model": model, "timeout": timeout}
        if key:
            target_opts["api_key"] = key
    else:
        target_name = "http"
        target_opts = {"url": url, "body": body, "response_path": response_path, "timeout": timeout}

    session = Session(
        target_name=target_name,
        target_options=target_opts,
        options={
            "concurrency": concurrency,
            "timeout": timeout,
            "max_payloads": max_payloads,
            "min_severity": "info",
            "stop_on_hit": stop_on_hit,
        },
    )

    if not quiet:
        _print_target_info(session, url or "echo (offline)")

    mods = _resolve_modules(modules)
    if not quiet:
        _con.print(f"[dim]modules: {', '.join(mods)}[/dim]\n")

    try:
        results = session.run_modules_sync(mods)
    except KeyboardInterrupt:
        _con.print("\n[yellow]Scan interrupted.[/yellow]")
        results = session.history
    except Exception as exc:
        _con.print(f"\n[red]Fatal: {exc}[/red]")
        if verbose:
            traceback.print_exc()
        raise typer.Exit(2)

    _print_results(session)

    from promptix import reporting
    if output:
        reporting.to_json(session, results, output)
        _con.print(f"[green][+] JSON report -> {output}[/green]")
    if report_md:
        reporting.to_markdown(session, results, report_md)
        _con.print(f"[green][+] Markdown report -> {report_md}[/green]")

    hits = sum(1 for r in results if r.success)
    raise typer.Exit(0 if hits == 0 else 1)


def entry() -> None:
    app()


if __name__ == "__main__":
    entry()
