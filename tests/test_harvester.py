"""Tests for engine/harvester.py — Deterministic Structural Matrix."""

import math
import tempfile
import textwrap
from pathlib import Path

from pyshield.engine.harvester import (
    EMAIL_MUTATIONS,
    ID_MUTATIONS,
    generate_mutations,
    get_mutations_for_param,
    scan_constants,
)

# ---------------------------------------------------------------------------
# get_mutations_for_param
# ---------------------------------------------------------------------------


def test_email_param_gets_malformed_strings() -> None:
    """A parameter containing 'email' receives all EMAIL_MUTATIONS."""
    mutations = get_mutations_for_param("user_email")
    for expected in EMAIL_MUTATIONS:
        assert expected in mutations


def test_id_param_gets_integer_boundaries() -> None:
    """A parameter containing 'id' receives integer boundary values."""
    mutations = get_mutations_for_param("user_id")
    assert 0 in mutations
    assert -1 in mutations


def test_count_param_gets_integer_boundaries() -> None:
    """A parameter containing 'count' receives integer boundary values."""
    mutations = get_mutations_for_param("item_count")
    assert 0 in mutations
    assert -1 in mutations


def test_index_param_gets_integer_boundaries() -> None:
    """A bare 'index' parameter name receives integer boundary values."""
    mutations = get_mutations_for_param("index")
    for expected in ID_MUTATIONS:
        assert expected in mutations


def test_financial_balance_gets_float_mutations() -> None:
    """A parameter containing 'balance' receives float edge-case mutations."""
    mutations = get_mutations_for_param("user_balance")
    assert 0.0 in mutations
    assert -0.01 in mutations
    assert any(isinstance(m, float) and math.isnan(m) for m in mutations)


def test_financial_price_gets_inf() -> None:
    """A parameter containing 'price' receives float('inf')."""
    mutations = get_mutations_for_param("item_price")
    assert float("inf") in mutations


def test_financial_amount_gets_mutations() -> None:
    """A parameter containing 'amount' receives FINANCIAL_MUTATIONS."""
    mutations = get_mutations_for_param("transaction_amount")
    assert -0.01 in mutations


def test_unknown_param_gets_default_mutations() -> None:
    """An unrecognised parameter receives safe defaults (None, '', 0, -1)."""
    mutations = get_mutations_for_param("foobar")
    assert None in mutations
    assert "" in mutations
    assert 0 in mutations
    assert -1 in mutations


# ---------------------------------------------------------------------------
# scan_constants
# ---------------------------------------------------------------------------


def test_scan_constants_extracts_uppercase_literals() -> None:
    """UPPERCASE constants with literal values must be returned."""
    source = textwrap.dedent("""\
        MAX_LIMIT = 100
        MIN_VALUE = -5
        RATE = 0.07
        not_a_constant = 42
        Mixed_Case = 10
    """)
    tmp = tempfile.NamedTemporaryFile(
        suffix=".py", mode="w", delete=False, encoding="utf-8"
    )
    tmp.write(source)
    tmp.close()

    try:
        constants = scan_constants(tmp.name)
    finally:
        Path(tmp.name).unlink(missing_ok=True)

    assert constants.get("MAX_LIMIT") == 100
    assert constants.get("MIN_VALUE") == -5
    assert constants.get("RATE") == 0.07
    assert "not_a_constant" not in constants
    assert "Mixed_Case" not in constants


def test_scan_constants_returns_empty_for_missing_file() -> None:
    """scan_constants must return {} for a non-existent file."""
    result = scan_constants("/nonexistent/__pyshield_constants__.py")
    assert result == {}


# ---------------------------------------------------------------------------
# generate_mutations
# ---------------------------------------------------------------------------


def test_generate_mutations_merges_constants() -> None:
    """generate_mutations must include discovered constants alongside classifiers."""
    mutations = generate_mutations("balance", {"MAX_LIMIT": 100, "MIN_VAL": -999})
    assert 0.0 in mutations          # from FINANCIAL_MUTATIONS
    assert 100 in mutations          # from constants
    assert -999 in mutations         # from constants


def test_generate_mutations_without_constants() -> None:
    """generate_mutations with no constants falls back to classifier output."""
    mutations = generate_mutations("user_email")
    for expected in EMAIL_MUTATIONS:
        assert expected in mutations
