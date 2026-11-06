"""Deductive constraint propagation and relational inverse semantics.

Implements set-based witness functions (FlashMeta style) for formal relational
specifications, proving sound pruning (zero false negatives) of impossible AST branches.
"""

from __future__ import annotations

from dataclasses import dataclass

from cin.ir import IRViolation, Limits, run_ir_args
from cin.worlds import _ordered_input_names, check_formula


@dataclass(frozen=True)
class Interval:
    """Closed integer interval [min_val, max_val]."""

    min_val: int
    max_val: int

    def contains(self, val: int) -> bool:
        return self.min_val <= val <= self.max_val

    def intersects(self, other: Interval) -> bool:
        return not (self.max_val < other.min_val or other.max_val < self.min_val)


class SampledTargetSet(set[int]):
    """Observed target values within a finite search window, not a complete set."""


@dataclass
class DeductiveStats:
    """Work counters for deductive constraint propagation."""

    pairs_screened: int = 0
    soundly_pruned: int = 0
    retained_pairs: int = 0


def compute_relational_target_sets(
    cases: tuple[tuple[int, ...], ...],
    world: dict,
    search_range: tuple[int, int] = (-16, 16),
) -> list[set[int]]:
    """Compute the set of admissible target values for each input case.

    Supports general relational specifications (multiple valid target outputs).
    """
    post = world["postcondition"]
    var_names = _ordered_input_names(world)
    target_sets: list[set[int]] = []

    for pt in cases:
        valid_values: set[int] = SampledTargetSet()
        values = {k: v for k, v in zip(var_names, pt)}
        for candidate_val in range(search_range[0], search_range[1] + 1):
            values["result"] = candidate_val
            if check_formula(post, values):
                valid_values.add(candidate_val)
        target_sets.append(valid_values)

    return target_sets


def compute_term_interval(
    term: dict,
    cases: tuple[tuple[int, ...], ...],
    arity: int,
    limits: Limits = Limits(),
) -> Interval | None:
    """Compute the closed output interval [min, max] for a term across given cases."""
    vals = []
    for pt in cases:
        try:
            vals.append(run_ir_args(term, pt, limits, expected_arity=arity))
        except IRViolation:
            return None
    if not vals:
        return None
    return Interval(min(vals), max(vals))


def soundly_prunes_binary_op(
    op: str,
    left_interval: Interval,
    right_interval: Interval,
    target_interval: Interval,
) -> bool:
    """Prove whether a binary composition can be soundly pruned via interval bounds.

    Returns True if and only if NO combination of values in left and right intervals
    can produce a value within target_interval.
    """
    if op == "Add":
        composed = Interval(
            left_interval.min_val + right_interval.min_val,
            left_interval.max_val + right_interval.max_val,
        )
    elif op == "Sub":
        composed = Interval(
            left_interval.min_val - right_interval.max_val,
            left_interval.max_val - right_interval.min_val,
        )
    else:
        return False

    # Disjoint intervals mean mathematical impossibility
    return not composed.intersects(target_interval)


def deduce_inverse_obligations(
    op: str,
    left_val: int,
    admissible_targets: set[int],
) -> set[int]:
    """Compute the exact set of required values for the right child (FlashMeta witness function)."""
    if op == "Add":
        # left + right = target => right = target - left
        return {t - left_val for t in admissible_targets}
    if op == "Sub":
        # left - right = target => right = left - target
        return {left_val - t for t in admissible_targets}
    return set()


def deductive_filter_binary_pairs(
    op: str,
    left_terms: list[dict],
    right_terms: list[dict],
    cases: tuple[tuple[int, ...], ...],
    target_sets: list[set[int]],
    arity: int,
    limits: Limits = Limits(),
    stats: DeductiveStats | None = None,
) -> list[tuple[dict, dict]]:
    """Filter binary term pairs using sound deductive interval and obligation constraints.

    Guarantees zero false negatives: any pruned pair is mathematically proven incapable
    of producing an admissible target on all points.
    """
    if not target_sets:
        return []

    # Finite output sampling cannot certify that an unobserved value is invalid.
    # Retain every pair unless every target set was supplied as an exact set.
    if any(isinstance(targets, SampledTargetSet) or not targets for targets in target_sets):
        all_pairs = [(left, right) for left in left_terms for right in right_terms]
        if stats is not None:
            stats.pairs_screened += len(all_pairs)
            stats.retained_pairs += len(all_pairs)
        return all_pairs

    # Exact target sets supplied by the caller permit interval-based pruning.
    all_targets = set.union(*target_sets)
    target_interval = Interval(min(all_targets), max(all_targets))

    # Precompute intervals for terms
    left_intervals = [compute_term_interval(t, cases, arity, limits) for t in left_terms]
    right_intervals = [compute_term_interval(t, cases, arity, limits) for t in right_terms]

    admissible_pairs: list[tuple[dict, dict]] = []
    screened = 0
    pruned = 0

    for i, left in enumerate(left_terms):
        int_l = left_intervals[i]
        if int_l is None:
            continue
        for j, right in enumerate(right_terms):
            screened += 1
            int_r = right_intervals[j]
            if int_r is None:
                continue

            # Stage 1: Fast interval pruning
            if soundly_prunes_binary_op(op, int_l, int_r, target_interval):
                pruned += 1
                continue

            admissible_pairs.append((left, right))

    if stats is not None:
        stats.pairs_screened += screened
        stats.soundly_pruned += pruned
        stats.retained_pairs += len(admissible_pairs)

    return admissible_pairs
