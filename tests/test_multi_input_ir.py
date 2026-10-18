"""M2 regression contracts: legacy two-input IR and versioned N-input IR."""

from copy import deepcopy
from pathlib import Path

import pytest

from cin.contracts import ContractError, load_genome, validate_genome
from cin.ir import IRViolation, Limits, check_tree, render_python, run_ir, run_ir_args
from cin.search import candidate_stream

ROOT = Path(__file__).resolve().parents[1]
LEGACY = load_genome(ROOT / "examples/seed-genome.v0.1.yaml")
ARG2 = {"op": "Arg", "index": 2}


def new_genome(arity=3):
    genome = deepcopy(LEGACY)
    genome["api_version"] = "cin.genome/v0.2"
    base = genome["genome"]["base"]
    base["cin_ir_version"] = "0.2"
    base["input_types"] = ["Int"] * arity
    return genome


def test_legacy_two_input_contract_stays_frozen():
    base = LEGACY["genome"]["base"]
    assert check_tree({"op": "Arg", "index": 1}, base) == "Int"
    with pytest.raises(IRViolation):
        check_tree(ARG2, base)
    with pytest.raises(ContractError):
        validate_genome({**LEGACY, "api_version": "cin.genome/v0.2"})


def test_three_argument_typed_program_is_checked_executed_and_exported():
    base = validate_genome(new_genome())["genome"]["base"]
    expression = {
        "op": "If",
        "args": [
            {"op": "LessThan", "args": [{"op": "Arg", "index": 0}, ARG2]},
            ARG2,
            {"op": "Sub", "args": [{"op": "Arg", "index": 1}, ARG2]},
        ],
    }
    assert check_tree(expression, base) == "Int"
    assert run_ir_args(expression, (1, 9, 4)) == 4
    assert run_ir_args(expression, (5, 9, 4)) == 5
    assert "def solve(x: int, y: int, z: int) -> int:" in render_python(expression, base)
    with pytest.raises(IRViolation):
        run_ir_args(expression, (1, 2))


def test_signature_is_not_hardcoded_to_three():
    base = validate_genome(new_genome(4))["genome"]["base"]
    arg3 = {"op": "Arg", "index": 3}
    assert check_tree(arg3, base) == "Int"
    assert run_ir_args(arg3, (-1, 5, 6, 17)) == 17
    assert "a3: int" in render_python(arg3, base)
    with pytest.raises(IRViolation):
        check_tree({"op": "Arg", "index": 4}, base)


@pytest.mark.parametrize("signature", [[], ["Bool", "Int", "Int"], ["Int"] * 9])
def test_invalid_input_signatures_rejected(signature):
    with pytest.raises(ContractError):
        validate_genome(new_genome_with_signature(signature))


def new_genome_with_signature(signature):
    genome = new_genome()
    genome["genome"]["base"]["input_types"] = signature
    return genome


def test_unsupported_versions_and_non_integer_runtime_inputs_fail_closed():
    genome = new_genome()
    genome["genome"]["base"]["cin_ir_version"] = "0.3"
    with pytest.raises(ContractError):
        validate_genome(genome)
    with pytest.raises(IRViolation):
        run_ir_args(ARG2, (1, True, 2))
    with pytest.raises(IRViolation):
        run_ir_args(ARG2, (1, 2, 3), Limits(max_ops=0))
    with pytest.raises(IRViolation):
        run_ir_args(ARG2, (1, 2, 2**70), Limits(max_bits=64))


def test_existing_call_signature_and_code_export_remain_unchanged():
    base = LEGACY["genome"]["base"]
    assert run_ir({"op": "Arg", "index": 0}, 3, 4) == 3
    assert "def solve(x: int, y: int) -> int:" in render_python({"op": "Arg", "index": 0}, base)


def test_multi_input_search_is_task_blind_deterministic_and_uses_third_argument():
    base = validate_genome(new_genome())["genome"]["base"]
    parent = {"op": "Arg", "index": 0}
    first = list(candidate_stream(parent, base, seed=0, max_proposals=80))
    second = list(candidate_stream(parent, base, seed=0, max_proposals=80))
    assert [item.expression for item in first] == [item.expression for item in second]
    assert {"op": "Arg", "index": 2} in [item.expression for item in first]
    assert all(check_tree(item.expression, base) == "Int" for item in first)
    assert len(first) == 80


def test_eight_argument_search_has_bounded_probe_work():
    base = validate_genome(new_genome(8))["genome"]["base"]
    expressions = [
        proposal.expression
        for proposal in candidate_stream({"op": "Arg", "index": 0}, base, max_proposals=12)
    ]
    assert {"op": "Arg", "index": 7} in expressions
    assert len(expressions) == 12


def test_legacy_lazy_projection_does_not_evaluate_unused_oversized_argument():
    projection = {"op": "Arg", "index": 0}
    assert run_ir(projection, 7, 2**128, Limits(max_bits=16)) == 7
