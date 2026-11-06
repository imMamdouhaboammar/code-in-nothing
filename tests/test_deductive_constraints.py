"""Tests and soundness verification for deductive relational constraints."""

from __future__ import annotations

from itertools import product

from cin.contracts import load_world
from cin.synthesis import (
    Interval,
    compute_relational_target_sets,
    deduce_inverse_obligations,
    deductive_filter_binary_pairs,
    soundly_prunes_binary_op,
)


def test_interval_soundness():
    int_a = Interval(10, 20)
    int_b = Interval(5, 10)
    target = Interval(50, 100)

    # Add: [15, 30] vs [50, 100] -> Disjoint!
    assert soundly_prunes_binary_op("Add", int_a, int_b, target) is True

    # When target overlaps [15, 30] -> Must NOT prune
    target_overlap = Interval(25, 40)
    assert soundly_prunes_binary_op("Add", int_a, int_b, target_overlap) is False


def test_relational_target_sets_max2():
    world = load_world("examples/world-max2.v0.1.yaml")
    cases = ((2, 3), (5, 1), (-1, -1))
    target_sets = compute_relational_target_sets(cases, world, search_range=(-8, 8))

    assert len(target_sets) == 3
    # For (2, 3), max is 3
    assert 3 in target_sets[0]
    assert 2 not in target_sets[0]
    # For (5, 1), max is 5
    assert 5 in target_sets[1]
    # For (-1, -1), max is -1
    assert -1 in target_sets[2]


def test_incomplete_target_sampling_never_prunes_valid_arithmetic():
    world = load_world("examples/world-max2.v0.1.yaml")
    cases = ((100, 0),)
    sampled_targets = compute_relational_target_sets(cases, world)
    assert sampled_targets[0] == set()
    valid_left = [{"op": "Arg", "index": 0}]
    valid_right = [{"op": "ConstInt", "value": 0}]
    retained = deductive_filter_binary_pairs(
        "Add",
        valid_left,
        valid_right,
        cases,
        sampled_targets,
        arity=2,
    )
    assert len(retained) == 1


def test_deduce_inverse_obligations():
    admissible = {7, 10}
    # Add: L + R in {7, 10} => when L = 3, R in {4, 7}
    obligations = deduce_inverse_obligations("Add", 3, admissible)
    assert obligations == {4, 7}

    # Sub: L - R in {7, 10} => when L = 12, R in {5, 2}
    obligations_sub = deduce_inverse_obligations("Sub", 12, admissible)
    assert obligations_sub == {5, 2}


def test_deductive_filter_binary_pairs_soundness():
    cases = tuple(product(range(1, 4), range(1, 4)))
    # Target: x + y + 20
    # True terms: x, y, ConstInt(20)
    terms = [
        {"op": "Arg", "index": 0},
        {"op": "Arg", "index": 1},
        {"op": "ConstInt", "value": 0},
        {"op": "ConstInt", "value": 1},
    ]
    target_sets = [{pt[0] + pt[1] + 20} for pt in cases]

    # None of these pairs can produce x + y + 20, because terms output <= 4, sum <= 8 << 20!
    admissible = deductive_filter_binary_pairs("Add", terms, terms, cases, target_sets, arity=2)
    # Soundly pruned all pairs!
    assert len(admissible) == 0


def test_deductive_filter_retains_valid_solution():
    cases = tuple(product(range(1, 4), range(1, 4)))
    # Target: x + y
    left_terms = [{"op": "Arg", "index": 0}]
    right_terms = [{"op": "Arg", "index": 1}]
    target_sets = [{pt[0] + pt[1]} for pt in cases]

    admissible = deductive_filter_binary_pairs(
        "Add", left_terms, right_terms, cases, target_sets, arity=2
    )
    # Must retain (Arg(0), Arg(1))
    assert len(admissible) == 1
    assert admissible[0] == (left_terms[0], right_terms[0])
