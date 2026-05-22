"""Git Mutation Isolation — tracks changed and untracked Python files."""

import subprocess


def get_changed_files() -> list[str]:
    """Return deduplicated list of changed or untracked .py files via git.

    Executes ``git diff HEAD --name-only`` and
    ``git ls-files --others --exclude-standard`` in a subprocess.
    Returns an empty list when called outside a valid git working tree,
    when git is not installed, or on any OS-level error.
    """
    try:
        diff_result = subprocess.run(
            ["git", "diff", "HEAD", "--name-only"],
            capture_output=True,
            text=True,
            check=False,
        )
        if diff_result.returncode != 0 and (
            "not a git repository" in diff_result.stderr.lower()
            or "not a git repo" in diff_result.stderr.lower()
        ):
            return []

        changed: list[str] = [
            line.strip()
            for line in diff_result.stdout.splitlines()
            if line.strip().endswith(".py")
        ]

        untracked_result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True,
            text=True,
            check=False,
        )
        if untracked_result.returncode == 0:
            untracked: list[str] = [
                line.strip()
                for line in untracked_result.stdout.splitlines()
                if line.strip().endswith(".py")
            ]
            changed.extend(untracked)

        # Preserve insertion order while deduplicating.
        return list(dict.fromkeys(changed))

    except FileNotFoundError:
        # git binary not available on PATH.
        return []
    except OSError:
        return []
