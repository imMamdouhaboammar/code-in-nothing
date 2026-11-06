"""Tests for information-theoretic conditional program synthesis."""

from __future__ import annotations

from copy import deepcopy
from itertools import product

from cin.contracts import load_genome, load_world, validate_world
from cin.ir import Limits, run_ir_args
from cin.synthesis import (
    generate_candidate_predicates,
    synthesize_conditional_tree,
)
from cin.worlds import verify_program


def test_synthesize_max2():
    genome = load_genome("examples/seed-genome.v0.1.yaml")
    world = load_world("examples/world-max2.v0.1.yaml")
    base = genome["genome"]["base"]
    cases = tuple(product(range(-3, 4), range(-3, 4)))

    res = synthesize_conditional_tree(cases, world, base)
    assert res is not None
    assert res.nodes <= 7
    assert res.depth <= 3

    verdict = verify_program(res.expression, world, base)
    assert verdict.status == "PASS"


def test_synthesize_min2():
    genome = load_genome("examples/seed-genome.v0.1.yaml")
    world_max = load_world("examples/world-max2.v0.1.yaml")
    base = genome["genome"]["base"]

    world_min = deepcopy(world_max)
    world_min["id"] = "cin.world.logic.min2.001"
    world_min["postcondition"] = {
        "and": [
            {"lte": ["result", "x"]},
            {"lte": ["result", "y"]},
            {"or": [{"eq": ["result", "x"]}, {"eq": ["result", "y"]}]},
        ]
    }
    validate_world(world_min)
    cases = tuple(product(range(-3, 4), range(-3, 4)))

    res = synthesize_conditional_tree(cases, world_min, base)
    assert res is not None
    assert res.nodes <= 7

    verdict = verify_program(res.expression, world_min, base)
    assert verdict.status == "PASS"


def test_synthesize_abs_diff():
    genome = load_genome("examples/seed-genome.v0.1.yaml")
    base = dict(genome["genome"]["base"])
    base["allowed_primitives"] = list(set(base["allowed_primitives"]) | {"Sub"})
    base["max_ast_depth"] = 8
    base["max_ast_nodes"] = 32

    cases = tuple(product(range(-3, 4), range(-3, 4)))

    def abs_diff_oracle(pt: tuple[int, ...], val: int) -> bool:
        return val == abs(pt[0] - pt[1])

    res = synthesize_conditional_tree(cases, abs_diff_oracle, base)
    assert res is not None
    assert res.depth <= 4

    limits = Limits()
    for pt in cases:
        val = run_ir_args(res.expression, pt, limits, expected_arity=2)
        assert val == abs(pt[0] - pt[1])


def test_synthesize_clamp_3_vars():
    genome = load_genome("examples/seed-genome.v0.1.yaml")
    base = dict(genome["genome"]["base"])
    base["cin_ir_version"] = "0.2"
    base["input_types"] = ["Int", "Int", "Int"]
    base["max_ast_depth"] = 8
    base["max_ast_nodes"] = 32

    raw_cases = tuple(product(range(-2, 3), range(-2, 3), range(-2, 3)))
    cases = tuple(pt for pt in raw_cases if pt[1] <= pt[2])

    def clamp_oracle(pt: tuple[int, ...], val: int) -> bool:
        x, low, high = pt
        return val == min(max(x, low), high)

    res = synthesize_conditional_tree(cases, clamp_oracle, base)
    assert res is not None

    limits = Limits()
    for pt in cases:
        val = run_ir_args(res.expression, pt, limits, expected_arity=3)
        assert val == min(max(pt[0], pt[1]), pt[2])


def test_synthesize_direct_arithmetic_without_conditional():
    genome = load_genome("examples/seed-genome.v0.1.yaml")
    base = genome["genome"]["base"]
    cases = tuple(product(range(-3, 4), range(-3, 4)))

    # Target: x + y
    targets = tuple(x + y for x, y in cases)
    res = synthesize_conditional_tree(cases, targets, base)
    assert res is not None
    # Must be direct Add, not wrapped in If
    assert res.expression["op"] == "Add"


def test_synthesize_impossible_target_returns_none():
    genome = load_genome("examples/seed-genome.v0.1.yaml")
    base = genome["genome"]["base"]
    cases = tuple(product(range(1, 4), range(1, 4)))

    # Target: 1000 (Unreachable within AST depth/constant bounds)
    targets = tuple(1000 for _ in cases)
    res = synthesize_conditional_tree(cases, targets, base)
    assert res is None


def test_synthesize_empty_cases():
    genome = load_genome("examples/seed-genome.v0.1.yaml")
    base = genome["genome"]["base"]
    assert synthesize_conditional_tree((), (), base) is None


def test_generate_predicates_filters_trivial():
    cases = tuple(product(range(-2, 3), range(-2, 3)))
    terms = [
        {"op": "Arg", "index": 0},
        {"op": "Arg", "index": 1},
        {"op": "ConstInt", "value": 0},
    ]
    preds = generate_candidate_predicates(terms, {"LessThan", "Equal"}, cases, arity=2)
    # Trivial relations (x < x, x == x) must not be present
    for p in preds:
        args = p["args"]
        assert args[0] != args[1]
