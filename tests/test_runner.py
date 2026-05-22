"""Tests for engine/runner.py — Sandboxed Mutation Executor & PII Leak Fuzzer."""

import tempfile
import textwrap
from pathlib import Path

from pyshield.engine.parser import FunctionInfo
from pyshield.engine.runner import reset_circuit_breaker, run_mutation_tests

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _temp_py(source: str) -> str:
    tmp = tempfile.NamedTemporaryFile(
        suffix=".py", mode="w", delete=False, encoding="utf-8"
    )
    tmp.write(source)
    tmp.close()
    return tmp.name


# ---------------------------------------------------------------------------
# PII leak detection
# ---------------------------------------------------------------------------


def test_flags_unmasked_pii_in_stdout() -> None:
    """Runner must detect and flag PII values that appear in captured stdout."""
    source = textwrap.dedent("""\
        def display_patient(patient_id: str) -> None:
            print(f"Processing: {patient_id}")
    """)
    path = _temp_py(source)
    func_info = FunctionInfo(
        name="display_patient",
        lineno=1,
        params=["patient_id"],
        annotations={"patient_id": "str"},
    )
    try:
        results = run_mutation_tests(path, func_info)
    finally:
        Path(path).unlink(missing_ok=True)

    pii_results = [r for r in results if r.pii_leak_detected]
    assert len(pii_results) > 0


def test_pii_result_is_marked_as_failed() -> None:
    """A PII leak must also set passed=False on the TestResult."""
    source = textwrap.dedent("""\
        def show_ssn(ssn: str) -> None:
            print(ssn)
    """)
    path = _temp_py(source)
    func_info = FunctionInfo(
        name="show_ssn",
        lineno=1,
        params=["ssn"],
        annotations={"ssn": "str"},
    )
    try:
        results = run_mutation_tests(path, func_info)
    finally:
        Path(path).unlink(missing_ok=True)

    for r in results:
        if r.pii_leak_detected:
            assert r.passed is False


# ---------------------------------------------------------------------------
# Basic mutation coverage
# ---------------------------------------------------------------------------


def test_mutation_results_generated_for_each_param() -> None:
    """At least one TestResult must be produced per parameter."""
    source = textwrap.dedent("""\
        def process(user_id: int) -> int:
            if user_id < 0:
                raise ValueError("Negative ID")
            return user_id
    """)
    path = _temp_py(source)
    func_info = FunctionInfo(
        name="process",
        lineno=1,
        params=["user_id"],
        annotations={"user_id": "int"},
    )
    try:
        results = run_mutation_tests(path, func_info)
    finally:
        Path(path).unlink(missing_ok=True)

    assert len(results) > 0
    assert all(r.param == "user_id" for r in results)


def test_failing_function_produces_error_in_result() -> None:
    """A function that always raises must produce TestResults with error set."""
    source = textwrap.dedent("""\
        def always_fails(user_id: int) -> None:
            raise RuntimeError("always fails")
    """)
    path = _temp_py(source)
    func_info = FunctionInfo(
        name="always_fails",
        lineno=1,
        params=["user_id"],
        annotations={"user_id": "int"},
    )
    try:
        results = run_mutation_tests(path, func_info)
    finally:
        Path(path).unlink(missing_ok=True)

    assert any(r.error is not None for r in results)
    assert all(not r.passed for r in results if not r.circuit_broken)


# ---------------------------------------------------------------------------
# Circuit-breaker
# ---------------------------------------------------------------------------


def test_circuit_breaker_triggers_after_threshold() -> None:
    """Repeated pipeline calls for the same failing (func, param, value) must
    eventually produce TestResults with circuit_broken=True."""
    reset_circuit_breaker()

    source = textwrap.dedent("""\
        def always_fails(user_id: int) -> None:
            raise RuntimeError("always fails")
    """)
    path = _temp_py(source)
    func_info = FunctionInfo(
        name="always_fails",
        lineno=1,
        params=["user_id"],
        annotations={"user_id": "int"},
    )
    try:
        all_results = []
        for _ in range(5):
            all_results.extend(run_mutation_tests(path, func_info))
    finally:
        Path(path).unlink(missing_ok=True)
        reset_circuit_breaker()

    broken = [r for r in all_results if r.circuit_broken]
    assert len(broken) > 0


# ---------------------------------------------------------------------------
# Sandboxing
# ---------------------------------------------------------------------------


def test_sandboxes_write_operations_do_not_touch_disk(tmp_path: Path) -> None:
    """Calls to open() in write mode inside the sandbox must be intercepted."""
    sentinel: Path = tmp_path / "pyshield_write_test.txt"
    source = textwrap.dedent(f"""\
        def write_file(user_id: int) -> None:
            with open(r"{sentinel}", "w") as f:
                f.write(str(user_id))
    """)
    path = _temp_py(source)
    func_info = FunctionInfo(
        name="write_file",
        lineno=1,
        params=["user_id"],
        annotations={"user_id": "int"},
    )
    try:
        run_mutation_tests(path, func_info)
    finally:
        Path(path).unlink(missing_ok=True)

    assert not sentinel.exists(), "Sandboxed write must not create files on disk."
