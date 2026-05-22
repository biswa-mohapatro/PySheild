"""AST Code Investigator — extracts function metadata from Python source files."""

import ast
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FunctionInfo:
    """Metadata extracted for a single function definition."""

    name: str
    lineno: int
    params: list[str]
    annotations: dict[str, str] = field(default_factory=dict)


def parse_file(filepath: str) -> list[FunctionInfo]:
    """Parse *filepath* and return metadata for every function defined in it.

    Reads the file as UTF-8 text, builds a Python AST, and walks it to locate
    ``ast.FunctionDef`` nodes.  The ``self`` and ``cls`` parameters are
    discarded from every parameter list before returning.

    Raises:
        RuntimeError: If the file cannot be read (OS/IO error) or contains a
            syntax error that prevents parsing.
    """
    path = Path(filepath)
    try:
        source: str = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"Cannot read file {filepath}: {exc}") from exc

    try:
        tree: ast.Module = ast.parse(source, filename=filepath)
    except SyntaxError as exc:
        raise RuntimeError(f"Syntax error in {filepath}: {exc}") from exc

    functions: list[FunctionInfo] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        params: list[str] = []
        annotations: dict[str, str] = {}

        for arg in node.args.args:
            if arg.arg in ("self", "cls"):
                continue
            params.append(arg.arg)
            if arg.annotation is not None:
                annotations[arg.arg] = ast.unparse(arg.annotation)

        if node.returns is not None:
            annotations["return"] = ast.unparse(node.returns)

        functions.append(
            FunctionInfo(
                name=node.name,
                lineno=node.lineno,
                params=params,
                annotations=annotations,
            )
        )

    return functions
