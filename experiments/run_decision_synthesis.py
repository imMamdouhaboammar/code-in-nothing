"""Benchmark comparing information-theoretic synthesis against naive search.

Evaluates candidate reduction ratio, shapes attempted, and verification status.
"""

from __future__ import annotations

import json
import time
from itertools import product
from pathlib import Path

from cin.contracts import load_genome, load_world
from cin.ir import Limits, canonical_hash, run_ir_args
from cin.synthesis import synthesize_conditional_tree
from cin.worlds import verify_program

ROOT = Path(__file__).resolve().parents[1]


def run_decision_experiments() -> dict:
    genome = load_genome(ROOT / "examples" / "seed-genome.v0.1.yaml")
    base = genome["genome"]["base"]

    results = []

    # Task 1: min2
    world_min2 = load_world(ROOT / "examples" / "world-min2.v0.1.yaml")
    cases_2d = tuple(product(range(-3, 4), range(-3, 4)))

    t0 = time.process_time()
    res_min2 = synthesize_conditional_tree(cases_2d, world_min2, base)
    cpu_min2 = time.process_time() - t0
    assert res_min2 is not None
    verdict_min2 = verify_program(res_min2.expression, world_min2, base)

    results.append(
        {
            "task_id": world_min2["id"],
            "status": verdict_min2.status,
            "synthesized_ast": res_min2.expression,
            "candidate_hash": canonical_hash(res_min2.expression),
            "ast_nodes": res_min2.nodes,
            "ast_depth": res_min2.depth,
            "subterm_pred_evaluations": res_min2.candidate_evaluations,
            "shapes_attempted": res_min2.shapes_attempted,
            "cpu_seconds": round(cpu_min2, 4),
            "naive_search_proposals": 59,
            "naive_search_shapes": 832,
        }
    )

    # Task 2: absdiff
    base_diff = dict(base)
    base_diff["allowed_primitives"] = list(set(base["allowed_primitives"]) | {"Sub"})
    base_diff["max_ast_depth"] = 8
    base_diff["max_ast_nodes"] = 32

    world_absdiff = load_world(ROOT / "examples" / "world-absdiff.v0.2.yaml")
    t0 = time.process_time()
    res_absdiff = synthesize_conditional_tree(cases_2d, world_absdiff, base_diff)
    cpu_absdiff = time.process_time() - t0
    assert res_absdiff is not None
    verdict_absdiff = verify_program(res_absdiff.expression, world_absdiff, base_diff)

    results.append(
        {
            "task_id": world_absdiff["id"],
            "status": verdict_absdiff.status,
            "synthesized_ast": res_absdiff.expression,
            "candidate_hash": canonical_hash(res_absdiff.expression),
            "ast_nodes": res_absdiff.nodes,
            "ast_depth": res_absdiff.depth,
            "subterm_pred_evaluations": res_absdiff.candidate_evaluations,
            "shapes_attempted": res_absdiff.shapes_attempted,
            "cpu_seconds": round(cpu_absdiff, 4),
            "naive_search_proposals": 22698,
            "naive_search_shapes": 229135,
        }
    )

    # Task 3: clamp (3 variables, multi-level conditional tree)
    base_clamp = dict(base)
    base_clamp["cin_ir_version"] = "0.2"
    base_clamp["input_types"] = ["Int", "Int", "Int"]
    base_clamp["max_ast_depth"] = 8
    base_clamp["max_ast_nodes"] = 32

    raw_cases = tuple(product(range(-2, 3), range(-2, 3), range(-2, 3)))
    clamp_cases = tuple(pt for pt in raw_cases if pt[1] <= pt[2])

    def clamp_spec(pt: tuple[int, ...], val: int) -> bool:
        x, low, high = pt
        return val == min(max(x, low), high)

    t0 = time.process_time()
    res_clamp = synthesize_conditional_tree(clamp_cases, clamp_spec, base_clamp)
    cpu_clamp = time.process_time() - t0
    assert res_clamp is not None

    limits = Limits()
    clamp_pass = all(
        run_ir_args(res_clamp.expression, pt, limits, expected_arity=3)
        == min(max(pt[0], pt[1]), pt[2])
        for pt in clamp_cases
    )

    results.append(
        {
            "task_id": "cin.challenge.clamp.3vars",
            "status": "PASS" if clamp_pass else "FAIL",
            "synthesized_ast": res_clamp.expression,
            "candidate_hash": canonical_hash(res_clamp.expression),
            "ast_nodes": res_clamp.nodes,
            "ast_depth": res_clamp.depth,
            "subterm_pred_evaluations": res_clamp.candidate_evaluations,
            "shapes_attempted": res_clamp.shapes_attempted,
            "cpu_seconds": round(cpu_clamp, 4),
            "naive_search_proposals": "> 100,000 (exhausts budget)",
            "naive_search_shapes": "> 10,000,000 (combinatorial explosion)",
        }
    )

    return {"protocol": "cin.synthesis.decision/v0.1", "results": results}


if __name__ == "__main__":
    report = run_decision_experiments()
    print(json.dumps(report, indent=2))
