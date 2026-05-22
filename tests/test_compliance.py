"""Tests for engine/compliance.py — Static Policy-as-Code & Cryptographic Ledger."""

import json
import tempfile
import textwrap
from pathlib import Path

import pytest

from pyshield.engine.compliance import (
    PolicyViolation,
    check_financial_float_usage,
    compute_seal,
    store_seal,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_ANTI_PATTERN_AUGASSIGN = textwrap.dedent("""\
    def process_payment(user_balance: float, fee: float) -> float:
        user_balance -= fee
        return user_balance
""")

_ANTI_PATTERN_BINOP = textwrap.dedent("""\
    def apply_discount(price: float, discount: float) -> float:
        new_price = price * (1 - discount)
        return new_price
""")

_ANTI_PATTERN_AMOUNT = textwrap.dedent("""\
    def charge(amount: float, tax: float) -> float:
        total = amount + tax
        return total
""")

_COMPLIANT_NO_FLOAT_OPS = textwrap.dedent("""\
    from decimal import Decimal

    def process_payment(user_balance: Decimal, fee: Decimal) -> Decimal:
        return user_balance
""")


# ---------------------------------------------------------------------------
# check_financial_float_usage
# ---------------------------------------------------------------------------


def test_detects_augmented_assign_violation() -> None:
    """AugAssign on a financial variable must trigger FIN001."""
    violations = check_financial_float_usage(_ANTI_PATTERN_AUGASSIGN)
    assert len(violations) >= 1
    assert any(v.rule == "FIN001" for v in violations)
    assert any("user_balance" in v.message for v in violations)


def test_detects_binop_on_price_parameter() -> None:
    """Binary arithmetic involving 'price' must trigger FIN001."""
    violations = check_financial_float_usage(_ANTI_PATTERN_BINOP)
    assert len(violations) >= 1
    assert any(v.rule == "FIN001" for v in violations)


def test_detects_binop_on_amount_parameter() -> None:
    """Binary arithmetic involving 'amount' must trigger FIN001."""
    violations = check_financial_float_usage(_ANTI_PATTERN_AMOUNT)
    assert len(violations) >= 1
    assert any(v.rule == "FIN001" for v in violations)


def test_compliant_code_produces_no_violations() -> None:
    """A function that does not perform float BinOp on financial vars is clean."""
    violations = check_financial_float_usage(_COMPLIANT_NO_FLOAT_OPS)
    assert violations == []


def test_returns_empty_list_on_syntax_error() -> None:
    """Unparseable source must return an empty list rather than raising."""
    violations = check_financial_float_usage("def broken(: ->\n    pass")
    assert violations == []


def test_violation_carries_function_name_and_lineno() -> None:
    """Each violation must record the enclosing function name and a line number."""
    violations = check_financial_float_usage(_ANTI_PATTERN_AUGASSIGN)
    for v in violations:
        assert v.function == "process_payment"
        assert v.lineno > 0


# ---------------------------------------------------------------------------
# compute_seal
# ---------------------------------------------------------------------------


def test_compute_seal_returns_64_char_hex_digest() -> None:
    """SHA-256 digest must be exactly 64 hexadecimal characters."""
    tmp = tempfile.NamedTemporaryFile(
        suffix=".py", mode="w", delete=False, encoding="utf-8"
    )
    tmp.write("def foo(): pass\n")
    tmp.close()
    try:
        seal = compute_seal(tmp.name, [])
    finally:
        Path(tmp.name).unlink(missing_ok=True)

    assert len(seal.sha256) == 64
    assert all(c in "0123456789abcdef" for c in seal.sha256)


def test_compute_seal_passed_flag_reflects_violations() -> None:
    """Seal.passed must be True when violations is empty, False otherwise."""
    tmp = tempfile.NamedTemporaryFile(
        suffix=".py", mode="w", delete=False, encoding="utf-8"
    )
    tmp.write("x = 1\n")
    tmp.close()
    try:
        clean_seal = compute_seal(tmp.name, [])
        dirty_seal = compute_seal(
            tmp.name,
            [PolicyViolation(rule="FIN001", message="x", lineno=1, function="f")],
        )
    finally:
        Path(tmp.name).unlink(missing_ok=True)

    assert clean_seal.passed is True
    assert dirty_seal.passed is False


def test_compute_seal_raises_for_missing_file() -> None:
    """compute_seal must raise RuntimeError for a non-existent file."""
    with pytest.raises(RuntimeError, match="Cannot read"):
        compute_seal("/nonexistent/__pyshield_seal__.py", [])


# ---------------------------------------------------------------------------
# store_seal
# ---------------------------------------------------------------------------


def test_store_seal_creates_valid_json_file(tmp_path: Path) -> None:
    """store_seal must create a JSON file with the expected fields."""
    source_file = tmp_path / "example.py"
    source_file.write_text("def foo(): pass\n", encoding="utf-8")

    seal = compute_seal(str(source_file), [])
    seal_path = store_seal(seal, output_dir=str(tmp_path / ".pyshield"))

    assert seal_path.exists()
    data = json.loads(seal_path.read_text(encoding="utf-8"))
    assert data["sha256"] == seal.sha256
    assert data["passed"] is True
    assert isinstance(data["violations"], list)
    assert "timestamp" in data
