"""Static Policy-as-Code & Cryptographic Ledger."""

import ast
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from pathlib import Path

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

_RE_FINANCIAL: re.Pattern[str] = re.compile(r"price|balance|amount", re.IGNORECASE)

# Arithmetic operators that must NOT be used with financial primitives.
_ARITHMETIC_OPS: tuple[type, ...] = (
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.Pow,
)


@dataclass
class PolicyViolation:
    """A single policy-as-code infraction."""

    rule: str
    message: str
    lineno: int
    function: str


@dataclass
class ValidationSeal:
    """Cryptographic proof of a successful validation run."""

    filepath: str
    sha256: str
    timestamp: str
    violations: list[PolicyViolation]
    passed: bool


# ---------------------------------------------------------------------------
# Policy checks
# ---------------------------------------------------------------------------


def check_financial_float_usage(
    source: str,
    filepath: str = "<string>",
) -> list[PolicyViolation]:
    """Scan *source* for financial variables manipulated with float arithmetic.

    Rule **FIN001** fires when a parameter or local variable whose name
    contains ``price``, ``balance``, or ``amount`` appears as an operand in a
    binary arithmetic expression, or as the target of an augmented-assignment
    arithmetic operator, instead of being wrapped in ``decimal.Decimal``.

    Returns an empty list when the source cannot be parsed.
    """
    violations: list[PolicyViolation] = []
    try:
        tree: ast.Module = ast.parse(source, filename=filepath)
    except SyntaxError:
        return violations

    for func_node in ast.walk(tree):
        if not isinstance(func_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        func_name: str = func_node.name
        flagged_lines: set[int] = set()

        for child in ast.walk(func_node):
            lineno: int = getattr(child, "lineno", 0)
            if lineno in flagged_lines:
                continue

            # AugAssign: balance -= fee  /  price *= factor
            if isinstance(child, ast.AugAssign):
                if (
                    isinstance(child.target, ast.Name)
                    and _RE_FINANCIAL.search(child.target.id)
                    and isinstance(child.op, _ARITHMETIC_OPS)
                ):
                    flagged_lines.add(lineno)
                    violations.append(
                        PolicyViolation(
                            rule="FIN001",
                            message=(
                                f"Financial variable '{child.target.id}' modified with "
                                f"standard arithmetic operator. Use decimal.Decimal."
                            ),
                            lineno=lineno,
                            function=func_name,
                        )
                    )

            # BinOp: any financial name as a direct operand
            elif isinstance(child, ast.BinOp) and isinstance(
                child.op, _ARITHMETIC_OPS
            ):
                for operand in (child.left, child.right):
                    if isinstance(operand, ast.Name) and _RE_FINANCIAL.search(
                        operand.id
                    ):
                        flagged_lines.add(lineno)
                        violations.append(
                            PolicyViolation(
                                rule="FIN001",
                                message=(
                                    f"Financial variable '{operand.id}' used in float "
                                    f"arithmetic. Use decimal.Decimal."
                                ),
                                lineno=lineno,
                                function=func_name,
                            )
                        )
                        break

    return violations


# ---------------------------------------------------------------------------
# Cryptographic sealing
# ---------------------------------------------------------------------------


def compute_seal(
    filepath: str,
    violations: list[PolicyViolation],
) -> ValidationSeal:
    """Compute an offline SHA-256 seal for *filepath*.

    Raises:
        RuntimeError: If the file cannot be read.
    """
    path = Path(filepath)
    try:
        content: bytes = path.read_bytes()
    except OSError as exc:
        raise RuntimeError(f"Cannot read {filepath} for sealing: {exc}") from exc

    digest: str = hashlib.sha256(content).hexdigest()
    timestamp: str = datetime.now(UTC).isoformat()

    return ValidationSeal(
        filepath=str(filepath),
        sha256=digest,
        timestamp=timestamp,
        violations=violations,
        passed=len(violations) == 0,
    )


def store_seal(
    seal: ValidationSeal,
    output_dir: str = ".pyshield",
) -> Path:
    """Persist *seal* as a JSON metadata block under *output_dir*.

    The directory is created if it does not exist.  Returns the path of the
    written seal file.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    safe_stem: str = Path(seal.filepath).stem
    seal_path: Path = out_dir / f"{safe_stem}.seal.json"

    payload: dict[str, Any] = {
        "filepath": seal.filepath,
        "sha256": seal.sha256,
        "timestamp": seal.timestamp,
        "passed": seal.passed,
        "violations": [
            {
                "rule": v.rule,
                "message": v.message,
                "lineno": v.lineno,
                "function": v.function,
            }
            for v in seal.violations
        ],
    }

    seal_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return seal_path
