"""Tier-1 mathematical capability tests with task-blind candidate generation."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from cin.contracts import ContractError, load_genome, load_world, validate_world
from cin.ir import Limits, canonical_hash, check_tree, run_ir
from cin.search import candidate_stream
from cin.worlds import check_formula, verify_program

ROOT = Path(__file__).resolve().parents[1]
BASE = load_genome(ROOT / "examples/seed-genome.v0.1.yaml")["genome"]["base"]
MIN2 = load_world(ROOT / "examples/world-min2.v0.1.yaml")
ABSDIFF = load_world(ROOT / "examples/world-absdiff.v0.2.yaml")

# Training-side screening reduces full-world verifier calls. Neither these
# examples nor the world object is passed to candidate_stream.
SCREEN = ((-4, -1), (1, -4), (0, 0), (-2, 3), (3, -2), (4, 4))


def discover(world: dict, budget: int) -> tuple[int, dict] | None:
    for count, proposal in enumerate(
        candidate_stream(BASE["starting_expression"], BASE, seed=0, max_proposals=budget), 1
    ):
        expression = proposal.expression
        if not all(
            check_formula(
                world["postcondition"],
                {"x": x, "y": y, "result": run_ir(expression, x, y)},
            )
            for x, y in SCREEN
        ):
            continue
        # The final verdict sees the complete 81-point formal world.
        verdict = verify_program(expression, world, BASE, max_cases=81)
        if verdict.status == "PASS":
            assert verdict.checked == 81
            return count, expression
    return None


@pytest.mark.parametrize("world,budget", [(MIN2, 250), (ABSDIFF, 30000)])
def test_synthesizes_from_formal_spec_without_oracle_injection(world, budget):
    result = discover(world, budget)
    assert result is not None, f"no verified solution within {budget} proposals"
    count, expression = result
    assert 0 < count <= budget
    assert check_tree(expression, BASE) == "Int"
    assert verify_program(expression, world, BASE).status == "PASS"


def test_legacy_contract_rejects_arithmetic_terms():
    legacy = deepcopy(ABSDIFF)
    legacy["api_version"] = "cin.world/v0.1"
    with pytest.raises(ContractError):
        validate_world(legacy)


def test_versioned_subtraction_rejects_unrecognized_operations():
    invalid = deepcopy(ABSDIFF)
    invalid["postcondition"]["or"][0]["and"][1] = {
        "eq": ["result", {"abs": {"sub": ["x", "y"]}}]
    }
    with pytest.raises(ContractError):
        validate_world(invalid)


def test_signed_direction_and_ties_are_mathematically_constrained():
    subtract = {
        "op": "Sub",
        "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 1}],
    }
    assert verify_program(subtract, ABSDIFF, BASE).status == "FAIL"
    assert verify_program({"op": "Arg", "index": 0}, MIN2, BASE).status == "FAIL"
    assert check_formula(
        ABSDIFF["postcondition"], {"x": -4, "y": 2, "result": 6}
    )
    assert not check_formula(
        ABSDIFF["postcondition"], {"x": -4, "y": 2, "result": -6}
    )


def test_cost_layers_determinism_and_no_duplicate_asts():
    first = list(candidate_stream(BASE["starting_expression"], BASE, seed=3, max_proposals=250))
    replay = list(candidate_stream(BASE["starting_expression"], BASE, seed=3, max_proposals=250))
    assert len(first) == 250
    assert [p.expression for p in first] == [p.expression for p in replay]
    assert len({canonical_hash(p.expression) for p in first}) == len(first)

    def size(node):
        return 1 + sum(size(child) for child in node.get("args", ()))

    assert [size(p.expression) for p in first] == sorted(
        size(p.expression) for p in first
    )
    assert all(check_tree(p.expression, BASE) == "Int" for p in first)


def test_forbidden_primitives_and_strict_bounds():
    base = deepcopy(BASE)
    base["allowed_primitives"] = ["Arg", "ConstInt", "Sub"]
    base["max_ast_depth"] = 2
    base["max_ast_nodes"] = 3
    candidates = list(candidate_stream(base["starting_expression"], base, max_proposals=1000))
    assert candidates
    assert all(check_tree(p.expression, base) == "Int" for p in candidates)
    assert all(p.expression["op"] != "If" for p in candidates)
    assert list(candidate_stream(base["starting_expression"], base, max_proposals=0)) == []


def test_finite_verification_is_not_an_unbounded_proof():
    expression = discover(MIN2, 250)
    assert expression is not None
    count, candidate = expression
    assert count > 0
    assert verify_program(candidate, MIN2, BASE, Limits(), max_cases=80).status == "INVALID"
