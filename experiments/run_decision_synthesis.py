"""Measured generation costs and finite-world outcomes for decision synthesis."""

from __future__ import annotations

import json
import time
from itertools import product
from pathlib import Path

from cin.contracts import load_genome, load_world
from cin.ir import canonical_hash
from cin.synthesis.decision import SynthesisWork, synthesize_conditional_tree
from cin.worlds import verify_program
from experiments.adversarial_harness import get_peak_rss_kb

ROOT = Path(__file__).resolve().parents[1]


def _measure_task(world: dict, base: dict, cases: tuple[tuple[int, ...], ...]) -> dict:
    """Account for generation, public probing, and independent finite verification."""
    work = SynthesisWork()
    started = time.perf_counter()
    result = synthesize_conditional_tree(cases, world, base, work=work)
    verifier_time_ms = 0.0
    verifier_calls = 0
    if result is None:
        status = "EXHAUSTED"
    else:
        verify_started = time.perf_counter()
        verdict = verify_program(result.expression, world, base)
        verifier_time_ms = (time.perf_counter() - verify_started) * 1000
        verifier_calls = 1
        status = verdict.status

    return {
        "task_id": world["id"],
        "status": status,
        "proof_scope": "finite_world" if verifier_calls else "none",
        "synthesized_ast": result.expression if result is not None else None,
        "candidate_hash": canonical_hash(result.expression) if result is not None else None,
        "ast_nodes": result.nodes if result is not None else None,
        "ast_depth": result.depth if result is not None else None,
        "synthesis_shapes_attempted": result.shapes_attempted if result is not None else None,
        "primitive_subterms": work.primitive_subterms,
        "primitive_predicates": work.primitive_predicates,
        "subterm_representatives": work.subterm_representatives,
        "predicate_representatives": work.predicate_representatives,
        "probe_evaluations": work.probe_evaluations,
        "auxiliary_scoring_steps": work.auxiliary_scoring_steps,
        "verifier_calls": verifier_calls,
        "verifier_time_ms": verifier_time_ms,
        "wall_clock_ms": (time.perf_counter() - started) * 1000,
        "process_peak_rss_kb": get_peak_rss_kb(),
    }


def run_decision_experiments() -> dict:
    genome = load_genome(ROOT / "examples" / "seed-genome.v0.1.yaml")
    base = genome["genome"]["base"]
    cases_2d = tuple(product(range(-3, 4), repeat=2))

    min2 = load_world(ROOT / "examples" / "world-min2.v0.1.yaml")
    absdiff = load_world(ROOT / "examples" / "world-absdiff.v0.2.yaml")
    clamp = load_world(ROOT / "examples" / "world-clamp3.v0.3.yaml")

    base_diff = dict(base)
    base_diff["max_ast_depth"] = 8
    base_diff["max_ast_nodes"] = 32

    base_clamp = dict(base)
    base_clamp["cin_ir_version"] = "0.2"
    base_clamp["input_types"] = ["Int"] * 3
    base_clamp["max_ast_depth"] = 8
    base_clamp["max_ast_nodes"] = 32

    raw_cases = tuple(product(range(-2, 3), repeat=3))
    clamp_cases = tuple(pt for pt in raw_cases if pt[1] <= pt[2])

    results = [
        _measure_task(min2, base, cases_2d),
        _measure_task(absdiff, base_diff, cases_2d),
        _measure_task(clamp, base_clamp, clamp_cases),
    ]
    return {
        "protocol": "cin.synthesis.decision/v0.2",
        "measurement_scope": "Single process, observed generation and finite-world verification",
        "limitations": [
            "RSS is a process peak, not independent per-task memory",
            "Scoring-step counts exclude Python runtime and macro-discovery cost",
            "No matched naive-search comparison is included",
        ],
        "results": results,
    }


if __name__ == "__main__":
    report = run_decision_experiments()
    print(json.dumps(report, indent=2))
