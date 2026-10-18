"""Reproduce the M1 finite-domain results; no target code enters search.

This development harness screens proposals against public training examples and
then requests an independent, exhaustive formal-world verdict for survivors.
Screening is not a proof, and this script is not an organism lifecycle run.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from cin.contracts import load_genome, load_world
from cin.ir import canonical_hash, run_ir
from cin.search import SearchStats, candidate_stream
from cin.worlds import check_formula, verify_program

ROOT = Path(__file__).resolve().parents[1]
SCREEN = ((-4, -1), (1, -4), (0, 0), (-2, 3), (3, -2), (4, 4))
TASKS = (
    ("world-min2.v0.1.yaml", 250),
    ("world-absdiff.v0.2.yaml", 30000),
)


def run_task(filename: str, budget: int, base: dict) -> dict:
    world = load_world(ROOT / "examples" / filename)
    screened = 0
    screen_operations = [0]
    formal_checks = 0
    formal_operations = 0
    stats = SearchStats()
    count = 0
    start = time.process_time()
    for count, proposal in enumerate(
        candidate_stream(
            base["starting_expression"], base, seed=0, max_proposals=budget, stats=stats
        ),
        1,
    ):
        for x, y in SCREEN:
            screened += 1
            output = run_ir(proposal.expression, x, y, ops_counter=screen_operations)
            if not check_formula(world["postcondition"], {"x": x, "y": y, "result": output}):
                break
        else:
            verdict = verify_program(proposal.expression, world, base, max_cases=81)
            formal_checks += 1
            formal_operations += verdict.operations
            if verdict.status == "PASS":
                return {
                    "task_id": world["id"],
                    "status": "PASS",
                    "proof_scope": "FINITE_EXHAUSTIVE",
                    "domain_cases_checked": verdict.checked,
                    "candidate_proposals_seen": count,
                    "proposal_budget": budget,
                    "candidate_hash": canonical_hash(proposal.expression),
                    "screen_cases_executed": screened,
                    "screen_interpreter_operations": screen_operations[0],
                    "formal_verification_calls": formal_checks,
                    "formal_interpreter_operations": formal_operations,
                    "cpu_seconds": round(time.process_time() - start, 3),
                    "world_admission": "not_run",
                    "internal_shape_attempts": stats.attempted_shapes,
        "observational_prunes": stats.observational_prunes,
        "integer_representatives": stats.integer_representatives,
        "boolean_representatives": stats.boolean_representatives,
                }
    return {
        "task_id": world["id"],
        "status": "UNKNOWN",
        "proof_scope": "UNKNOWN",
        "candidate_proposals_seen": count,
        "proposal_budget": budget,
        "screen_cases_executed": screened,
        "screen_interpreter_operations": screen_operations[0],
        "formal_verification_calls": formal_checks,
        "formal_interpreter_operations": formal_operations,
        "cpu_seconds": round(time.process_time() - start, 3),
        "world_admission": "not_run",
        "internal_shape_attempts": stats.attempted_shapes,
                    "observational_prunes": stats.observational_prunes,
                    "integer_representatives": stats.integer_representatives,
                    "boolean_representatives": stats.boolean_representatives,
    }


if __name__ == "__main__":
    base = load_genome(ROOT / "examples" / "seed-genome.v0.1.yaml")["genome"]["base"]
    results = [run_task(filename, budget, base) for filename, budget in TASKS]
    print(json.dumps({"protocol": "cin.m1/development-pilot", "results": results}, indent=2))
    raise SystemExit(0 if all(result["status"] == "PASS" for result in results) else 1)
