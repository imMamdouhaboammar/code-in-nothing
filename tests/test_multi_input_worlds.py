"""Tests for multi-input formal worlds (cin.world/v0.3)."""

from __future__ import annotations

import json
from itertools import product
from pathlib import Path

import pytest

from cin.contracts import ContractError, load_genome, load_world, validate_world
from cin.synthesis import synthesize_conditional_tree
from cin.worlds import verify_program


@pytest.mark.parametrize(
    "path",
    ["examples/world-absdiff.v0.2.yaml", "examples/world-clamp3.v0.3.yaml"],
)
def test_result_name_is_reserved_for_output_only(path):
    world = load_world(path)
    input_name = next(iter(world["input_domain"]))
    world["input_domain"]["result"] = world["input_domain"].pop(input_name)
    with pytest.raises(ContractError):
        validate_world(world)


def test_v03_schema_mirror_matches_package_contract():
    repo_root = Path(__file__).resolve().parents[1]
    package_schema = json.loads((repo_root / "cin/schemas/world-spec.v0.3.schema.json").read_text())
    mirrored_schema = json.loads((repo_root / "schemas/world-spec.v0.3.schema.json").read_text())
    assert mirrored_schema == package_schema


def test_legacy_world_input_positions_ignore_yaml_key_order():
    world = load_world("examples/world-max2.v0.1.yaml")
    old_domain = world["input_domain"]
    world["input_domain"] = {"y": old_domain["y"], "x": old_domain["x"]}
    world["postcondition"] = {"eq": ["result", "x"]}
    base = load_genome("examples/seed-genome.v0.1.yaml")["genome"]["base"]
    verdict = verify_program({"op": "Arg", "index": 0}, world, base)
    assert verdict.status == "PASS"


def test_validate_and_verify_clamp3_world():
    world = load_world("examples/world-clamp3.v0.3.yaml")
    assert world["api_version"] == "cin.world/v0.3"
    assert len(world["input_domain"]) == 3

    genome = load_genome("examples/seed-genome.v0.2.yaml")
    base = dict(genome["genome"]["base"])
    base["cin_ir_version"] = "0.2"
    base["input_types"] = ["Int", "Int", "Int"]
    base["max_ast_depth"] = 8
    base["max_ast_nodes"] = 32

    # A valid clamp(x, low, high) expression:
    # If(x < low, low, If(high < x, high, x))
    clamp_expr = {
        "op": "If",
        "args": [
            {"op": "LessThan", "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 1}]},
            {"op": "Arg", "index": 1},
            {
                "op": "If",
                "args": [
                    {
                        "op": "LessThan",
                        "args": [{"op": "Arg", "index": 2}, {"op": "Arg", "index": 0}],
                    },
                    {"op": "Arg", "index": 2},
                    {"op": "Arg", "index": 0},
                ],
            },
        ],
    }

    verdict = verify_program(clamp_expr, world, base)
    assert verdict.status == "PASS"
    assert verdict.checked > 0


def test_clamp3_invalid_candidate_fails_with_counterexample():
    world = load_world("examples/world-clamp3.v0.3.yaml")
    genome = load_genome("examples/seed-genome.v0.2.yaml")
    base = dict(genome["genome"]["base"])
    base["cin_ir_version"] = "0.2"
    base["input_types"] = ["Int", "Int", "Int"]

    # Candidate just returns x without clamping
    bad_expr = {"op": "Arg", "index": 0}
    verdict = verify_program(bad_expr, world, base)
    assert verdict.status == "FAIL"
    assert verdict.counterexample is not None
    assert len(verdict.counterexample) == 3


def test_synthesize_and_verify_clamp3_world():
    world = load_world("examples/world-clamp3.v0.3.yaml")
    genome = load_genome("examples/seed-genome.v0.2.yaml")
    base = dict(genome["genome"]["base"])
    base["cin_ir_version"] = "0.2"
    base["input_types"] = ["Int", "Int", "Int"]
    base["max_ast_depth"] = 8
    base["max_ast_nodes"] = 32

    raw_cases = tuple(product(range(-2, 3), range(-2, 3), range(-2, 3)))
    cases = tuple(pt for pt in raw_cases if pt[1] <= pt[2])

    res = synthesize_conditional_tree(cases, world, base)
    assert res is not None

    verdict = verify_program(res.expression, world, base)
    assert verdict.status == "PASS"


def test_verify_median3_world():
    world = load_world("examples/world-median3.v0.3.yaml")
    assert world["api_version"] == "cin.world/v0.3"
    assert len(world["input_domain"]) == 3

    genome = load_genome("examples/seed-genome.v0.2.yaml")
    base = dict(genome["genome"]["base"])
    base["cin_ir_version"] = "0.2"
    base["input_types"] = ["Int", "Int", "Int"]
    base["max_ast_depth"] = 8
    base["max_ast_nodes"] = 64

    cases = tuple(product(range(-2, 3), range(-2, 3), range(-2, 3)))

    def median_oracle(pt: tuple[int, ...], val: int) -> bool:
        s = sorted(pt)
        return val == s[1]

    subterms = [{"op": "Arg", "index": i} for i in range(3)]
    preds = [
        {"op": "LessThan", "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 1}]},
        {"op": "LessThan", "args": [{"op": "Arg", "index": 1}, {"op": "Arg", "index": 2}]},
        {"op": "LessThan", "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 2}]},
        {"op": "LessThan", "args": [{"op": "Arg", "index": 1}, {"op": "Arg", "index": 0}]},
        {"op": "LessThan", "args": [{"op": "Arg", "index": 2}, {"op": "Arg", "index": 1}]},
        {"op": "LessThan", "args": [{"op": "Arg", "index": 2}, {"op": "Arg", "index": 0}]},
    ]

    res = synthesize_conditional_tree(
        cases, median_oracle, base, subterms=subterms, predicates=preds
    )
    assert res is not None

    verdict = verify_program(res.expression, world, base)
    assert verdict.status == "PASS"
    assert verdict.checked == 125
