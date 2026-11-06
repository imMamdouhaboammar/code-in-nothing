"""Threshold-free exploratory program reuse from formally accepted training outcomes.

This module never names or selects candidate programs using target task identity.
It does not claim individual subtree correctness against an unseen specification.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from cin.ir import IRViolation, canonical_hash, check_tree

from .cegis import CEGISResult
from .library import Macro, MacroRegistry, ast_node_count, collect_subtrees, normalize_args
from .sygus import SYGUS_BENCHMARKS

OPEN_PILOT_TRAIN = ("max2", "min2", "absdiff")
OPEN_PILOT_HOLDOUT = ("max3", "min3", "clamp3", "median3", "max4")


def validate_open_manifest(train: tuple[str, ...], holdout: tuple[str, ...]) -> None:
    """Reject leakage, duplicate names, and an incomplete registry census."""
    if not train or not holdout:
        raise ValueError("Both task cohorts must contain at least one task")
    all_names = (*train, *holdout)
    if len(all_names) != len(set(all_names)):
        raise ValueError("Duplicate training/heldout task name")
    if set(all_names) != set(SYGUS_BENCHMARKS):
        raise ValueError("Frozen task split must cover exactly the registered SyGuS tasks")


def _type_check_discovery(node: dict, arity: int) -> bool:
    """Check only the interpreter's existing typed, data-only IR grammar."""
    constants: set[int] = set()

    def visit(subtree: dict) -> None:
        if subtree.get("op") == "ConstInt":
            constants.add(subtree["value"])
        for child in subtree.get("args", []):
            visit(child)

    visit(node)
    base = {
        "cin_ir_version": "0.2",
        "input_types": ["Int"] * max(1, arity),
        "return_type": "Int",
        "allowed_primitives": ["Arg", "ConstInt", "Add", "Sub", "LessThan", "Equal", "If"],
        "allowed_constants": sorted(constants),
        "max_ast_depth": ast_node_count(node),
        "max_ast_nodes": ast_node_count(node),
    }
    try:
        check_tree(node, base)
    except (IRViolation, TypeError, KeyError, ValueError):
        return False
    return True


def discover_open_macros(
    proved_training: Iterable[tuple[str, CEGISResult]],
) -> tuple[MacroRegistry, dict[str, int]]:
    """Keep every distinct typed integer subtree from proved training programs.

    No MDL threshold, recurrence threshold, task-name hint, size threshold, or
    observed-transfer gate is applied. Whole expressions are included.
    """
    counters = {
        "programs_seen": 0,
        "programs_accepted": 0,
        "subtrees_visited": 0,
        "type_rejected": 0,
        "unique_macros": 0,
        "duplicate_subtrees": 0,
    }
    candidates: dict[str, tuple[dict, int]] = {}
    origins: dict[str, set[str]] = defaultdict(set)
    complete_programs: set[str] = set()

    for task_id, result in proved_training:
        counters["programs_seen"] += 1
        if (
            result.status != "PROVED"
            or result.expression is None
            or result.z3_verdict is None
            or result.z3_verdict.status != "SYMBOLIC_PROVED"
        ):
            continue
        counters["programs_accepted"] += 1
        complete_programs.add(canonical_hash(normalize_args(result.expression)[0]))

        for subtree in collect_subtrees(result.expression, min_nodes=1):
            counters["subtrees_visited"] += 1
            normalized, arity = normalize_args(subtree)
            if not _type_check_discovery(normalized, arity):
                counters["type_rejected"] += 1
                continue
            fingerprint = canonical_hash(normalized)
            if fingerprint in candidates:
                counters["duplicate_subtrees"] += 1
            else:
                candidates[fingerprint] = (normalized, arity)
            origins[fingerprint].add(task_id)

    registry = MacroRegistry()
    for fingerprint, (body, arity) in sorted(candidates.items()):
        registry.register(
            Macro(
                name=f"discovered_{fingerprint[:16]}",
                arity=arity,
                body=body,
                origin_hash=fingerprint,
                description="Integer subtree reused from independently proved training program",
                metadata={
                    "origin_task_ids": sorted(origins[fingerprint]),
                    "discovery_mode": "all_typed_subtrees_no_threshold",
                    "search_usable": arity in (1, 2),
                    "complete_training_program": fingerprint in complete_programs,
                },
            )
        )
    counters["unique_macros"] = len(registry)
    return registry, counters
