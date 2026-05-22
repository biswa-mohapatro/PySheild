"""Tests for engine/parser.py — AST Code Investigator."""

import tempfile
import textwrap
from pathlib import Path

import pytest

from pyshield.engine.parser import parse_file

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _temp_py(source: str) -> str:
    """Write *source* to a temp .py file and return its path."""
    tmp = tempfile.NamedTemporaryFile(
        suffix=".py", mode="w", delete=False, encoding="utf-8"
    )
    tmp.write(source)
    tmp.close()
    return tmp.name


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_extracts_function_names_and_linenos() -> None:
    """Function names and their line numbers must be captured accurately."""
    source = textwrap.dedent("""\
        def add(a: int, b: int) -> int:
            return a + b

        def subtract(x: float, y: float) -> float:
            return x - y
    """)
    path = _temp_py(source)
    try:
        functions = parse_file(path)
    finally:
        Path(path).unlink(missing_ok=True)

    names = [f.name for f in functions]
    assert "add" in names
    assert "subtract" in names

    add_func = next(f for f in functions if f.name == "add")
    assert add_func.lineno == 1


def test_excludes_self_and_cls() -> None:
    """self and cls must not appear in the extracted parameter list."""
    source = textwrap.dedent("""\
        class Foo:
            def method(self, value: int) -> None:
                pass

            @classmethod
            def create(cls, label: str) -> "Foo":
                pass
    """)
    path = _temp_py(source)
    try:
        functions = parse_file(path)
    finally:
        Path(path).unlink(missing_ok=True)

    for func in functions:
        assert "self" not in func.params
        assert "cls" not in func.params


def test_captures_type_annotations() -> None:
    """Parameter and return type annotations must be captured as strings."""
    source = textwrap.dedent("""\
        def greet(name: str, age: int) -> str:
            return f"Hello {name}"
    """)
    path = _temp_py(source)
    try:
        functions = parse_file(path)
    finally:
        Path(path).unlink(missing_ok=True)

    greet = next(f for f in functions if f.name == "greet")
    assert greet.annotations["name"] == "str"
    assert greet.annotations["age"] == "int"
    assert greet.annotations["return"] == "str"


def test_returns_empty_list_for_module_with_no_functions() -> None:
    """A module containing no function definitions returns an empty list."""
    source = "X = 1\nY = 2\n"
    path = _temp_py(source)
    try:
        functions = parse_file(path)
    finally:
        Path(path).unlink(missing_ok=True)

    assert functions == []


def test_raises_on_syntax_error() -> None:
    """A file with invalid syntax raises RuntimeError mentioning 'Syntax error'."""
    source = "def broken(: ->\n    pass"
    path = _temp_py(source)
    try:
        with pytest.raises(RuntimeError, match="Syntax error"):
            parse_file(path)
    finally:
        Path(path).unlink(missing_ok=True)


def test_raises_on_missing_file() -> None:
    """A non-existent path raises RuntimeError mentioning 'Cannot read file'."""
    with pytest.raises(RuntimeError, match="Cannot read file"):
        parse_file("/nonexistent/__pyshield_test__.py")


def test_async_functions_are_included() -> None:
    """async def functions must be included in the output."""
    source = textwrap.dedent("""\
        async def fetch(url: str) -> bytes:
            return b""
    """)
    path = _temp_py(source)
    try:
        functions = parse_file(path)
    finally:
        Path(path).unlink(missing_ok=True)

    names = [f.name for f in functions]
    assert "fetch" in names
