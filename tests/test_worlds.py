from copy import deepcopy
from pathlib import Path

from cin.contracts import load_genome, load_world
from cin.ir import Limits
from cin.worlds import (
    admit_world,
    expand_domain,
    verify_program,
)

ROOT = Path(__file__).resolve().parents[1]
BASE = load_genome(ROOT / "examples/seed-genome.v0.1.yaml")["genome"]["base"]
WORLD = load_world(ROOT / "examples/world-max2.v0.1.yaml")
MAX = {
    "op": "If",
    "args": [
        {"op": "LessThan", "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 1}]},
        {"op": "Arg", "index": 1},
        {"op": "Arg", "index": 0},
    ],
}


def test_formal_spec_proves_max_on_declared_finite_domain():
    verdict = verify_program(MAX, WORLD, BASE, Limits())
    assert verdict.status == "PASS"
    assert verdict.checked == 289


def test_seed_does_not_satisfy_max():
    verdict = verify_program({"op": "Arg", "index": 0}, WORLD, BASE, Limits())
    assert verdict.status == "FAIL"
    assert verdict.counterexample is not None


def test_world_admission_finds_private_witness_from_grammar():
    result = admit_world(WORLD, BASE, max_proposals=250, max_cases=400)
    assert result.status == "ADMITTED", result.reason
    assert result.witness_hash
    assert not hasattr(result, "witness_program")


def test_unsatisfiable_task_is_not_admitted():
    world = deepcopy(WORLD)
    world["postcondition"] = {"and": [{"eq": ["result", 0]}, {"eq": ["result", 1]}]}
    result = admit_world(world, BASE, max_proposals=250, max_cases=400)
    assert result.status in ("REJECTED", "UNKNOWN")
    assert not result.witness_hash


def test_invalid_domain_is_not_admitted():
    world = deepcopy(WORLD)
    world["input_domain"]["x"]["max"] = 99999
    result = admit_world(world, BASE, max_proposals=10, max_cases=400)
    assert result.status == "REJECTED"


def test_mutated_world_is_new_admissible_formal_spec():
    modified = expand_domain(WORLD, 1)
    assert modified["id"] != WORLD["id"]
    assert modified["input_domain"]["x"]["min"] == -9
    assert admit_world(modified, BASE, max_proposals=250, max_cases=500).status == "ADMITTED"


def test_precondition_cannot_depend_on_program_result():
    import pytest

    from cin.contracts import ContractError, validate_world

    world = deepcopy(WORLD)
    world["precondition"] = {"eq": ["result", 0]}
    with pytest.raises(ContractError):
        validate_world(world)


def test_postcondition_cannot_be_trivial_without_result():
    import pytest

    from cin.contracts import ContractError, validate_world

    world = deepcopy(WORLD)
    world["postcondition"] = {"eq": ["x", "x"]}
    with pytest.raises(ContractError):
        validate_world(world)
