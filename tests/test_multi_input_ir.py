"""M2 regression contracts: legacy two-input IR and versioned N-input IR."""

from copy import deepcopy
from pathlib import Path

import pytest

from cin.contracts import ContractError, load_genome, validate_genome
from cin.ir import IRViolation, Limits, check_tree, render_python, run_ir, run_ir_args

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
    assert "def solve(x: int, y: int) -> int:" in render_python(
        {"op": "Arg", "index": 0}, base
    )
