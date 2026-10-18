"""A data-only typed IR and total, bounded interpreter. No eval, exec, imports, I/O."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass


class IRViolation(ValueError):
    pass


@dataclass(frozen=True)
class Limits:
    max_ops: int = 512
    max_bits: int = 64
    max_depth: int = 8
    max_nodes: int = 64


def canonical_bytes(obj: object) -> bytes:
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode()


def canonical_hash(obj: object) -> str:
    return hashlib.sha256(canonical_bytes(obj)).hexdigest()


def check_tree(node: dict, base: dict) -> str:
    """Returns output type; validates every branch and shape statically."""
    limit_depth, limit_nodes = base["max_ast_depth"], base["max_ast_nodes"]
    seen = [0]

    def walk(v, depth):
        seen[0] += 1
        if seen[0] > limit_nodes or depth > limit_depth:
            raise IRViolation("AST resource limit")
        if not isinstance(v, dict) or not isinstance(v.get("op"), str):
            raise IRViolation("invalid node")
        op = v["op"]
        if op not in base["allowed_primitives"]:
            raise IRViolation(f"op not allowed: {op}")
        if op == "Arg":
            if set(v) != {"op", "index"} or type(v["index"]) is not int or v["index"] not in (0, 1):
                raise IRViolation("invalid argument")
            return "Int"
        if op == "ConstInt":
            if (
                set(v) != {"op", "value"}
                or type(v["value"]) is not int
                or v["value"] not in base["allowed_constants"]
            ):
                raise IRViolation("invalid constant")
            return "Int"
        if set(v) != {"op", "args"} or not isinstance(v["args"], list):
            raise IRViolation("invalid children")
        expected = {
            "Add": ("Int", "Int"),
            "Sub": ("Int", "Int"),
            "LessThan": ("Int", "Int"),
            "Equal": ("Int", "Int"),
            "If": ("Bool", "Int", "Int"),
        }.get(op)
        if expected is None or len(v["args"]) != len(expected):
            raise IRViolation("wrong arity")
        actual = tuple(walk(child, depth + 1) for child in v["args"])
        if actual != expected:
            raise IRViolation(f"type error: expected {expected}, got {actual}")
        return "Bool" if op in ("LessThan", "Equal") else "Int"

    result = walk(node, 1)
    if result != "Int":
        raise IRViolation("root must be Int")
    return result


def run_ir(
    node: dict, x: int, y: int, limits: Limits = Limits(), ops_counter: list[int] | None = None
) -> int:
    """Evaluate only whitelisted IR; callers should statically check once first."""
    if type(x) is not int or type(y) is not int:
        raise IRViolation("integer inputs required")
    operations = [0]

    def bound(v):
        if type(v) is int and v.bit_length() > limits.max_bits:
            raise IRViolation("integer bit limit")
        return v

    def execute(v, depth):
        operations[0] += 1
        if (
            operations[0] > limits.max_ops
            or depth > limits.max_depth
            or operations[0] > limits.max_nodes
        ):
            raise IRViolation("interpreter budget exceeded")
        op = v["op"]
        if op == "Arg":
            return bound((x, y)[v["index"]])
        if op == "ConstInt":
            return bound(v["value"])
        if op == "If":
            pred = execute(v["args"][0], depth + 1)
            return execute(v["args"][1] if pred else v["args"][2], depth + 1)
        a = execute(v["args"][0], depth + 1)
        b = execute(v["args"][1], depth + 1)
        if op == "Add":
            return bound(a + b)
        if op == "Sub":
            return bound(a - b)
        if op == "LessThan":
            return a < b
        if op == "Equal":
            return a == b
        raise IRViolation("unrecognized opcode")

    try:
        return bound(execute(node, 1))
    finally:
        if ops_counter is not None:
            ops_counter[0] += operations[0]


def render_python(node: dict, base: dict) -> str:
    """Export readable source from validated IR; NEVER executes the exported text.

    Exported Python does not enforce CIN interpreter budgets; verification and
    experiment claims apply to the CIN-IR interpreter, not unrestricted hosts.
    """
    check_tree(node, base)

    def emit(n):
        op = n["op"]
        if op == "Arg":
            return ("x", "y")[n["index"]]
        if op == "ConstInt":
            return str(n["value"])
        args = n["args"]
        if op == "If":
            return f"({emit(args[1])} if {emit(args[0])} else {emit(args[2])})"
        operator = {"Add": "+", "Sub": "-", "LessThan": "<", "Equal": "=="}[op]
        return f"({emit(args[0])} {operator} {emit(args[1])})"

    return (
        "# Generated from a verified CIN-IR artifact.\n"
        "# This export is not the bounded CIN runtime.\n"
        "def solve(x: int, y: int) -> int:\n"
        f"    return {emit(node)}\n"
    )
