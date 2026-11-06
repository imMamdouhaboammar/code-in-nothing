"""Tests for information-theoretic conditional program synthesis."""

from __future__ import annotations

import hashlib
from copy import deepcopy
from itertools import product

import pytest

from cin.contracts import load_genome, load_world, validate_world
from cin.ir import Limits, run_ir_args
from cin.synthesis import (
    decision,
    generate_candidate_predicates,
    synthesize_conditional_tree,
)
from cin.worlds import verify_program
from experiments import adversarial_harness, run_decision_synthesis


def test_failed_world_verification_does_not_claim_finite_proof(monkeypatch):
    from cin.worlds import Verdict

    candidate = {"op": "Arg", "index": 0}
    monkeypatch.setattr(
        run_decision_synthesis,
        "synthesize_conditional_tree",
        lambda *args, **kwargs: decision.DecisionResult(candidate, 1, 1, 1, 1),
    )
    monkeypatch.setattr(
        run_decision_synthesis, "verify_program", lambda *args: Verdict("INVALID", 0)
    )
    result = run_decision_synthesis._measure_task({"id": "invalid"}, {}, ((0,),))
    assert result["verifier_calls"] == 1
    assert result["status"] == "INVALID"
    assert result["proof_scope"] == "none"


def test_benchmark_checkout_can_prepare_and_verify_write_locks(tmp_path, monkeypatch):
    target = tmp_path / "schemas/sample.json"
    target.parent.mkdir()
    target.write_text("test payload", encoding="utf-8")
    manifest = tmp_path / ".benchmarks/checksums.sha256"
    manifest.parent.mkdir()
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    manifest.write_text(f"{digest}  schemas/sample.json\n", encoding="utf-8")
    monkeypatch.setattr(adversarial_harness, "ROOT", tmp_path)

    with pytest.raises(PermissionError):
        adversarial_harness.verify_filesystem_integrity()
    adversarial_harness.prepare_benchmark_write_locks()
    assert target.stat().st_mode & 0o222 == 0
    adversarial_harness.verify_filesystem_integrity()


def test_benchmark_lock_setup_rejects_tampered_inputs(tmp_path, monkeypatch):
    target = tmp_path / "sample.json"
    target.write_text("tampered", encoding="utf-8")
    manifest = tmp_path / ".benchmarks/checksums.sha256"
    manifest.parent.mkdir()
    manifest.write_text(f"{'0' * 64}  sample.json\n", encoding="utf-8")
    monkeypatch.setattr(adversarial_harness, "ROOT", tmp_path)

    with pytest.raises(ValueError, match="TAMPERING_DETECTED"):
        adversarial_harness.prepare_benchmark_write_locks()
    assert target.stat().st_mode & 0o200


def test_world_target_search_never_calls_verifier_formula_helpers(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("synthesis depended on verifier internals")

    monkeypatch.setattr(decision, "check_formula", forbidden, raising=False)
    monkeypatch.setattr(decision, "_ordered_input_names", forbidden, raising=False)
    world = load_world("examples/world-clamp3.v0.3.yaml")
    base = deepcopy(load_genome("examples/seed-genome.v0.1.yaml")["genome"]["base"])
    base["cin_ir_version"] = "0.2"
    base["input_types"] = ["Int"] * 3
    result = decision.synthesize_conditional_tree(
        ((0, -1, 1),),
        world,
        base,
        subterms=[{"op": "Arg", "index": 0}],
        predicates=[],
    )
    assert result is not None
    assert result.expression == {"op": "Arg", "index": 0}


def test_high_arity_stress_probes_vary_each_input_independently():
    cases = adversarial_harness.make_high_arity_cases(8)
    assert len(cases) >= 24
    assert all(len(case) == 8 for case in cases)
    for axis in range(8):
        assert len({case[axis] for case in cases}) >= 3
    assert any(len(set(case)) > 1 for case in cases)


def test_decision_benchmark_json_contains_actual_cost_accounting():
    report = run_decision_synthesis.run_decision_experiments()
    assert len(report["results"]) == 3
    for row in report["results"]:
        assert row["primitive_subterms"] > 0
        assert row["primitive_predicates"] > 0
        assert row["probe_evaluations"] > 0
        assert row["auxiliary_scoring_steps"] >= 0
        assert row["verifier_calls"] in (0, 1)
        assert row["verifier_time_ms"] >= 0
        assert row["wall_clock_ms"] >= 0
        assert row["process_peak_rss_kb"] > 0
        assert "naive_search_shapes" not in row


def test_adversarial_harness_reports_measured_generation_work():
    base = dict(load_genome("examples/seed-genome.v0.1.yaml")["genome"]["base"])
    world = load_world("examples/world-min2.v0.1.yaml")
    _, cost = adversarial_harness.instrumented_synthesize(world, base, timeout_sec=5)
    assert cost.primitive_subterms > 0
    assert cost.primitive_predicates > 0
    assert cost.probe_evaluations >= cost.primitive_subterms
    assert cost.auxiliary_scoring_steps >= 0


def test_generation_work_counts_candidates_before_observational_pruning():
    base = dict(load_genome("examples/seed-genome.v0.1.yaml")["genome"]["base"])
    work = decision.SynthesisWork()
    cases = tuple(product((-1, 0, 1), repeat=2))
    result = synthesize_conditional_tree(cases, tuple(max(x, y) for x, y in cases), base, work=work)
    assert result is not None
    assert work.primitive_subterms > 0
    assert work.primitive_predicates > 0
    assert work.probe_evaluations >= result.candidate_evaluations
    assert work.primitive_subterms >= work.subterm_representatives
    assert work.primitive_predicates >= work.predicate_representatives


def test_induction_backtracks_when_highest_scoring_split_is_unsolvable():
    genome = load_genome("examples/seed-genome.v0.1.yaml")
    base = dict(genome["genome"]["base"])
    base["cin_ir_version"] = "0.2"
    base["input_types"] = ["Int"]
    base["max_ast_depth"] = 5
    base["max_ast_nodes"] = 30
    base["allowed_constants"] = [0, 1, 2, 3]
    arg = {"op": "Arg", "index": 0}

    def const(value):
        return {"op": "ConstInt", "value": value}

    preds = [
        {"op": "Equal", "args": [arg, const(0)]},
        {"op": "LessThan", "args": [arg, const(2)]},
        {"op": "LessThan", "args": [arg, const(3)]},
    ]
    cases = tuple((x,) for x in range(6))
    targets = (2, 0, 1, 0, 0, 0)
    result = synthesize_conditional_tree(
        cases,
        targets,
        base,
        subterms=[const(0), const(1), const(2)],
        predicates=preds,
        max_tree_depth=4,
    )
    assert result is not None
    for case, expected in zip(cases, targets):
        assert run_ir_args(result.expression, case, Limits(), expected_arity=1) == expected


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


def test_max_tree_depth_limits_direct_arithmetic():
    genome = load_genome("examples/seed-genome.v0.1.yaml")
    base = dict(genome["genome"]["base"])
    cases = ((1, 2), (3, 4), (5, 6))
    arg0, arg1 = {"op": "Arg", "index": 0}, {"op": "Arg", "index": 1}
    addition = {"op": "Add", "args": [arg0, arg1]}
    result = synthesize_conditional_tree(
        cases,
        (3, 7, 11),
        base,
        subterms=[arg0, arg1, addition],
        predicates=[],
        max_tree_depth=1,
    )
    assert result is None


def test_world_precondition_excludes_invalid_cases_before_routing():
    base = dict(load_genome("examples/seed-genome.v0.1.yaml")["genome"]["base"])
    arg0 = {"op": "Arg", "index": 0}
    world = {
        "input_domain": {"x": {"min": -1, "max": 0}, "y": {"min": 0, "max": 1}},
        "precondition": {"gte": ["x", 0]},
        "postcondition": {"eq": ["result", 0]},
    }
    result = synthesize_conditional_tree(
        ((-1, 1), (0, 1)),
        world,
        base,
        subterms=[arg0],
        predicates=[],
    )
    assert result is not None
    assert result.expression == arg0


def test_missing_nested_macro_does_not_crash_subterm_generation():
    from cin.synthesis.library import Macro, MacroRegistry

    bad = Macro(
        name="bad",
        arity=1,
        body={
            "op": "CallMacro",
            "macro": "missing",
            "args": [
                {"op": "Arg", "index": 0},
            ],
        },
        origin_hash="adversarial-test",
    )
    terms = decision.generate_candidate_subterms(
        arity=2,
        allowed={"Arg", "Add"},
        constants=[],
        probe_cases=((1, 2), (3, 4)),
        max_depth=2,
        macro_registry=MacroRegistry({"bad": bad}),
    )
    assert {"op": "Arg", "index": 0} in terms
