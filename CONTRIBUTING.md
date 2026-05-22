# Contributing to PyShield

Thank you for your interest in contributing.  PyShield is a community project and welcomes bug reports, documentation improvements, new policy rules, and broader engine enhancements.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Running Tests](#running-tests)
5. [Coding Standards](#coding-standards)
6. [Adding a New Policy Rule](#adding-a-new-policy-rule)
7. [Adding a New Mutation Classifier](#adding-a-new-mutation-classifier)
8. [Pull Request Checklist](#pull-request-checklist)
9. [Reporting Bugs](#reporting-bugs)

---

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating you agree to abide by its terms.

---

## Getting Started

```bash
git clone https://github.com/biswa-mohapatro/PySheild.git
cd pyshield
uv sync           # installs runtime + dev dependencies
uv run pytest     # verify all 41 tests pass before you start
```

---

## Development Workflow

1. Fork the repository and clone your fork.
2. Create a focused feature branch: `git checkout -b feat/my-feature`.
3. Make your changes (see guidelines below).
4. Run the full quality gate locally:

   ```bash
   uv run ruff check .
   uv run mypy pyshield/
   uv run pytest -v
   ```

5. Commit using clear, imperative commit messages (e.g. `Add SEC001 rule for eval() on user input`).
6. Push and open a pull request against `main`.

---

## Running Tests

```bash
uv run pytest                   # full suite
uv run pytest tests/test_compliance.py -v   # single module
uv run pytest -k "pii"          # filter by keyword
```

---

## Coding Standards

- **Python 3.13+** with strict type annotations on all public functions and class attributes.
- **Ruff** for linting and import sorting (`uv run ruff check . --fix`).
- **Mypy** in strict mode (`uv run mypy pyshield/`).
- **No placeholders** — every function must have production logic. No `# TODO` stubs or bare `pass` blocks in non-abstract code.
- **Determinism** — PyShield must remain 100% deterministic. Do not introduce probabilistic components (LLMs, embeddings, heuristics, network calls).
- **Test coverage** — every new module or meaningful code path needs a corresponding test in `tests/`.

---

## Adding a New Policy Rule

Policy rules live in `pyshield/engine/compliance.py`.

1. Choose a rule ID in the format `XXX000` (e.g. `SEC001`).
2. Implement a detection function that accepts `(source: str, filepath: str) -> list[PolicyViolation]` and walks the AST.
3. Add the rule to the `check_*` function chain in `compliance.py` and to the pipeline call in `cli.py`.
4. Add tests in `tests/test_compliance.py` covering the violation case, the compliant case, and the syntax-error edge case.
5. Document the rule in the README mutation/policy tables and in `CHANGELOG.md` under `[Unreleased]`.

---

## Adding a New Mutation Classifier

Classifiers live in `pyshield/engine/harvester.py`.

1. Define a `_RE_<NAME>` compiled regex constant.
2. Add the boundary array constant (e.g. `DATE_MUTATIONS: list[str] = [...]`).
3. Extend `get_mutations_for_param()` with the new branch.
4. Add tests in `tests/test_harvester.py`.
5. Update the classifier rules table in `README.md`.

---

## Pull Request Checklist

Before requesting review, confirm:

- [ ] `uv run ruff check .` — no errors
- [ ] `uv run mypy pyshield/` — no errors
- [ ] `uv run pytest` — all tests pass
- [ ] New behaviour has corresponding tests
- [ ] `CHANGELOG.md` updated under `[Unreleased]`
- [ ] Public API changes reflected in `README.md`

---

## Reporting Bugs

Open a [GitHub Issue](https://github.com/biswa-mohapatro/PySheild/issues/new?template=bug_report.md) with:

- Your OS, Python version, and PyShield version (`pyshield --version`)
- The minimal Python file that reproduces the problem
- The full CLI output (use `--format json` for structured output)
