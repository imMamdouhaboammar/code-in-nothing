"""Deterministic typed structural exploration; no task answers or pretrained models."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from itertools import product

from .ir import IRViolation, canonical_hash, check_tree


@dataclass(frozen=True)
class Proposal:
    expression: dict
    operator: str
    parent_hash: str
    rng_seed: int


def candidate_stream(
    parent: dict, base: dict, seed: int = 0, max_proposals: int = 2000
) -> Iterator[Proposal]:
    """Small bounded grammar enumerator + compositional perturbation of the parent.

    Seed determines a stable traversal permutation of binary operations without
    changing the coverage of the small core grammar.
    """
    parent_hash = canonical_hash(parent)
    seen = {parent_hash}
    produced = 0
    leaves = [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 1}]
    leaves.extend({"op": "ConstInt", "value": x} for x in base["allowed_constants"])

    def candidates():
        for leaf in leaves:
            yield (leaf, "replace_subtree")
        for op in ("Add", "Sub") if seed % 2 == 0 else ("Sub", "Add"):
            for a, b in product(leaves, repeat=2):
                yield ({"op": op, "args": [a, b]}, "compose_subtree")
        for op in ("LessThan", "Equal"):
            for a, b in product(leaves, repeat=2):
                predicate = {"op": op, "args": [a, b]}
                for then, otherwise in product(leaves, repeat=2):
                    yield ({"op": "If", "args": [predicate, then, otherwise]}, "insert_conditional")
        # Parent-based transformations, not unbounded source-code editing.
        for leaf in leaves:
            for op in ("Add", "Sub"):
                yield ({"op": op, "args": [parent, leaf]}, "compose_subtree")
                yield ({"op": op, "args": [leaf, parent]}, "compose_subtree")
        for a, b in product(leaves[:2], repeat=2):
            for leaf in leaves:
                yield (
                    {"op": "If", "args": [{"op": "LessThan", "args": [a, b]}, parent, leaf]},
                    "insert_conditional",
                )
                yield (
                    {"op": "If", "args": [{"op": "LessThan", "args": [a, b]}, leaf, parent]},
                    "insert_conditional",
                )

    for expression, operator in candidates():
        hash_ = canonical_hash(expression)
        if hash_ in seen:
            continue
        seen.add(hash_)
        try:
            check_tree(expression, base)
        except IRViolation:
            continue
        yield Proposal(expression, operator, parent_hash, seed)
        produced += 1
        if produced >= max_proposals:
            break
