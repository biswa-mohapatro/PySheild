"""Tests for engine/tracker.py — Git Mutation Isolation."""

import subprocess
from unittest.mock import patch

from pyshield.engine.tracker import get_changed_files

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _completed(stdout: str, returncode: int = 0, stderr: str = "") -> subprocess.CompletedProcess:
    result: subprocess.CompletedProcess = subprocess.CompletedProcess(
        args=[], returncode=returncode
    )
    result.stdout = stdout
    result.stderr = stderr
    return result


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_returns_only_py_files() -> None:
    """Non-.py files in git diff output must be excluded."""
    def _side(args, **_kw):
        if "diff" in args:
            return _completed("foo.py\nbar.txt\nbaz.py\n")
        return _completed("")

    with patch("subprocess.run", side_effect=_side):
        files = get_changed_files()

    assert "foo.py" in files
    assert "baz.py" in files
    assert "bar.txt" not in files


def test_returns_empty_outside_git_repo() -> None:
    """Returns an empty list when called outside a git working tree."""
    def _side(args, **_kw):
        return _completed(stdout="", returncode=128, stderr="not a git repository")

    with patch("subprocess.run", side_effect=_side):
        files = get_changed_files()

    assert files == []


def test_returns_empty_when_git_not_installed() -> None:
    """Returns an empty list when the git binary is not found on PATH."""
    with patch("subprocess.run", side_effect=FileNotFoundError):
        files = get_changed_files()

    assert files == []


def test_includes_untracked_py_files() -> None:
    """Untracked .py files from ls-files --others must be included."""
    def _side(args, **_kw):
        if "diff" in args:
            return _completed("changed.py\n")
        return _completed("untracked.py\n")

    with patch("subprocess.run", side_effect=_side):
        files = get_changed_files()

    assert "changed.py" in files
    assert "untracked.py" in files


def test_deduplicates_files() -> None:
    """Duplicate entries across diff and ls-files must be collapsed."""
    def _side(args, **_kw):
        if "diff" in args:
            return _completed("dup.py\n")
        return _completed("dup.py\n")

    with patch("subprocess.run", side_effect=_side):
        files = get_changed_files()

    assert files.count("dup.py") == 1


def test_handles_os_error_gracefully() -> None:
    """An OSError during subprocess execution returns an empty list."""
    with patch("subprocess.run", side_effect=OSError("pipe broken")):
        files = get_changed_files()

    assert files == []
