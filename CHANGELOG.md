# Changelog

All notable changes to PyShield are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- `SEC001` — flag `eval()` / `exec()` on user-supplied input
- `PII001` — detect PII in function return values
- Per-file policy configuration via `.pyshield.toml`
- HTML report output
- Parallel file processing

---

## [0.1.0] — 2026-05-22

### Added
- **`engine/tracker.py`** — git-aware file discovery via `git diff HEAD` and `git ls-files --others`
- **`engine/parser.py`** — AST extraction of `FunctionDef` / `AsyncFunctionDef` metadata (name, lineno, params, annotations); strips `self` / `cls`
- **`engine/harvester.py`** — deterministic mutation arrays for `email`, `id/count/index`, `price/balance/amount`, and PII param names; UPPERCASE constant discovery from sibling files
- **`engine/compliance.py`** — **FIN001** static policy rule (float arithmetic on financial variables); offline SHA-256 validation seal with local JSON storage
- **`engine/runner.py`** — sandboxed mutation execution via `importlib` + `tempfile`; `sys.stdout` and root logger interception for PII leak detection; write-mode `open()` and subprocess mocking; circuit-breaker after 3 consecutive failures per (func, param, value) triple
- **`cli.py`** — `pyshield [files] [--format json|markdown]` entry point; per-file Provenance Ledger; exit code `0` / `1`; `--version` flag
- **`mcp_server.py`** — FastMCP stdio server exposing `run_shield_check(files)` tool with Markdown failure-contract output
- 41 unit tests across 5 modules (tracker, parser, harvester, compliance, runner)
- `pyproject.toml` with `hatchling` build backend, `uv` dev workflow, `ruff` + `mypy` tooling
- GitHub Actions CI workflow (lint → type check → test)

[Unreleased]: https://github.com/biswa-mohapatro/PySheild/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/biswa-mohapatro/PySheild/releases/tag/v0.1.0
