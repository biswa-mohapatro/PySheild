"""Deterministic Structural Matrix — generates mutation profiles from parameter names."""

import ast
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Regex classifiers
# ---------------------------------------------------------------------------

_RE_EMAIL: re.Pattern[str] = re.compile(r"email", re.IGNORECASE)
_RE_ID: re.Pattern[str] = re.compile(
    r"(?:^|_)(id|count|index)(?:_|$)|^(id|count|index)$", re.IGNORECASE
)
_RE_FINANCIAL: re.Pattern[str] = re.compile(r"price|balance|amount", re.IGNORECASE)

# ---------------------------------------------------------------------------
# Canonical mutation arrays
# ---------------------------------------------------------------------------

EMAIL_MUTATIONS: list[str] = ["a@b", "@@", "   ", "", "not-an-email", "@domain.com"]
ID_MUTATIONS: list[int] = [0, -1, 1, 2**31 - 1, -(2**31)]
FINANCIAL_MUTATIONS: list[float] = [
    0.0,
    -0.01,
    float("nan"),
    float("inf"),
    -float("inf"),
]
_DEFAULT_MUTATIONS: list[object] = [None, "", 0, -1]


def get_mutations_for_param(param_name: str) -> list[object]:
    """Return boundary/mutation values appropriate for *param_name*.

    Classification is based on substring matching against the parameter name:

    * ``email``                     → structurally malformed strings
    * ``id`` / ``count`` / ``index``→ integer boundary values
    * ``price`` / ``balance`` / ``amount`` → float edge cases (nan, inf, …)

    Returns a generic set of defaults when no classifier matches.
    """
    mutations: list[object] = []

    if _RE_EMAIL.search(param_name):
        mutations.extend(EMAIL_MUTATIONS)

    # Accept bare names ("id", "count", "index") or compound names ("user_id").
    if _RE_ID.search(param_name) or param_name.lower() in ("id", "count", "index"):
        mutations.extend(ID_MUTATIONS)

    if _RE_FINANCIAL.search(param_name):
        mutations.extend(FINANCIAL_MUTATIONS)

    return mutations if mutations else list(_DEFAULT_MUTATIONS)


def scan_constants(filepath: str) -> dict[str, object]:
    """Scan *filepath* for UPPERCASE module-level constant assignments.

    Returns a mapping of constant name → literal value.  Only names that are
    entirely uppercase (``SCREAMING_SNAKE_CASE``) and whose values can be
    resolved as Python literals via ``ast.literal_eval`` are included.
    Parsing or IO errors are swallowed and an empty dict is returned.
    """
    constants: dict[str, object] = {}
    try:
        source: str = Path(filepath).read_text(encoding="utf-8")
        tree: ast.Module = ast.parse(source, filename=filepath)
    except (OSError, SyntaxError):
        return constants

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not (isinstance(target, ast.Name) and target.id.isupper()):
                continue
            try:
                value: object = ast.literal_eval(node.value)
                constants[target.id] = value
            except (ValueError, TypeError):
                pass

    return constants


def generate_mutations(
    param_name: str,
    constants: dict[str, object] | None = None,
) -> list[object]:
    """Generate the full mutation list for *param_name*, including discovered constants.

    Combines the classifier-based mutations with any UPPERCASE constants
    scanned from neighbouring source files.
    """
    mutations: list[object] = get_mutations_for_param(param_name)
    if constants:
        mutations.extend(constants.values())
    return mutations
