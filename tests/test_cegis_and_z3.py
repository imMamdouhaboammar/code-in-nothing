"""Tests for Z3 SMT Verification, CEGIS Loop, and Neuro-Symbolic Agent Kernel."""

import pytest

from cin.synthesis import (
    HAS_Z3,
    MacroRegistry,
    NeuroSymbolicAgentKernel,
    cin_to_z3,
    get_sygus_task,
    run_cegis_loop,
    verify_equivalence_with_z3,
    verify_spec_with_z3,
)

if not HAS_Z3:
    pytest.skip("z3-solver is not available", allow_module_level=True)

import z3

BASE_2D = {
    "cin_ir_version": "0.1",
    "organism_class": "test",
    "input_types": ["Int", "Int"],
    "return_type": "Int",
    "starting_expression": {"op": "Arg", "index": 0},
    "allowed_primitives": ["Arg", "ConstInt", "Add", "Sub", "LessThan", "Equal", "If"],
    "allowed_constants": [0, 1],
    "max_ast_depth": 7,
    "max_ast_nodes": 25,
    "invariants": ["typed", "pure", "deterministic", "resource_bounded"],
}

BASE_3D = {
    "cin_ir_version": "0.2",
    "organism_class": "test",
    "input_types": ["Int", "Int", "Int"],
    "return_type": "Int",
    "starting_expression": {"op": "Arg", "index": 0},
    "allowed_primitives": ["Arg", "ConstInt", "Add", "Sub", "LessThan", "Equal", "If"],
    "allowed_constants": [0, 1],
    "max_ast_depth": 7,
    "max_ast_nodes": 25,
    "invariants": ["typed", "pure", "deterministic", "resource_bounded"],
}

MAX2_IR_1 = {
    "op": "If",
    "args": [
        {"op": "LessThan", "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 1}]},
        {"op": "Arg", "index": 1},
        {"op": "Arg", "index": 0},
    ],
}

MAX2_IR_2 = {
    "op": "If",
    "args": [
        {"op": "LessThan", "args": [{"op": "Arg", "index": 1}, {"op": "Arg", "index": 0}]},
        {"op": "Arg", "index": 0},
        {"op": "Arg", "index": 1},
    ],
}

MIN2_IR = {
    "op": "If",
    "args": [
        {"op": "LessThan", "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 1}]},
        {"op": "Arg", "index": 0},
        {"op": "Arg", "index": 1},
    ],
}


class TestZ3TranslationAndVerification:
    def test_cin_to_z3_translation(self):
        x, y = z3.Int("x"), z3.Int("y")
        z3_expr = cin_to_z3(MAX2_IR_1, [x, y])
        # Check evaluation: for x=3, y=7, max is 7
        solver = z3.Solver()
        solver.add(x == 3, y == 7)
        res_var = z3.Int("res")
        solver.add(res_var == z3_expr)
        assert solver.check() == z3.sat
        model = solver.model()
        assert model[res_var].as_long() == 7

    def test_verify_spec_with_z3_proved(self):
        task_max2 = get_sygus_task("max2")
        verdict = verify_spec_with_z3(
            MAX2_IR_1,
            task_max2.z3_spec,
            arity=2,
            var_names=task_max2.variable_names,
        )
        assert verdict.status == "SYMBOLIC_PROVED"
        assert verdict.counterexample is None

    def test_verify_spec_with_z3_counterexample(self):
        task_max2 = get_sygus_task("max2")
        flawed_max = {"op": "Arg", "index": 0}  # returns x always
        verdict = verify_spec_with_z3(
            flawed_max,
            task_max2.z3_spec,
            arity=2,
            var_names=task_max2.variable_names,
        )
        assert verdict.status == "COUNTEREXAMPLE"
        assert verdict.counterexample is not None
        cx, cy = verdict.counterexample
        assert cx < cy  # Counterexample proves x < y where identity fails

    def test_verify_equivalence_with_z3(self):
        verdict = verify_equivalence_with_z3(MAX2_IR_1, MAX2_IR_2, arity=2)
        assert verdict.status == "SYMBOLIC_PROVED"

        diff_verdict = verify_equivalence_with_z3(MAX2_IR_1, MIN2_IR, arity=2)
        assert diff_verdict.status == "COUNTEREXAMPLE"

    def test_duplicate_z3_variable_names_cannot_prove_aliasing(self):
        verdict = verify_spec_with_z3(
            {"op": "Arg", "index": 0},
            lambda values, output: output == values[1],
            arity=2,
            var_names=["same", "same"],
        )
        assert verdict.status == "UNKNOWN"
        assert verdict.counterexample is None

    def test_median3_rejects_first_input_as_universal_answer(self):
        task = get_sygus_task("median3")
        verdict = verify_spec_with_z3(
            {"op": "Arg", "index": 0},
            task.z3_spec,
            arity=3,
            var_names=task.variable_names,
        )
        assert verdict.status == "COUNTEREXAMPLE"
        assert verdict.counterexample is not None
        x, y, z = verdict.counterexample
        assert x != sorted((x, y, z))[1]


class TestCEGISLoop:
    def test_cegis_loop_solves_max2(self):
        task_max2 = get_sygus_task("max2")
        result = run_cegis_loop(task_max2, BASE_2D, max_rounds=5)
        assert result.status == "PROVED"
        assert result.expression is not None
        assert result.iterations >= 1
        assert result.z3_verdict is not None
        assert result.z3_verdict.status == "SYMBOLIC_PROVED"

    def test_cegis_filters_out_of_precondition_seeds(self):
        from dataclasses import replace

        task = replace(
            get_sygus_task("max2"),
            initial_seed_cases=((0, 1),),
            precondition=lambda values: values[0] == values[1],
        )
        result = run_cegis_loop(task, BASE_2D, max_rounds=4)
        assert result.status == "PROVED"
        assert all(x == y for x, y in result.counterexamples)

    def test_cegis_reports_zero_rounds_if_timeout_prevents_start(self):
        result = run_cegis_loop(get_sygus_task("max2"), BASE_2D, timeout_sec=-1)
        assert result.status == "EXHAUSTED"
        assert result.iterations == 0

    def test_cegis_loop_solves_absdiff(self):
        task_abs = get_sygus_task("absdiff")
        result = run_cegis_loop(task_abs, BASE_2D, max_rounds=5)
        assert result.status == "PROVED"
        assert result.expression is not None
        assert result.z3_verdict.status == "SYMBOLIC_PROVED"


def test_blind_baseline_reports_measured_zero_budget():
    from experiments.run_cegis_sygus_benchmark import (
        make_base_config,
        measure_blind_baseline,
    )

    status, shapes, elapsed_ms = measure_blind_baseline(
        get_sygus_task("max2"), make_base_config(2), max_proposals=0
    )
    assert status == "EXHAUSTED"
    assert shapes == 0
    assert elapsed_ms >= 0


class TestNeuroSymbolicKernel:
    def test_intuitive_sketch_must_respect_genome_base(self):
        kernel = NeuroSymbolicAgentKernel()
        kernel.register_verified_tool("max2", 2, MAX2_IR_1, "test")
        restricted_base = dict(BASE_3D)
        restricted_base["allowed_primitives"] = ["Arg", "Add"]
        verdict = kernel.solve_and_verify(
            get_sygus_task("max3"), restricted_base, max_cegis_rounds=0
        )
        assert verdict.status != "SYMBOLIC_PROVED"
        assert "max3" not in kernel.verified_tools

    def test_caller_supplied_empty_registry_is_preserved(self):
        registry = MacroRegistry()
        kernel = NeuroSymbolicAgentKernel(registry)
        assert kernel.registry is registry

    def test_neuro_symbolic_generational_inheritance(self):
        kernel = NeuroSymbolicAgentKernel()

        # Generation 0: Solve max2 and min2, inheriting them into kernel
        task_max2 = get_sygus_task("max2")
        v_max = kernel.solve_and_verify(task_max2, BASE_2D)
        assert v_max.status == "SYMBOLIC_PROVED"
        assert "max2" in kernel.verified_tools

        task_min2 = get_sygus_task("min2")
        v_min = kernel.solve_and_verify(task_min2, BASE_2D)
        assert v_min.status == "SYMBOLIC_PROVED"
        assert "min2" in kernel.verified_tools

        # Generation 1: Solve clamp3 via intuitive sketch using inherited max2 & min2
        task_clamp = get_sygus_task("clamp3")
        v_clamp = kernel.solve_and_verify(task_clamp, BASE_3D, try_intuitive_prior=True)
        assert v_clamp.status == "SYMBOLIC_PROVED"
        assert v_clamp.provenance == "intuitive_sketch"
        assert "clamp3" in kernel.verified_tools

        # Generation 2: Solve max3 via intuitive sketch using inherited max2
        task_max3 = get_sygus_task("max3")
        v_max3 = kernel.solve_and_verify(task_max3, BASE_3D, try_intuitive_prior=True)
        assert v_max3.status == "SYMBOLIC_PROVED"
        assert v_max3.provenance == "intuitive_sketch"
        assert "max3" in kernel.verified_tools
