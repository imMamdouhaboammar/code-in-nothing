"""Regression tests for exploratory, threshold-free discovery and heldout isolation."""

from __future__ import annotations

import pytest

pytest.importorskip("z3")

from cin.ir import canonical_hash
from cin.synthesis.cegis import CEGISResult, run_cegis_loop
from cin.synthesis.decision import SynthesisWork
from cin.synthesis.open_discovery import (
    OPEN_PILOT_HOLDOUT,
    OPEN_PILOT_TRAIN,
    discover_open_macros,
    validate_open_manifest,
)
from cin.synthesis.sygus import get_sygus_task
from cin.synthesis.z3_verifier import Z3Verdict
from experiments.run_open_discovery_pilot import (
    build_distractors,
    counted_work,
    make_base_config,
    make_sum_task,
    split_macro_ablation,
)


def _result(expression: dict | None, status: str = "PROVED") -> CEGISResult:
    return CEGISResult(
        status=status,
        expression=expression,
        iterations=1,
        z3_verdict=Z3Verdict(
            "SYMBOLIC_PROVED" if status == "PROVED" else "COUNTEREXAMPLE",
            "cin.verifier/z3-smt-lia-v0.1",
        ),
    )


def test_work_ledger_counts_all_instrumented_search_categories():
    work = SynthesisWork(
        primitive_subterms=3,
        primitive_predicates=4,
        probe_evaluations=5,
        auxiliary_scoring_steps=6,
    )
    result = CEGISResult(
        status="EXHAUSTED",
        expression=None,
        iterations=1,
        total_shapes_attempted=7,
        verifier_invocations=2,
    )
    assert counted_work(work, result) == 27


def test_stress_construction_is_reproducible_and_has_20_distractions():
    first = build_distractors()
    second = build_distractors()
    assert len(first) == 20
    assert first.to_dict() == second.to_dict()
    for arity in (5, 8):
        task = make_sum_task(arity)
        assert task.arity == arity
        assert task.reference_oracle(*range(arity)) == sum(range(arity))


def test_cegis_exposes_full_work_and_verifier_accounting():
    work = SynthesisWork()
    result = run_cegis_loop(
        get_sygus_task("max2"),
        make_base_config(2),
        max_rounds=3,
        work=work,
    )
    assert result.status == "PROVED"
    assert work.primitive_subterms > 0
    assert work.primitive_predicates > 0
    assert work.probe_evaluations >= result.total_evaluations
    assert result.verifier_invocations >= 1
    assert result.verifier_elapsed_ms >= 0


def test_manifest_is_disjoint_and_covers_current_catalog():
    validate_open_manifest(OPEN_PILOT_TRAIN, OPEN_PILOT_HOLDOUT)
    assert set(OPEN_PILOT_TRAIN).isdisjoint(OPEN_PILOT_HOLDOUT)


@pytest.mark.parametrize(
    ("train", "holdout"),
    [
        (("max2",), ("max2",)),
        (("max2", "unknown_task"), ("min2",)),
        ((), ("max2",)),
        (("max2",), ()),
    ],
)
def test_invalid_manifest_is_rejected(train, holdout):
    with pytest.raises(ValueError):
        validate_open_manifest(train, holdout)


def test_discovers_int_subtrees_even_when_they_occur_once():
    expr = {
        "op": "If",
        "args": [
            {"op": "LessThan", "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 1}]},
            {"op": "Sub", "args": [{"op": "Arg", "index": 1}, {"op": "Arg", "index": 0}]},
            {"op": "Arg", "index": 0},
        ],
    }
    registry, counters = discover_open_macros([("arbitrary_training_id", _result(expr))])
    bodies = [m.body for m in registry.list_macros()]
    assert expr in bodies  # whole-program reuse without named, hand-authored macros
    assert {"op": "Sub", "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 1}]} in bodies
    assert all(
        m.metadata["origin_task_ids"] == ["arbitrary_training_id"] for m in registry.list_macros()
    )
    assert all(m.name.startswith("discovered_") for m in registry.list_macros())
    assert counters["subtrees_visited"] >= len(bodies)
    assert counters["type_rejected"] >= 1  # LessThan returns Bool
    whole, proper = split_macro_ablation(registry.to_dict())
    assert len(whole) == 1
    assert any(m["body"]["op"] == "Sub" for m in proper.values())
    assert set(whole).isdisjoint(proper)


def test_excludes_unproved_and_missing_proof_results():
    bad = _result({"op": "Arg", "index": 0}, status="EXHAUSTED")
    forged = CEGISResult(status="PROVED", expression={"op": "Arg", "index": 0}, iterations=1)
    registry, counters = discover_open_macros([("bad", bad), ("missing", forged)])
    assert len(registry) == 0
    assert counters["programs_accepted"] == 0


def test_is_deterministic_and_deduplicates_normalized_subtrees():
    first = {"op": "Sub", "args": [{"op": "Arg", "index": 1}, {"op": "Arg", "index": 0}]}
    second = {"op": "Sub", "args": [{"op": "Arg", "index": 2}, {"op": "Arg", "index": 1}]}
    r1, _ = discover_open_macros([("training_A", _result(first)), ("training_B", _result(second))])
    r2, _ = discover_open_macros([("training_A", _result(first)), ("training_B", _result(second))])
    assert r1.to_dict() == r2.to_dict()
    pairs = [m for m in r1.list_macros() if m.body["op"] == "Sub"]
    assert len(pairs) == 1
    assert pairs[0].metadata["origin_task_ids"] == ["training_A", "training_B"]
    assert pairs[0].origin_hash == canonical_hash(pairs[0].body)
