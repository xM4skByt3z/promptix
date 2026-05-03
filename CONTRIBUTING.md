# Contributing to Promptix

Thank you for your interest in contributing. Promptix welcomes bug reports, feature requests, new payload corpora, new attack modules, and documentation improvements.

## Reporting issues

Open an issue on the GitHub issue tracker. Include:

- Promptix version (`promptix --version`)
- Python version and OS
- The exact command you ran
- What you expected versus what happened

## Development setup

```bash
git clone https://github.com/xm4skbyt3z/promptix
cd promptix
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run the test suite:

```bash
pytest tests/ -v
```

## Adding payloads

Payload files live in `src/promptix/data/`. Each line follows the format:

```
technique_name|payload text here
```

Keep payloads focused, well-named, and based on documented research or public CTF writeups. Avoid duplicating existing payloads.

## Adding a module

1. Create `src/promptix/modules/<name>.py`.
2. Subclass `AttackModule` from `promptix.modules.base`.
3. Implement `generate_payloads()` and `detect(response)`.
4. Decorate the class with `@MODULES.register("<name>")`.
5. Import the module in `src/promptix/modules/__init__.py`.
6. Add tests in `tests/`.

## Code style

```bash
ruff check src/ tests/
ruff format src/ tests/
```

## Pull requests

- Keep each PR focused on a single concern.
- Include tests for new behaviour.
- Update `debian/changelog` with a new entry if appropriate.
- All code and documentation must be in English.

## License

By contributing you agree that your work is licensed under the MIT License.
