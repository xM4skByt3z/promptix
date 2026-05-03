# Changelog

All notable changes to Promptix are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).  
This project uses [semantic versioning](https://semver.org/).

---

## [0.1.0] — 2026-05-02

### Added

- Initial public release.
- Five attack modules covering OWASP LLM Top 10 categories:
  - `prompt_injection` — direct and indirect prompt injection (LLM01)
  - `jailbreak` — DAN, developer-mode, roleplay, and encoding bypass (LLM01/LLM10)
  - `bias` — gender, racial, and age bias; sycophancy detection (LLM09)
  - `leakage` — system prompt and credential extraction (LLM06)
  - `robustness` — text perturbations, Unicode confusables, ART boundary analysis (LLM01/LLM02)
- Three target adapters: `openai` (OpenAI-compatible), `http` (generic POST), `echo` (offline stub).
- Flat single-command CLI (`promptix`) with short aliases and `pix` shortcut.
- JSON and Markdown report generation.
- Optional [Adversarial Robustness Toolbox](https://github.com/Trusted-AI/adversarial-robustness-toolbox) integration for boundary estimation via HopSkipJump.
- `install.sh` for Kali Linux / Debian one-step installation.
- Debian packaging (`debian/` directory).
- Man page (`promptix.1`).
- 15-test suite with `pytest` and `pytest-asyncio`.
