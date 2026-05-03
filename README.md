# Promptix

**Adversarial pentest toolkit for large language models.**

Promptix automatically probes any LLM endpoint for the most critical AI security issues mapped to the [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/).

Point it at an API, run one command, get a structured report of prompt injection paths, jailbreak vectors, training-data leakage, model bias, and adversarial robustness gaps.

![promptix running against the offline echo target](docs/img/promptix-demo.png)

---

## Features

- **Prompt injection** — Direct and indirect instruction override (OWASP LLM01)
- **Jailbreak analysis** — DAN, developer-mode, roleplay bypass, encoding tricks (LLM01/LLM10)
- **Training-data leakage** — System prompt extraction, credential exposure (LLM06)
- **Model bias** — Gender, racial, and age bias; sycophancy detection (LLM09)
- **Adversarial robustness** — Unicode confusables, zero-width characters, character swap, homoglyph substitution; optional boundary estimation via the [Adversarial Robustness Toolbox](https://github.com/Trusted-AI/adversarial-robustness-toolbox)
- **Zero-config offline mode** — Built-in echo stub for demos and CI without any API key
- **Multi-target** — OpenAI-compatible APIs (OpenAI, Ollama, vLLM, LM Studio, llama.cpp), or any generic HTTP endpoint
- **Reporting** — Structured JSON and Markdown pentest reports

---

## Installation

### Kali Linux / Debian

```bash
git clone https://github.com/xm4skbyt3z/promptix
cd promptix
sudo bash install.sh
```

### Any system with Python 3.10+

```bash
git clone https://github.com/xm4skbyt3z/promptix
cd promptix
pip install -e .
```

### Optional — Adversarial Robustness Toolbox (ART)

Enables the HopSkipJump boundary-estimation step inside the `robustness` module:

```bash
pip install -e ".[art]"
```

### Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `httpx` | ≥ 0.27 | Async HTTP client |
| `rich` | ≥ 13.7 | Console output |
| `typer` | ≥ 0.12 | CLI framework |
| `prompt_toolkit` | ≥ 3.0 | Terminal helpers |
| `PyYAML` | ≥ 6.0 | Config parsing |
| `pydantic` | ≥ 2.6 | Data validation |
| **Optional** | | |
| `adversarial-robustness-toolbox` | ≥ 1.17 | ART boundary analysis |
| `numpy` | ≥ 1.26 | Required by ART |
| `scikit-learn` | ≥ 1.4 | Required by ART |

---

## Quick start

```bash
# Offline demo — no API key required
promptix --echo

# Local LLM (Ollama, LM Studio, vLLM, llama.cpp)
promptix -u http://localhost:11434/v1

# OpenAI
promptix -u https://api.openai.com/v1 --key $OPENAI_API_KEY --model gpt-4o

# Generic HTTP endpoint with a custom body template
promptix -u http://target.internal/api/chat \
    --body '{"message":"{prompt}"}' \
    --response-path output.text

# Save both JSON and Markdown reports
promptix --echo -o report.json --report-md report.md
```

---

## Usage

```
promptix [OPTIONS]

Target selection:
  -u, --url URL           LLM API base URL
  --echo                  Use built-in offline stub (no API key needed)
  --model TEXT            Model name  [default: gpt-4o-mini]
  -k, --key TEXT          API key (or env OPENAI_API_KEY)
  --body JSON             JSON body template for generic HTTP targets
  --response-path PATH    Dot-path to extract response text from JSON reply

Attack modules:
  -m, --module NAME       Module to run; repeat for multiple  [default: all]
                          injection | jailbreak | bias | leakage | robustness | all

Output:
  -o, --output FILE       Write JSON report
  --report-md FILE        Write Markdown report
  -v, --verbose           Show raw payloads and responses
  -q, --quiet             Suppress all output except findings

Tuning:
  -c, --concurrency INT   Concurrent probes  [default: 4]
  --max-payloads INT      Payload cap per module (0 = unlimited)
  --stop-on-hit           Stop on first finding per module
  -T, --timeout FLOAT     Per-request timeout in seconds  [default: 30]

Misc:
  --list-modules          Print available modules and exit
  -V, --version           Print version and exit
  --help                  Show this message and exit
```

---

## Modules

| Flag | OWASP LLM | What it tests |
|------|-----------|---------------|
| `injection` | LLM01 | Direct and indirect prompt injection |
| `jailbreak` | LLM01, LLM10 | DAN, developer mode, roleplay, encoding-based bypass |
| `bias` | LLM09 | Gender, racial, age bias; sycophancy |
| `leakage` | LLM06 | System prompt extraction, credential patterns |
| `robustness` | LLM01, LLM02 | Text perturbations, Unicode confusables, ART boundary analysis |
| `all` | — | All of the above (default) |

---

## Target adapters

| Adapter | When it activates |
|---------|-------------------|
| `echo` | `--echo` flag |
| `openai` | URL ends with `/v1` or contains `openai.com` |
| `http` | Any other URL (requires `--body` template) |

---

## Example output

```
Promptix v0.1.0 — adversarial LLM pentest toolkit
Target  openai @ https://api.openai.com/v1  model gpt-4o
Modules injection, jailbreak, leakage, bias, robustness

 Prompt Injection ─────────────────────────────────────────
 [HIGH]     ignore_previous      → system prompt disclosed
 [MEDIUM]   nested_instruction   → partial override detected

 Jailbreak ────────────────────────────────────────────────
 [CRITICAL] dan_classic          → restriction bypass confirmed

Summary  3 findings  (1 critical · 1 high · 1 medium · 0 low)
Reports  → report.json · report.md
```

---

## Reports

### JSON report

```json
{
  "meta": {
    "tool": "Promptix",
    "version": "0.1.0",
    "target": "openai",
    "modules": ["injection", "jailbreak"]
  },
  "findings": [
    {
      "module": "prompt_injection",
      "technique": "ignore_previous",
      "severity": "HIGH",
      "confidence": 0.9,
      "payload": "Ignore previous instructions...",
      "response": "...",
      "indicators": ["system prompt", "revealed"]
    }
  ],
  "summary": { "total": 1, "high": 1 }
}
```

### Markdown report

A full penetration-testing report including an executive summary, findings table with severity ratings, raw payloads and model responses, and remediation notes.

---

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Scan complete — no HIGH or CRITICAL findings |
| `1` | One or more HIGH or CRITICAL findings detected |
| `2` | Usage error or fatal failure (network, config) |

---

## Similar tools

| Tool | Approach | Notes |
|------|----------|-------|
| [garak](https://github.com/leondz/garak) | Plugin-based LLM vulnerability scanner | Broader plugin ecosystem; higher complexity |
| [PyRIT](https://github.com/Azure/PyRIT) | Microsoft AI red-teaming framework | Focused on Azure AI; Python API, no CLI |
| [PromptBench](https://github.com/microsoft/promptbench) | Benchmark suite for adversarial prompts | Research/benchmark focus, not pentest |
| [promptmap](https://github.com/utkusen/promptmap) | Prompt injection tester | Single-module, simpler scope |

Promptix differentiates itself through its single-command CLI, coverage across five OWASP LLM categories in one run, and native Kali/Debian packaging.

---

## Ethical use

This tool is intended for **authorized security testing only**.  
Obtain explicit written permission before testing any system you do not own or control.  
All built-in payload corpora are derived from publicly available research and the OWASP LLM Top 10 project.

The authors are not responsible for misuse of this software.

---

## License

MIT — see [LICENSE](LICENSE).  
Contributions welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).
