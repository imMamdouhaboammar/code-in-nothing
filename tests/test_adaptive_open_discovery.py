"""Adaptive open-discovery search: opt-in grammar expansion and resource supervision."""

from __future__ import annotations

from dataclasses import replace

import pytest

pytest.importorskip("z3")

from cin.ir import Limits, canonical_hash
from cin.synthesis.cegis import run_cegis_loop
from cin.synthesis.decision import (
    SynthesisSearchConfig,
    SynthesisWork,
    generate_candidate_subterms,
)
from cin.synthesis.library import Macro, MacroRegistry
from cin.synthesis.sygus import get_sygus_task
from experiments.run_adaptive_open_discovery import (
    ADAPTIVE_STAGES,
    choose_adaptive_stages,
    run_progressive_attempts,
    run_supervised_stage,
)
from experiments.run_open_discovery_pilot import make_base_config


@pytest.fixture
def ternary_sum_registry() -> MacroRegistry:
    body = {
        "op": "Add",
        "args": [
            {
                "op": "Add",
                "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 1}],
            },
            {"op": "Arg", "index": 2},
        ],
    }
    return MacroRegistry({"ternary": Macro("ternary", 3, body, canonical_hash(body))})


def test_default_generator_does_not_change_arity_behavior(ternary_sum_registry):
    cases = ((1, 2, 4), (7, 3, 1), (-2, 5, 9))
    subterms = generate_candidate_subterms(
        3,
        {"Arg"},
        [],
        cases,
        max_depth=2,
        limits=Limits(max_depth=8),
        macro_registry=ternary_sum_registry,
    )
    assert all(node["op"] != "CallMacro" for node in subterms)


def test_opt_in_generator_can_use_discovered_ternary_macros(ternary_sum_registry):
    cases = ((1, 2, 4), (7, 3, 1), (-2, 5, 9))
    work = SynthesisWork()
    subterms = generate_candidate_subterms(
        3,
        {"Arg"},
        [],
        cases,
        max_depth=2,
        limits=Limits(max_depth=8),
        macro_registry=ternary_sum_registry,
        work=work,
        max_macro_arity=3,
        macro_combination_limit=40,
    )
    assert any(node["op"] == "CallMacro" and len(node["args"]) == 3 for node in subterms)
    assert 1 <= work.macro_combinations_tried <= 40


def test_per_macro_combination_budget_counts_rejected_proposals(ternary_sum_registry):
    cases = ((1, 2, 4), (7, 3, 1))
    work = SynthesisWork()
    generate_candidate_subterms(
        3,
        {"Arg"},
        [],
        cases,
        max_depth=2,
        macro_registry=ternary_sum_registry,
        work=work,
        max_macro_arity=3,
        macro_combination_limit=1,
    )
    assert work.macro_combinations_tried == 1


def test_nullary_macro_is_optional_and_counted():
    body = {"op": "ConstInt", "value": 2}
    macros = MacroRegistry({"const": Macro("const", 0, body, canonical_hash(body))})
    work = SynthesisWork()
    generate_candidate_subterms(
        2,
        {"Arg", "ConstInt"},
        [0, 1, 2],
        ((0, 0), (1, 2)),
        max_depth=2,
        macro_registry=macros,
        work=work,
        include_nullary_macros=True,
    )
    assert work.macro_combinations_tried >= 1


@pytest.mark.parametrize(
    "settings",
    [
        {"subterm_depth": 0},
        {"predicate_term_depth": -1},
        {"max_macro_arity": 9},
        {"max_macro_arity": 0},
        {"macro_combination_limit": 0},
        {"branch_attempt_limit": 0},
    ],
)
def test_invalid_search_configs_rejected(settings):
    with pytest.raises(ValueError):
        SynthesisSearchConfig(**settings)


def test_cegis_accepts_opt_in_search_config_without_changing_proof():
    task = get_sygus_task("max2")
    config = SynthesisSearchConfig(
        subterm_depth=3,
        predicate_term_depth=2,
        max_macro_arity=3,
        macro_combination_limit=100,
        branch_attempt_limit=512,
    )
    result = run_cegis_loop(task, make_base_config(2), max_rounds=4, search_config=config)
    assert result.status == "PROVED"
    assert result.z3_verdict is not None
    assert result.z3_verdict.status == "SYMBOLIC_PROVED"


def test_progression_monotonically_expands_search_options():
    assert len(ADAPTIVE_STAGES) == 3
    for before, after in zip(ADAPTIVE_STAGES, ADAPTIVE_STAGES[1:]):
        assert before.ast_depth < after.ast_depth
        assert before.ast_nodes < after.ast_nodes
        assert before.search.subterm_depth < after.search.subterm_depth
        assert before.search.max_macro_arity < after.search.max_macro_arity
    assert sum(stage.wall_seconds for stage in ADAPTIVE_STAGES) == 10
    assert ADAPTIVE_STAGES[0].wall_seconds == 3
    assert ADAPTIVE_STAGES[-1].search.macro_combination_limit is None
    assert ADAPTIVE_STAGES[-1].search.branch_attempt_limit is None
    assert choose_adaptive_stages(ADAPTIVE_STAGES) == ADAPTIVE_STAGES


def test_progressive_schedule_stops_on_first_proof():
    visited = []

    def solve(stage):
        visited.append(stage.name)
        return {
            "status": "PROVED" if stage.name == "P1" else "EXHAUSTED",
            "elapsed_ms": 10,
        }

    attempts = run_progressive_attempts(ADAPTIVE_STAGES, solve)
    assert visited == ["P0", "P1"]
    assert [step["status"] for step in attempts] == ["EXHAUSTED", "PROVED"]


def test_progression_stops_after_memory_exhaustion():
    def solve(stage):
        return {"status": "MEMOUT", "elapsed_ms": 10}

    attempts = run_progressive_attempts(ADAPTIVE_STAGES, solve)
    assert len(attempts) == 1
    assert attempts[0]["status"] == "MEMOUT"


def test_supervised_stage_preserves_independent_proof():
    result = run_supervised_stage("max2", {}, ADAPTIVE_STAGES[0], rss_limit_mib=256)
    assert result["status"] == "PROVED"
    assert result["proof"] == "SYMBOLIC_PROVED"
    assert result["verifier_invocations"] >= 1
    assert result["peak_rss_mib"] > 0
    assert result["process_wall_ms"] > 0


def test_supervised_stage_timeout_does_not_fabricate_partial_counts():
    tiny = replace(ADAPTIVE_STAGES[0], name="tiny_timeout", wall_seconds=0.001)
    result = run_supervised_stage("max2", {}, tiny)
    assert result["status"] == "TIMEOUT"
    assert result["work_units"] is None
    assert result["verifier_invocations"] is None


def test_supervised_stage_memory_ceiling_interrupts_worker():
    result = run_supervised_stage("max2", {}, ADAPTIVE_STAGES[0], rss_limit_mib=1)
    assert result["status"] == "MEMOUT"
    assert result["work_units"] is None
    assert result["peak_rss_mib"] > 1


def test_supervisor_fails_closed_if_memory_is_not_observable(monkeypatch):
    import psutil

    class InaccessibleMemory:
        def memory_info(self):
            raise psutil.AccessDenied(pid=9876)

    monkeypatch.setattr(psutil, "Process", lambda pid: InaccessibleMemory())
    result = run_supervised_stage("max2", {}, ADAPTIVE_STAGES[0], rss_limit_mib=256)
    assert result["status"] == "WORKER_FAILED"
    assert result["work_units"] is None
    assert "RSS" in result["note"]
