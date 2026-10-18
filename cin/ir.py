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


def _input_arity(base: dict) -> int:
    """Validate the versioned integer function signature without mutating the genome."""
    version = base.get("cin_ir_version", "0.1")
    parameters = base.get("input_types", ["Int", "Int"])
    if base.get("return_type", "Int") != "Int":
        raise IRViolation("unsupported return type")
    if version == "0.1":
        if parameters != ["Int", "Int"]:
            raise IRViolation("legacy IR requires exactly two Int arguments")
    elif version == "0.2":
        if not isinstance(parameters, list) or not 1 <= len(parameters) <= 8:
            raise IRViolation("IR v0.2 requires 1..8 parameters")
        if any(kind != "Int" for kind in parameters):
            raise IRViolation("unsupported parameter type")
    else:
        raise IRViolation("unsupported IR version")
    return len(parameters)


def check_tree(node: dict, base: dict) -> str:
    """Returns output type; validates every branch and shape statically."""
    arity = _input_arity(base)
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
            if (
                set(v) != {"op", "index"}
                or type(v["index"]) is not int
                or not 0 <= v["index"] < arity
            ):
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
    """Legacy two-argument entry point, preserving positional caller compatibility."""
    return run_ir_args(node, (x, y), limits, ops_counter, expected_arity=2)


def run_ir_args(
    node: dict,
    arguments: tuple[int, ...],
    limits: Limits = Limits(),
    ops_counter: list[int] | None = None,
    *,
    expected_arity: int,
) -> int:
    """Execute checked IR; callers with a declared signature must bind its arity."""
    if not isinstance(arguments, tuple) or not 1 <= len(arguments) <= 8:
        raise IRViolation("argument tuple must contain 1..8 inputs")
    if (
        type(expected_arity) is not int
        or not 1 <= expected_arity <= 8
        or len(arguments) != expected_arity
    ):
        raise IRViolation("arguments do not match declared function arity")
    if any(type(value) is not int for value in arguments):
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
            index = v["index"]
            if type(index) is not int or not 0 <= index < len(arguments):
                raise IRViolation("invalid argument index")
            return bound(arguments[index])
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
    arity = _input_arity(base)
    names = ("x", "y", "z", *(f"a{i}" for i in range(3, arity)))[:arity]

    def emit(n):
        op = n["op"]
        if op == "Arg":
            return names[n["index"]]
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
        "def solve(" + ", ".join(f"{name}: int" for name in names) + ") -> int:\n"
        f"    return {emit(node)}\n"
    )
