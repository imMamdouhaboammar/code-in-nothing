"""Deterministic cost-layered typed search without task or verifier feedback."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass
from itertools import product

from .ir import IRViolation, Limits, canonical_hash, check_tree, run_ir_args

# Search-only probes are fixed independently of all formal worlds and targets.
# Equivalence here is a heuristic for pruning, never a correctness certificate.
_PROBES = tuple(product(range(-3, 4), repeat=2))


def _probe_inputs(arity: int) -> tuple[tuple[int, ...], ...]:
    """Fixed task-independent observations. These are not equivalence proofs."""
    if arity == 2:
        return _PROBES
    # Cover each axis, plus bounded mixed tuples; never form a 7**arity grid.
    probes = [tuple([value] * arity) for value in range(-3, 4)]
    for index in range(arity):
        for value in range(-3, 4):
            point = [0] * arity
            point[index] = value
            probes.append(tuple(point))
    for sample in range(49):
        probes.append(
            tuple(
                ((sample // (7 ** (index % 2)) + sample * (index + 1) + 2 * index) % 7) - 3
                for index in range(arity)
            )
        )
    return tuple(dict.fromkeys(probes))


@dataclass(frozen=True)
class Proposal:
    expression: dict
    operator: str
    parent_hash: str
    rng_seed: int


@dataclass
class SearchStats:
    """Mutable measurements of search work, not a fitness or proof signal."""

    attempted_shapes: int = 0
    observational_prunes: int = 0
    integer_representatives: int = 0
    boolean_representatives: int = 0


@dataclass(frozen=True)
class _Entry:
    expression: dict
    values: tuple
    depth: int


def _size_depth(node: dict) -> tuple[int, int]:
    children = node.get("args", ())
    if not children:
        return 1, 1
    dimensions = [_size_depth(child) for child in children]
    return 1 + sum(size for size, _ in dimensions), 1 + max(depth for _, depth in dimensions)


def candidate_stream(
    parent: dict,
    base: dict,
    seed: int = 0,
    max_proposals: int = 2000,
    stats: SearchStats | None = None,
) -> Iterator[Proposal]:
    """Enumerate typed expressions by AST node count, with bounded work.

    Int and Bool subterms are memoized by fixed-probe observational signatures.
    All externally yielded candidates are valid Int trees, and no world, task
    answer, verifier witness, or failed-candidate feedback enters this search.
    Finite probes may conflate distinct functions outside the probes: only the
    independent world verifier may declare a candidate correct.
    """
    if type(max_proposals) is not int or max_proposals < 1:
        return
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    check_tree(parent, base)
    arity = len(base.get("input_types", ("Int", "Int")))
    probes = _probe_inputs(arity)
    parent_hash = canonical_hash(parent)
    limits = Limits(
        max_depth=base["max_ast_depth"],
        max_nodes=base["max_ast_nodes"],
        max_ops=max(512, base["max_ast_nodes"]),
    )
    bank: dict[str, dict[int, list[_Entry]]] = {
        "Int": defaultdict(list),
        "Bool": defaultdict(list),
    }
    signatures: dict[str, set[tuple]] = {"Int": set(), "Bool": set()}
    allowed = set(base["allowed_primitives"])
    max_depth = base["max_ast_depth"]
    max_nodes = base["max_ast_nodes"]
    # Count attempted intermediate shapes too, including discarded duplicates.
    # This prevents a small output budget from hiding unbounded internal work.
    max_shapes = max(3000, 100 * max_proposals)
    shapes = 0
    produced = 0

    def add(kind: str, size: int, expr: dict, values: tuple, depth: int) -> bool:
        if depth > max_depth:
            return False
        if values in signatures[kind]:
            if stats is not None:
                stats.observational_prunes += 1
            return False
        if kind == "Bool" and len(signatures["Bool"]) >= max_proposals:
            return False
        signatures[kind].add(values)
        bank[kind][size].append(_Entry(expr, values, depth))
        if stats is not None:
            if kind == "Bool":
                stats.boolean_representatives += 1
            else:
                stats.integer_representatives += 1
        return True

    # Parent is available as a reusable expression at its honest syntax cost.
    size, depth = _size_depth(parent)
    try:
        observations = tuple(run_ir_args(parent, point, limits, expected_arity=arity) for point in probes)
    except IRViolation:
        observations = None
    if observations is not None and size <= max_nodes:
        add("Int", size, parent, observations, depth)

    leaves = []
    if "Arg" in allowed:
        leaves.extend({"op": "Arg", "index": i} for i in range(arity))
    if "ConstInt" in allowed:
        leaves.extend({"op": "ConstInt", "value": c} for c in base["allowed_constants"])
    for leaf in leaves:
        observations = tuple(
            point[leaf["index"]] if leaf["op"] == "Arg" else leaf["value"] for point in probes
        )
        if add("Int", 1, leaf, observations, 1):
            produced += 1
            yield Proposal(leaf, "replace_subtree", parent_hash, seed)
            if produced >= max_proposals:
                return

    arithmetic = ("Add", "Sub") if seed % 2 == 0 else ("Sub", "Add")
    operators = tuple(op for op in (*arithmetic, "LessThan", "Equal") if op in allowed)
    for size in range(2, max_nodes + 1):
        # Every binary child has strictly lower cost than its parent.
        for left_size in range(1, size - 1):
            right_size = size - 1 - left_size
            for left in bank["Int"][left_size]:
                for right in bank["Int"][right_size]:
                    depth = 1 + max(left.depth, right.depth)
                    if depth > max_depth:
                        continue
                    for op in operators:
                        shapes += 1
                        if stats is not None:
                            stats.attempted_shapes = shapes
                        if shapes > max_shapes:
                            return
                        if op == "Add":
                            values = tuple(a + b for a, b in zip(left.values, right.values))
                        elif op == "Sub":
                            values = tuple(a - b for a, b in zip(left.values, right.values))
                        elif op == "LessThan":
                            values = tuple(a < b for a, b in zip(left.values, right.values))
                        else:
                            values = tuple(a == b for a, b in zip(left.values, right.values))
                        kind = "Bool" if op in ("LessThan", "Equal") else "Int"
                        expr = {"op": op, "args": [left.expression, right.expression]}
                        if not add(kind, size, expr, values, depth):
                            continue
                        if kind == "Int":
                            check_tree(expr, base)
                            produced += 1
                            yield Proposal(expr, "compose_subtree", parent_hash, seed)
                            if produced >= max_proposals:
                                return

        if "If" not in allowed:
            continue
        # Cost fairness includes both branches and the condition.
        for pred_size in range(1, size - 2):
            for then_size in range(1, size - 1 - pred_size):
                else_size = size - 1 - pred_size - then_size
                for pred in bank["Bool"][pred_size]:
                    for yes in bank["Int"][then_size]:
                        for no in bank["Int"][else_size]:
                            depth = 1 + max(pred.depth, yes.depth, no.depth)
                            if depth > max_depth:
                                continue
                            shapes += 1
                            if stats is not None:
                                stats.attempted_shapes = shapes
                            if shapes > max_shapes:
                                return
                            values = tuple(
                                a if p else b for p, a, b in zip(pred.values, yes.values, no.values)
                            )
                            expr = {
                                "op": "If",
                                "args": [pred.expression, yes.expression, no.expression],
                            }
                            if not add("Int", size, expr, values, depth):
                                continue
                            check_tree(expr, base)
                            produced += 1
                            yield Proposal(expr, "insert_conditional", parent_hash, seed)
                            if produced >= max_proposals:
                                return
