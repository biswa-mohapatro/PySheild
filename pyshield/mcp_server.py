"""FastMCP Server — stdio JSON-RPC bridge for the hybrid agent handoff."""

from fastmcp import FastMCP

from pyshield.cli import run_pipeline

mcp: FastMCP = FastMCP("PyShield")


@mcp.tool()
def run_shield_check(files: list[str] | None = None) -> str:
    """Run PyShield deterministic validation on changed or specified Python files.

    This tool is the **hybrid handoff interface**.  It executes the full
    validation pipeline (git tracking → AST parse → policy check → mutation
    tests → PII leak detection) and returns a high-density Markdown payload
    containing *exact* failure contracts — crash vectors, parameter values,
    tracebacks, and policy violations.

    The output is intentionally raw and uninterpreted.  The calling external
    probabilistic agent (Claude Code, Cursor, GitHub Copilot) is expected to
    consume this contract and autonomously generate code fixes.

    Args:
        files: Optional list of absolute file paths to validate.  When
            omitted, PyShield resolves targets from ``git diff HEAD``.

    Returns:
        A Markdown string containing the full Provenance Ledger.  Returns a
        single-line "ALL CLEAR" message when every check passes.
    """
    ledger = run_pipeline(files)
    return _build_agent_payload(ledger)


# ---------------------------------------------------------------------------
# Internal payload builder
# ---------------------------------------------------------------------------


def _build_agent_payload(ledger: dict) -> str:
    """Compile the error contract Markdown for the calling external agent."""
    status: str = "PASSED" if ledger["passed"] else "FAILED"
    lines: list[str] = [
        f"# PyShield Report — {status}",
        f"\n**Timestamp:** {ledger['timestamp']}",
        f"**Files Analysed:** {len(ledger['git_files'])}",
    ]

    if ledger["passed"]:
        lines.append(
            "\nAll validations passed.  Cryptographic seals have been applied."
        )
        return "\n".join(lines)

    lines.append("\n---\n## Failure Contract\n")
    lines.append(
        "> The following data is the deterministic truth payload intended for "
        "the connected AI agent to interpret and resolve.\n"
    )

    for file_result in ledger["results"]:
        filepath: str = file_result["file"]
        lines.append(f"### File: `{filepath}`")

        if file_result.get("parse_error"):
            lines.append(f"\n**PARSE ERROR:** {file_result['parse_error']}")
            continue

        if file_result.get("read_error"):
            lines.append(f"\n**READ ERROR:** {file_result['read_error']}")

        if file_result["policy"]:
            lines.append("\n**Policy Violations (FIN001):**")
            for v in file_result["policy"]:
                lines.append(
                    f"- `{v['rule']}` @ line {v['lineno']}"
                    f" in `{v['function']}`: {v['message']}"
                )

        for func in file_result.get("functions", []):
            failures = [m for m in func["mutations"] if not m["passed"]]
            if not failures:
                continue

            lines.append(
                f"\n**`{func['name']}`** (line {func['lineno']}) — "
                f"{len(failures)} failure(s):"
            )
            for fail in failures:
                lines.append(
                    f"\n- **Param:** `{fail['param']}` | **Value:** `{fail['value']}`"
                )
                if fail["pii_leak"]:
                    lines.append(
                        "  - **PII LEAK DETECTED** — Sensitive data "
                        "appeared unmasked in captured output."
                    )
                if fail["circuit_broken"]:
                    lines.append(
                        "  - **CIRCUIT BREAKER TRIGGERED** — "
                        "Recurring failure requires human review."
                    )
                if fail["error"]:
                    snippet = fail["error"][:500].replace("\n", "\n    ")
                    lines.append(f"  - **Traceback:**\n    ```\n    {snippet}\n    ```")

    return "\n".join(lines)


def main() -> None:
    """Entry point for the ``pyshield-mcp`` CLI script.

    Starts the FastMCP server over stdio so that MCP clients (Claude Desktop,
    Cursor, VS Code Copilot, etc.) can launch it as a subprocess.
    """
    mcp.run()


if __name__ == "__main__":
    main()
