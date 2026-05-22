"""Universal POSIX Terminal Access Loop — CLI entry point (exit code 0/1)."""

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pyshield import __version__
from pyshield.engine import compliance, harvester, parser, runner, tracker
from pyshield.engine.runner import _safe_repr

# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


def run_pipeline(target_files: list[str] | None = None) -> dict[str, Any]:
    """Execute the full validation pipeline and return a Provenance Ledger dict.

    Stages (per file):
    1. Parse AST → extract function metadata.
    2. Scan sibling constants for mutation enrichment.
    3. Check financial float-usage policy.
    4. Run sandboxed mutation tests with PII leak detection.
    5. Compute and store SHA-256 cryptographic seal (only when all checks pass).
    """
    files: list[str] = target_files if target_files else tracker.get_changed_files()

    ledger: dict[str, Any] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "git_files": files,
        "results": [],
        "passed": True,
    }

    for filepath in files:
        file_entry: dict[str, Any] = {
            "file": filepath,
            "functions": [],
            "policy": [],
            "seal": None,
        }

        # ── Stage 1: AST parse ─────────────────────────────────────────────
        try:
            functions = parser.parse_file(filepath)
        except RuntimeError as exc:
            file_entry["parse_error"] = str(exc)
            ledger["results"].append(file_entry)
            ledger["passed"] = False
            continue

        # ── Stage 2: Scan sibling constants ───────────────────────────────
        sibling_constants: dict[str, object] = {}
        for sibling in Path(filepath).parent.glob("*.py"):
            sibling_constants.update(harvester.scan_constants(str(sibling)))

        # ── Stage 3: Policy check ──────────────────────────────────────────
        try:
            source: str = Path(filepath).read_text(encoding="utf-8")
            violations = compliance.check_financial_float_usage(source, filepath)
        except OSError as exc:
            file_entry["read_error"] = str(exc)
            violations = []

        file_entry["policy"] = [
            {
                "rule": v.rule,
                "message": v.message,
                "lineno": v.lineno,
                "function": v.function,
            }
            for v in violations
        ]
        if violations:
            ledger["passed"] = False

        # ── Stage 4: Mutation tests ────────────────────────────────────────
        for func in functions:
            test_results = runner.run_mutation_tests(
                filepath, func, sibling_constants
            )
            func_entry: dict[str, Any] = {
                "name": func.name,
                "lineno": func.lineno,
                "params": func.params,
                "mutations": [],
            }
            file_passed: bool = not violations
            for tr in test_results:
                func_entry["mutations"].append(
                    {
                        "param": tr.param,
                        "value": _safe_repr(tr.value),
                        "passed": tr.passed,
                        "pii_leak": tr.pii_leak_detected,
                        "circuit_broken": tr.circuit_broken,
                        "error": tr.error,
                    }
                )
                if not tr.passed:
                    file_passed = False
                    ledger["passed"] = False
            file_entry["functions"].append(func_entry)

        # ── Stage 5: Per-file cryptographic seal ───────────────────────────
        # Each file is sealed independently when its own policy + mutations pass,
        # regardless of whether other files in the batch have failures.
        if file_passed:
            try:
                seal = compliance.compute_seal(filepath, violations)
                compliance.store_seal(seal)
                file_entry["seal"] = {
                    "sha256": seal.sha256,
                    "timestamp": seal.timestamp,
                }
            except RuntimeError as exc:
                file_entry["seal_error"] = str(exc)

        ledger["results"].append(file_entry)

    return ledger


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------


def _render_markdown(ledger: dict[str, Any]) -> str:
    """Render the Provenance Ledger as a human-readable Markdown summary."""
    status: str = "PASSED" if ledger["passed"] else "FAILED"
    lines: list[str] = [
        f"# PyShield Provenance Ledger — [{status}]",
        f"\n**Timestamp:** {ledger['timestamp']}",
        f"**Git Files Scanned:** {len(ledger['git_files'])}",
    ]

    for file_result in ledger["results"]:
        lines.append(f"\n## `{file_result['file']}`")

        if file_result.get("parse_error"):
            lines.append(f"\n> **PARSE ERROR:** {file_result['parse_error']}")
            continue

        if file_result.get("read_error"):
            lines.append(f"\n> **READ ERROR:** {file_result['read_error']}")

        if file_result["policy"]:
            lines.append("\n### Policy Violations (FIN001)")
            for v in file_result["policy"]:
                lines.append(
                    f"- `{v['rule']}` line {v['lineno']}"
                    f" in `{v['function']}`: {v['message']}"
                )
        else:
            lines.append("\n### Policy: No violations detected")

        for func in file_result["functions"]:
            failures = [m for m in func["mutations"] if not m["passed"]]
            lines.append(f"\n#### `{func['name']}` (line {func['lineno']})")
            if not failures:
                lines.append("  All mutations passed.")
            else:
                for fail in failures:
                    tag = (
                        "[PII LEAK]"
                        if fail["pii_leak"]
                        else "[CIRCUIT]"
                        if fail["circuit_broken"]
                        else "[FAIL]"
                    )
                    lines.append(
                        f"  - {tag} param=`{fail['param']}` value=`{fail['value']}`"
                    )
                    if fail["error"]:
                        snippet = fail["error"][:300].replace("\n", "\n    ")
                        lines.append(f"    ```\n    {snippet}\n    ```")

        if file_result.get("seal"):
            lines.append("\n### Validation Seal")
            lines.append(f"  SHA-256: `{file_result['seal']['sha256']}`")
            lines.append(f"  Sealed:  {file_result['seal']['timestamp']}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point.  Exits with code 0 on success, 1 on any failure."""
    arg_parser = argparse.ArgumentParser(
        prog="pyshield",
        description="PyShield Deterministic Validation Engine",
    )
    arg_parser.add_argument(
        "files",
        nargs="*",
        help="Python files to validate (defaults to git-changed files)",
    )
    arg_parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    arg_parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    args = arg_parser.parse_args()

    ledger = run_pipeline(args.files or None)

    if args.format == "json":
        print(json.dumps(ledger, indent=2))
    else:
        print(_render_markdown(ledger))

    sys.exit(0 if ledger["passed"] else 1)


if __name__ == "__main__":
    main()
