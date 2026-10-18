"""Reproduce the opt-in CIN B0/B1/B2 public-feedback experiment.

The complete verifier domain is independent of the frozen public training
panel. This is NOT a world-admission, inheritance or generalization benchmark.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cin.contracts import load_genome, load_world
from cin.guided_experiment import ARMS, run_trial
from cin.training import PublicTrainingPanel

ROOT = Path(__file__).resolve().parents[1]
TASKS = {
    "MAX2": "world-max2.v0.1.yaml",
    "MIN2": "world-min2.v0.1.yaml",
    "ABSDIFF": "world-absdiff.v0.2.yaml",
}
PUBLIC_CASES = ((-4, -1), (1, -4), (0, 0), (-2, 3), (3, -2))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    parser.add_argument("--proposals", type=int, default=250)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.seeds or any(seed < 0 for seed in args.seeds):
        parser.error("seeds must be nonnegative")
    if len(set(args.seeds)) != len(args.seeds):
        parser.error("seeds must be unique")
    if not 1 <= args.proposals <= 30000:
        parser.error("proposals must be 1..30000")
    if args.output.exists():
        parser.error("output already exists; refusal to overwrite experiment evidence")

    base = load_genome(ROOT / "examples" / "seed-genome.v0.1.yaml")["genome"]["base"]
    results = []
    for name, filename in TASKS.items():
        world = load_world(ROOT / "examples" / filename)
        panel = PublicTrainingPanel(world, PUBLIC_CASES)
        for seed in args.seeds:
            for arm in ARMS:
                result = run_trial(
                    arm, world, base, panel, seed=seed, max_proposals=args.proposals
                )
                result["task"] = name
                results.append(result)

    by_arm = {}
    for arm in ARMS:
        group = [result for result in results if result["arm"] == arm]
        successful = [result for result in group if result["status"] == "PASS"]
        by_arm[arm] = {
            "trials": len(group),
            "verified_successes": len(successful),
            "success_rate": len(successful) / len(group),
            "accounted_events_to_pass": [
                result["accounted_events"] for result in successful
            ],
            "unknowns": sum(result["status"] == "UNKNOWN" for result in group),
        }

    record = {
        "protocol": "cin.guided-ablation-suite/v0.1",
        "preregistered_arms": list(ARMS),
        "task_order": list(TASKS),
        "seeds": args.seeds,
        "proposal_limit": args.proposals,
        "public_cases": PUBLIC_CASES,
        "training_verifier_separation": "public_cases_vs_independent_declared_domain",
        "matched_budget_definition": "identical per-dimension governor limits and proposal caps",
        "accounted_events_caveat": "unit-weight proxy; not calibrated CPU costs",
        "formal_world_admission": "not_run",
        "summary_by_arm": by_arm,
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as f:
        json.dump(record, f, indent=2, sort_keys=True)
        f.write("\n")
    print(json.dumps({"output": str(args.output), "summary_by_arm": by_arm}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
