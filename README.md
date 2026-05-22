# PyShield

[![CI](https://github.com/biswa-mohapatro/PySheild/actions/workflows/ci.yml/badge.svg)](https://github.com/biswa-mohapatro/PySheild/actions/workflows/ci.yml)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Typed](https://img.shields.io/badge/typing-strict-brightgreen.svg)](pyshield/py.typed)

> **A zero-token, air-gapped, deterministic validation engine and MCP Skill Agent — built to partner with external AI coding agents (Claude Code, Cursor, GitHub Copilot) in a hybrid development lifecycle.**

---

## The Problem

Modern AI coding agents are powerful but probabilistic. They generate plausible code, not guaranteed-correct code. When they operate in a loop — generate → test → fix → generate — they need a grounding signal they can fully trust. A signal that is:

- **Deterministic** — same input, same result, every time
- **Fast** — no network calls, no token budgets, no LLM inference
- **Precise** — exact crash vectors, parameter values, and policy violations
- **Honest** — never guesses at fixes; only reports what it observed

**PyShield is that signal.**

It sits between your codebase and your AI agent. The agent writes code; PyShield runs the ground truth; PyShield hands the exact failure contract back to the agent. The agent uses its probabilistic intelligence to heal the code. Neither side tries to do the other's job.

---

## How It Works — The Hybrid Boundary

```
┌─────────────────────────────────────────────────────────────────┐
│                    Your Development Loop                         │
│                                                                  │
│   AI Agent (Claude / Cursor / Copilot)                          │
│       │ writes/edits Python code                                 │
│       ▼                                                          │
│   ┌────────────────────────────────────────────────────┐        │
│   │               PyShield  (deterministic)            │        │
│   │                                                    │        │
│   │  git diff  →  AST parse  →  Policy check (FIN001) │        │
│   │      ↓              ↓              ↓               │        │
│   │  Constants   Param classifier  SHA-256 seal        │        │
│   │  scanner     (email/id/money)                      │        │
│   │      ↓              ↓                              │        │
│   │  Sandboxed mutation tests + PII leak detection     │        │
│   │      ↓                                             │        │
│   │  Provenance Ledger (JSON / Markdown)               │        │
│   └───────────────────────┬────────────────────────────┘        │
│                           │ failure contract                     │
│                           ▼                                      │
│   AI Agent interprets exact errors → edits code → re-runs       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

PyShield enforces the **hybrid boundary rule**: zero probabilistic components inside (no local LLMs, no embeddings, no heuristic guesswork). The engine speaks only in hard runtime truths — crashes, exceptions, policy violations, PII leaks. The AI agent does the interpretation.

---

## Features

| Capability | Description |
|---|---|
| **Git-aware** | Automatically detects changed / untracked `.py` files via `git diff` |
| **AST parsing** | Extracts function signatures, parameter names, and type annotations |
| **Mutation testing** | Injects boundary values per parameter type (`email`, `id`, `price`, …) |
| **Constants discovery** | Scans sibling files for `UPPERCASE` constants and injects them as mutations |
| **FIN001 policy** | Flags `price` / `balance` / `amount` variables used in float arithmetic (must use `decimal.Decimal`) |
| **PII/PHI fuzzer** | Seeds `ssn`, `patient_id`, `credit_card` params with realistic mock data; intercepts `stdout` + logging for unmasked leaks |
| **Sandboxing** | Mocks all `open("w")` and `subprocess` calls during test execution |
| **Circuit-breaker** | Stops retrying after 3 consecutive failures on the same (func, param, value) triple |
| **SHA-256 seal** | Cryptographically attests validated files with a local `.pyshield/*.seal.json` |
| **MCP tool** | `run_shield_check()` exposes the full pipeline as an MCP tool over stdio |
| **CLI** | `pyshield [files] [--format json\|markdown]` — exits `0` on pass, `1` on failure |

---

## Installation

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

---

### Install as a tool with uv (recommended for agentic CLI / IDE use)

Install once — both the `pyshield` CLI and `pyshield-mcp` server are added to your PATH:

```bash
uv tool install pyshield
```

Run without installing at all (perfect for CI or one-off checks):

```bash
uvx pyshield [files...]
uvx --from pyshield pyshield-mcp   # launch the MCP server
```

Install a specific version:

```bash
uv tool install pyshield==0.1.0
```

### Install from PyPI with pip

```bash
pip install pyshield
```

### Install directly from GitHub (before first PyPI release)

```bash
uv tool install git+https://github.com/biswa-mohapatro/PySheild
# or
pip install git+https://github.com/biswa-mohapatro/PySheild.git
```

### From source (development)

```bash
git clone https://github.com/biswa-mohapatro/PySheild.git
cd pyshield
uv sync
uv run pyshield --version
```

---

## Quick Start — CLI

```bash
# Validate all git-changed Python files in the current repo
pyshield

# Validate specific files
pyshield src/payments.py src/orders.py

# Output machine-readable JSON (for CI pipelines)
pyshield --format json

# Exit code: 0 = all validations passed, 1 = failures detected
pyshield src/payments.py || echo "Validation failed — check output"
```

### Example output

```
# PyShield Provenance Ledger — [FAILED]

**Timestamp:** 2026-05-22T12:28:24+00:00
**Git Files Scanned:** 1

## `src/payments.py`

### Policy Violations (FIN001)
- `FIN001` line 27 in `calculate_total`: Financial variable 'price' used in float arithmetic. Use decimal.Decimal.

#### `calculate_total` (line 22)
  - [FAIL] param=`price` value=`0.0`
    ```
    TypeError: unsupported operand type(s) for *: 'float' and 'NoneType'
    ```
  - [FAIL] param=`price` value=`nan`
    ...

#### `display_patient_record` (line 50)
  - [PII LEAK] param=`patient_id` value=`'PATIENT-00042'`
    ```
    PII LEAK DETECTED: Sensitive value 'PATIEN…' appeared unmasked in captured output.
    ```
```

---

## MCP Server Setup

PyShield ships a [FastMCP](https://github.com/jlowin/fastmcp) server that exposes `run_shield_check()` as a tool over stdio JSON-RPC. The `pyshield-mcp` binary is included in every install.

### Test the MCP server with MCP Inspector (no IDE needed)

```bash
npx @modelcontextprotocol/inspector uvx --from pyshield pyshield-mcp
```

This opens an interactive browser UI where you can call `run_shield_check` and inspect tool schemas.

---

### Claude Desktop

Add to `~/.config/claude/claude_desktop_config.json` (macOS/Linux) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "pyshield": {
      "command": "uvx",
      "args": ["--from", "pyshield", "pyshield-mcp"],
      "cwd": "/path/to/your/project"
    }
  }
}
```

### Cursor (`.cursor/mcp.json`)

```json
{
  "mcpServers": {
    "pyshield": {
      "command": "uvx",
      "args": ["--from", "pyshield", "pyshield-mcp"],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

### VS Code Copilot (`.vscode/mcp.json`)

```json
{
  "servers": {
    "pyshield": {
      "type": "stdio",
      "command": "uvx",
      "args": ["--from", "pyshield", "pyshield-mcp"],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

> **Why `uvx`?** Using `uvx --from pyshield pyshield-mcp` means the IDE never needs PyShield installed globally — `uv` fetches and caches it automatically in an isolated environment on first launch.

### Tool signature

```python
run_shield_check(files: list[str] | None = None) -> str
```

When `files` is `None`, PyShield resolves targets from `git diff HEAD`. Returns a Markdown failure contract for the calling agent to interpret and fix — or a clean pass message when everything passes.

---

## Engine Architecture

```
pyshield/
├── pyshield/
│   ├── __init__.py
│   ├── cli.py             # argparse entry point; Provenance Ledger output
│   ├── mcp_server.py      # FastMCP stdio server; run_shield_check() tool
│   └── engine/
│       ├── tracker.py     # git diff + ls-files → changed .py files
│       ├── parser.py      # ast.parse → FunctionInfo (name, lineno, params, annotations)
│       ├── harvester.py   # param-name classifiers → boundary mutation arrays
│       ├── compliance.py  # FIN001 static policy + SHA-256 seal/store
│       └── runner.py      # sandboxed exec, PII fuzzer, circuit-breaker
└── tests/
    ├── test_tracker.py     # 6 tests
    ├── test_parser.py      # 7 tests
    ├── test_harvester.py   # 12 tests
    ├── test_compliance.py  # 10 tests
    └── test_runner.py      # 6 tests
```

### Engine Stages (per file)

1. **Track** — `tracker.py` runs `git diff HEAD` and `git ls-files --others` to build the target file list
2. **Parse** — `parser.py` walks the AST to extract every `FunctionDef` with its parameter names and type annotations (`self`/`cls` excluded)
3. **Harvest** — `harvester.py` classifies each parameter by name pattern, producing typed boundary arrays; also scans sibling `*.py` files for `UPPERCASE` constants
4. **Policy** — `compliance.py` statically checks for FIN001 (financial float arithmetic) across all function AST nodes
5. **Execute** — `runner.py` sandboxes each mutation in a temp file loaded via `importlib`, intercepts `stdout`/logging for PII, mocks all write-mode `open()` and subprocess calls
6. **Seal** — `compliance.py` writes a SHA-256 `.pyshield/<file>.seal.json` when all stages pass for a file

### Mutation Classifier Rules

| Param name contains | Mutations injected |
|---|---|
| `email` | `"a@b"`, `"@@"`, `"   "`, `""`, `"not-an-email"`, `"@domain.com"` |
| `id`, `count`, `index` | `0`, `-1`, `1`, `2147483647`, `-2147483648` |
| `price`, `balance`, `amount` | `0.0`, `-0.01`, `float('nan')`, `float('inf')`, `-float('inf')` |
| `ssn`, `patient_id`, `credit_card`, … | PII seed + default mutations |
| *(anything else)* | `None`, `""`, `0`, `-1` |

---

## Running Tests

```bash
# Full test suite
uv run pytest

# With verbose output
uv run pytest -v

# Linting
uv run ruff check .

# Type checking
uv run mypy pyshield/
```

---

## CI Integration

PyShield is designed as a native CI gate:

```yaml
# GitHub Actions example
- name: Run PyShield
  run: uv run pyshield --format json > pyshield-report.json
  continue-on-error: false   # exit 1 blocks the pipeline

- name: Upload report
  uses: actions/upload-artifact@v4
  with:
    name: pyshield-report
    path: pyshield-report.json
```

---

## Limitations & Known Behaviour

- **Sandboxed execution scope** — mutations are injected one parameter at a time; remaining parameters receive `None`. Functions with strict co-parameter validation will fail on unrelated params (this is expected; use it to find missing guard clauses).
- **Log-level PII detection** — PII leaks via `logger.info()` are only detected when the root log level is `INFO` or lower. At the default `WARNING` level, `info()` calls are suppressed before reaching the capture stream.
- **Import-dependent functions** — functions that import external packages not present in the current environment will fail with `ModuleNotFoundError` during sandboxed execution. Ensure your project environment is fully installed before running PyShield.
- **Policy rules are additive** — currently only FIN001 is shipped. Additional rule IDs (`SEC001`, `PII001`, etc.) are planned.

---

## Roadmap

- [ ] `SEC001` — detect `eval()` / `exec()` on user-supplied input
- [ ] `PII001` — detect unmasked PII in return values (not just stdout)
- [ ] Per-file policy configuration via `.pyshield.toml`
- [ ] HTML report output
- [ ] Parallel file processing
- [ ] VS Code extension with inline violation markers

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the development workflow, code standards, and how to add a new policy rule.

---

## Security

Please do not open public issues for security vulnerabilities. Read [SECURITY.md](SECURITY.md) for the responsible disclosure process.

---

## License

MIT — see [LICENSE](LICENSE).
