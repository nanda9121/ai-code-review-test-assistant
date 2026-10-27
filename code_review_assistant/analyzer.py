"""Lightweight, local checks for common Python issues."""

import ast
from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    severity: str
    title: str
    line: int
    explanation: str
    suggestion: str


class _ReviewVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.findings: list[Finding] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        for default in node.args.defaults:
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                self.findings.append(
                    Finding(
                        severity="high",
                        title="Mutable default argument",
                        line=default.lineno,
                        explanation=(
                            f"`{node.name}` uses a mutable object as a default "
                            "argument; that object is shared between calls."
                        ),
                        suggestion="Use `None` as the default and create the object inside the function.",
                    )
                )
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.type is None:
            self.findings.append(
                Finding(
                    severity="medium",
                    title="Bare except clause",
                    line=node.lineno,
                    explanation="This handler catches every exception, including exceptions the code may not expect.",
                    suggestion="Catch the specific exception types that can be handled here.",
                )
            )
        if not node.body or all(isinstance(item, ast.Pass) for item in node.body):
            self.findings.append(
                Finding(
                    severity="medium",
                    title="Exception is ignored",
                    line=node.lineno,
                    explanation="This exception handler discards the error without reporting or handling it.",
                    suggestion="Handle the error or log enough context to diagnose it.",
                )
            )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec"}:
            self.findings.append(
                Finding(
                    severity="high",
                    title=f"Dynamic execution with {node.func.id}",
                    line=node.lineno,
                    explanation=f"`{node.func.id}` executes dynamically supplied code and can be difficult to reason about.",
                    suggestion="Prefer explicit parsing or dispatch logic where possible.",
                )
            )
        self.generic_visit(node)


def analyze_python(source: str) -> list[Finding]:
    """Return local heuristic findings; this function never executes source code."""
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        return [
            Finding(
                severity="high",
                title="Python syntax error",
                line=error.lineno or 1,
                explanation=error.msg,
                suggestion="Correct the syntax error before running or testing this code.",
            )
        ]

    visitor = _ReviewVisitor()
    visitor.visit(tree)
    return visitor.findings
