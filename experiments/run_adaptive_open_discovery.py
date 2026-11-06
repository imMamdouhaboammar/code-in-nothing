"""Supervised progressive exploration with frozen profiles and formal checks.

This is an exploratory, not confirmatory, benchmark. No production search
behavior is changed by importing or running this module.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing as mp
import os
import platform
import random
import resource
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

from cin.ir import canonical_hash
from cin.synthesis.cegis import run_cegis_loop
from cin.synthesis.decision import SynthesisSearchConfig, SynthesisWork
from cin.synthesis.library import MacroRegistry
from cin.synthesis.open_discovery import (
    OPEN_PILOT_HOLDOUT,
    OPEN_PILOT_TRAIN,
    discover_open_macros,
    validate_open_manifest,
)
from cin.synthesis.sygus import get_sygus_task
from cin.synthesis.z3_verifier import HAS_Z3
from experiments.run_open_discovery_pilot import (
    build_distractors,
    counted_work,
    make_base_config,
    make_sum_task,
    split_macro_ablation,
)


@dataclass(frozen=True)
class AdaptiveStage:
    name: str
    ast_depth: int
    ast_nodes: int
    constants: tuple[int, ...]
    search: SynthesisSearchConfig
    wall_seconds: float

    def base_for(self, arity: int) -> dict:
        base = make_base_config(arity)
        base["max_ast_depth"] = self.ast_depth
        base["max_ast_nodes"] = self.ast_nodes
        base["allowed_constants"] = list(self.constants)
        return base


ADAPTIVE_STAGES = (
    AdaptiveStage(
        "P0",
        ast_depth=7,
        ast_nodes=25,
        constants=(0, 1),
        search=SynthesisSearchConfig(),
        wall_seconds=3.0,
    ),
    AdaptiveStage(
        "P1",
        ast_depth=9,
        ast_nodes=49,
        constants=(-1, 0, 1),
        search=SynthesisSearchConfig(
            subterm_depth=4,
            predicate_term_depth=3,
            max_macro_arity=4,
            macro_combination_limit=2000,
            branch_attempt_limit=2048,
            include_nullary_macros=True,
        ),
        wall_seconds=3.0,
    ),
    AdaptiveStage(
        "P2",
        ast_depth=12,
        ast_nodes=96,
        constants=(-2, -1, 0, 1, 2),
        search=SynthesisSearchConfig(
            subterm_depth=5,
            predicate_term_depth=4,
            max_macro_arity=8,
            macro_combination_limit=None,
            branch_attempt_limit=None,
            include_nullary_macros=True,
        ),
        wall_seconds=4.0,
    ),
)


def choose_adaptive_stages(stages: tuple[AdaptiveStage, ...]) -> tuple[AdaptiveStage, ...]:
    """Validate strictly increasing exploration opportunities."""
    if not stages:
        raise ValueError("At least one discovery stage is required")
    if any(stage.wall_seconds <= 0 for stage in stages):
        raise ValueError("Stage wall time must be positive")
    if any(stage.ast_depth < 1 or stage.ast_nodes < 1 for stage in stages):
        raise ValueError("AST ceilings must be positive")
    for previous, current in zip(stages, stages[1:]):
        if (
            previous.ast_depth >= current.ast_depth
            or previous.ast_nodes >= current.ast_nodes
            or previous.search.subterm_depth >= current.search.subterm_depth
            or previous.search.max_macro_arity >= current.search.max_macro_arity
        ):
            raise ValueError("Stages must expand depth, nodes and macro arity")
    return stages


def run_progressive_attempts(
    stages: tuple[AdaptiveStage, ...], solve: Callable[[AdaptiveStage], dict]
) -> list[dict]:
    """Continue after exhausted/timeout stages and stop on proof or hard failure."""
    attempts = []
    for stage in choose_adaptive_stages(stages):
        result = dict(solve(stage))
        result["stage"] = stage.name
        attempts.append(result)
        if result["status"] in ("PROVED", "MEMOUT", "WORKER_FAILED", "UNSUPPORTED"):
            break
    return attempts


def _memory_usage_mib() -> float:
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return round(raw / (1024 * 1024 if sys.platform == "darwin" else 1024), 2)


def _task_by_name(task_name: str):
    if task_name in ("sum5", "sum8"):
        return make_sum_task(int(task_name[3:]))
    return get_sygus_task(task_name)


def _stage_worker(
    result_queue: mp.Queue,
    task_name: str,
    macro_data: dict,
    stage: AdaptiveStage,
) -> None:
    try:
        task = _task_by_name(task_name)
        registry = MacroRegistry.from_dict(macro_data) if macro_data else None
        work = SynthesisWork()
        started_cpu = time.process_time()
        started_wall = time.perf_counter()
        result = run_cegis_loop(
            task,
            stage.base_for(task.arity),
            macro_registry=registry,
            max_rounds=6,
            timeout_sec=2.0,
            work=work,
            search_config=None if stage.name == "P0" else stage.search,
        )
        result_queue.put(
            {
                "record": {
                    "task": task_name,
                    "status": result.status,
                    "proof": result.z3_verdict.status if result.z3_verdict else None,
                    "proof_scope": (result.z3_verdict.proof_scope if result.z3_verdict else None),
                    "work": asdict(work),
                    "shapes_attempted": result.total_shapes_attempted,
                    "candidate_evaluations": result.total_evaluations,
                    "verifier_invocations": result.verifier_invocations,
                    "verifier_ms": round(result.verifier_elapsed_ms, 2),
                    "iterations": result.iterations,
                    "cpu_ms": round((time.process_time() - started_cpu) * 1000, 2),
                    "solver_wall_ms": round((time.perf_counter() - started_wall) * 1000, 2),
                    "peak_rss_mib": _memory_usage_mib(),
                    "work_units": counted_work(work, result) + work.macro_combinations_tried,
                    "expression_hash": (
                        canonical_hash(result.expression) if result.expression else None
                    ),
                    "macros_available": len(macro_data),
                }
            }
        )
    except Exception as exc:
        result_queue.put({"error": f"{type(exc).__name__}: {exc}"})


def run_supervised_stage(
    task_name: str,
    macro_data: dict,
    stage: AdaptiveStage,
    *,
    rss_limit_mib: float = 400.0,
) -> dict:
    """Enforce a per-process wall and observed memory ceiling from the parent."""
    if rss_limit_mib <= 0:
        raise ValueError("Memory ceiling must be positive")
    try:
        import psutil
    except ImportError as exc:
        raise RuntimeError("The adaptive benchmark requires dev dependency psutil") from exc

    ctx = mp.get_context("spawn")
    result_queue = ctx.Queue()
    process = ctx.Process(
        target=_stage_worker,
        args=(result_queue, task_name, macro_data, stage),
    )
    started = time.perf_counter()
    process.start()
    sampled_peak = 0.0
    interrupted = None

    try:
        monitor = psutil.Process(process.pid)
        while process.is_alive():
            elapsed = time.perf_counter() - started
            if elapsed >= stage.wall_seconds:
                interrupted = "TIMEOUT"
                break
            try:
                sampled_peak = max(sampled_peak, monitor.memory_info().rss / (1024 * 1024))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            if sampled_peak > rss_limit_mib:
                interrupted = "MEMOUT"
                break
            process.join(timeout=min(0.05, max(0, stage.wall_seconds - elapsed)))

        if interrupted is not None:
            process.terminate()
            process.join(timeout=0.5)
            if process.is_alive():
                process.kill()
                process.join()
            record = {
                "status": interrupted,
                "task": task_name,
                "proof": None,
                "work": None,
                "work_units": None,
                "shapes_attempted": None,
                "candidate_evaluations": None,
                "verifier_invocations": None,
                "verifier_ms": None,
                "cpu_ms": None,
                "solver_wall_ms": None,
                "macros_available": len(macro_data),
                "note": "Supervised worker interrupted; partial work counters unavailable",
            }
        else:
            try:
                message = result_queue.get(timeout=1)
            except Exception:
                message = {"error": f"No result from worker (exit code {process.exitcode})"}
            record = message.get("record") or {
                "status": "WORKER_FAILED",
                "task": task_name,
                "proof": None,
                "work": None,
                "work_units": None,
                "note": message.get("error", "Unknown subprocess failure"),
            }
    finally:
        if process.is_alive():
            process.terminate()
            process.join(timeout=0.5)
            if process.is_alive():
                process.kill()
                process.join()
        result_queue.close()
        result_queue.join_thread()

    record["process_wall_ms"] = round((time.perf_counter() - started) * 1000, 2)
    record["peak_rss_mib"] = round(max(sampled_peak, record.get("peak_rss_mib") or 0.0), 2)
    record["rss_limit_mib"] = rss_limit_mib
    record["stage_profile_hash"] = canonical_hash(asdict(stage))
    return record


def _source_digest() -> str:
    root = Path(__file__).resolve().parents[1]
    sha = hashlib.sha256()
    for name in (
        "cin/synthesis/decision.py",
        "cin/synthesis/cegis.py",
        "cin/synthesis/open_discovery.py",
        "experiments/run_open_discovery_pilot.py",
        "experiments/run_adaptive_open_discovery.py",
    ):
        sha.update(name.encode())
        sha.update((root / name).read_bytes())
    return sha.hexdigest()


def _training_and_library() -> tuple[list[dict], dict, dict]:
    training = []
    sources = []
    for task_name in OPEN_PILOT_TRAIN:
        task = get_sygus_task(task_name)
        work = SynthesisWork()
        started = time.perf_counter()
        result = run_cegis_loop(task, make_base_config(task.arity), work=work, max_rounds=6)
        rec = {
            "task": task_name,
            "status": result.status,
            "proof": result.z3_verdict.status if result.z3_verdict else None,
            "work": asdict(work),
            "shapes_attempted": result.total_shapes_attempted,
            "candidate_evaluations": result.total_evaluations,
            "verifier_invocations": result.verifier_invocations,
            "verifier_ms": result.verifier_elapsed_ms,
            "work_units": counted_work(work, result),
            "wall_ms": round((time.perf_counter() - started) * 1000, 2),
        }
        training.append(rec)
        sources.append((task_name, result))
        print(f"train {task_name} {result.status} work={rec['work_units']}", flush=True)

    started = time.perf_counter()
    registry, mining_counters = discover_open_macros(sources)
    mining_ms = round((time.perf_counter() - started) * 1000, 3)
    library = registry.to_dict()
    discovery = {
        "elapsed_ms": mining_ms,
        "work": mining_counters,
        "cost_lower_bound_units": (
            mining_counters["subtrees_visited"]
            + mining_counters["type_rejected"]
            + mining_counters["duplicate_subtrees"]
        ),
        "library_hash": canonical_hash(library),
        "macros": library,
    }
    print(f"frozen {len(library)} macros mining={mining_ms}ms", flush=True)
    return training, library, discovery


def _run_paired(
    tasks: tuple[str, ...],
    arms: list[tuple[str, dict]],
    stages: tuple[AdaptiveStage, ...],
    seeds: tuple[int, ...],
    rss_limit: float,
    category: str,
) -> list[dict]:
    results = []
    for seed in seeds:
        task_names = list(tasks)
        random.Random(seed).shuffle(task_names)
        for idx, task_name in enumerate(task_names):
            ordered = list(arms)
            if (seed + idx) % 2:
                ordered.reverse()
            for arm, library in ordered:
                attempts = run_progressive_attempts(
                    stages,
                    lambda stage, _t=task_name, _library=library: run_supervised_stage(
                        _t, _library, stage, rss_limit_mib=rss_limit
                    ),
                )
                work = [x.get("work_units") for x in attempts]
                record = {
                    "task": task_name,
                    "seed": seed,
                    "category": category,
                    "arm": arm,
                    "status": attempts[-1]["status"],
                    "proved": any(
                        x["status"] == "PROVED" and x.get("proof") == "SYMBOLIC_PROVED"
                        for x in attempts
                    ),
                    "total_completed_work_units": sum(v for v in work if v is not None),
                    "partial_work_unavailable": any(v is None for v in work),
                    "total_process_wall_ms": round(sum(x["process_wall_ms"] for x in attempts), 2),
                    "peak_rss_mib": max(x.get("peak_rss_mib", 0) for x in attempts),
                    "attempts": attempts,
                }
                results.append(record)
                print(
                    f"{category} seed={seed} {task_name} {arm}: "
                    f"{record['status']} steps={len(attempts)} "
                    f"work>={record['total_completed_work_units']} "
                    f"wall={record['total_process_wall_ms']}ms",
                    flush=True,
                )
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[2, 3])
    parser.add_argument("--rss-limit-mib", type=float, default=400)
    parser.add_argument("--skip-stress", action="store_true")
    args = parser.parse_args()

    if not HAS_Z3:
        raise RuntimeError("Formal benchmark requires z3-solver")
    stages = choose_adaptive_stages(ADAPTIVE_STAGES)
    validate_open_manifest(OPEN_PILOT_TRAIN, OPEN_PILOT_HOLDOUT)
    if args.output.exists():
        raise FileExistsError(f"Experimental evidence exists: {args.output}")
    if args.rss_limit_mib <= 0:
        parser.error("--rss-limit-mib must be positive")

    manifest = {
        "training": OPEN_PILOT_TRAIN,
        "heldout": OPEN_PILOT_HOLDOUT,
        "stress": ("clamp3", "sum5", "sum8") if not args.skip_stress else (),
        "seeds": args.seeds,
        "stages": [asdict(stage) for stage in stages],
        "rss_limit_mib": args.rss_limit_mib,
        "source_sha256": _source_digest(),
    }
    print("ADAPTIVE OPEN DISCOVERY", canonical_hash(manifest), flush=True)
    training, learned_library, discovery = _training_and_library()
    heldout = _run_paired(
        OPEN_PILOT_HOLDOUT,
        [("no_inheritance", {}), ("open_inheritance", learned_library)],
        stages,
        tuple(args.seeds),
        args.rss_limit_mib,
        "heldout",
    )
    whole, proper = split_macro_ablation(learned_library)
    ablation = _run_paired(
        ("max3", "min3"),
        [("whole_program_only", whole), ("proper_subtrees_only", proper)],
        stages,
        (args.seeds[0],),
        args.rss_limit_mib,
        "posthoc_ablation",
    )
    stress = []
    if not args.skip_stress:
        distractions = build_distractors().to_dict()
        combined = {**learned_library, **distractions}
        stress = _run_paired(
            ("clamp3", "sum5", "sum8"),
            [
                ("no_inheritance", {}),
                ("20_distractors", distractions),
                ("inheritance_plus_20_distractors", combined),
            ],
            stages,
            (args.seeds[0],),
            args.rss_limit_mib,
            "stress",
        )

    training_cost = sum(record["work_units"] for record in training)
    mining_lower_bound = discovery["cost_lower_bound_units"]
    cohort_cost = {}
    for seed in args.seeds:
        for arm in ("no_inheritance", "open_inheritance"):
            records = [r for r in heldout if r["seed"] == seed and r["arm"] == arm]
            cohort_cost[f"seed={seed}/{arm}"] = {
                "complete_work_lower_bound": (
                    training_cost
                    + (mining_lower_bound if arm == "open_inheritance" else 0)
                    + sum(r["total_completed_work_units"] for r in records)
                ),
                "has_interrupted_unknown_cost": any(r["partial_work_unavailable"] for r in records),
                "solved": sum(r["proved"] for r in records),
                "denominator": len(records),
                "total_task_process_wall_ms": round(
                    sum(r["total_process_wall_ms"] for r in records), 2
                ),
            }

    report = {
        "stage": "adaptive_exploratory_not_confirmatory",
        "manifest": manifest,
        "manifest_sha256": canonical_hash(manifest),
        "host": {
            "platform": platform.platform(),
            "python": sys.version,
            "git_revision": subprocess.run(
                ["git", "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip(),
            "source_sha256": manifest["source_sha256"],
            "pid": os.getpid(),
        },
        "training": training,
        "discovery": discovery,
        "heldout": heldout,
        "posthoc_ablation": ablation,
        "stress": stress,
        "cohort_cost": cohort_cost,
        "notes": [
            "The profiles jointly alter several search parameters; effects are not separately attributable",
            "Probe equality is not symbolic equivalence; proof requires independent Z3 check",
            "Hard-terminated worker partial counters are unavailable and excluded from known work totals",
            "The stage schedule is matched, while used work and time may differ by arm",
            "Two task-order seeds are not independent cohorts",
            "Unsolved tasks may be limited by the closed integer grammar or decision-tree shape",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print("saved", args.output, flush=True)


if __name__ == "__main__":
    main()
