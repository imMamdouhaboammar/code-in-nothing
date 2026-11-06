"""Explore threshold-free self-discovered CIN subprogram transfer.

Exploratory only: the corpus is small and related by construction, and the
reported work-unit threshold is not a hard interpreter/solver instruction cap.
"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import platform
import random
import resource
import subprocess
import sys
import time
from dataclasses import asdict
from pathlib import Path

from cin.ir import canonical_hash
from cin.synthesis.cegis import CEGISResult, run_cegis_loop
from cin.synthesis.decision import SynthesisWork
from cin.synthesis.library import Macro, MacroRegistry, normalize_args
from cin.synthesis.open_discovery import (
    OPEN_PILOT_HOLDOUT,
    OPEN_PILOT_TRAIN,
    discover_open_macros,
    validate_open_manifest,
)
from cin.synthesis.sygus import SyGuSTask, get_sygus_task
from cin.synthesis.z3_verifier import HAS_Z3

WORK_THRESHOLD = 200_000
CEGIS_ROUNDS = 6
SOFT_ROUND_TIMEOUT = 2.0
HARD_TASK_TIMEOUT = 7.0


def make_base_config(arity: int) -> dict:
    """Keep the exact same grammar and IR constraints in both comparison arms."""
    return {
        "cin_ir_version": "0.1" if arity == 2 else "0.2",
        "organism_class": "open_discovery_pilot",
        "input_types": ["Int"] * arity,
        "return_type": "Int",
        "starting_expression": {"op": "Arg", "index": 0},
        "allowed_primitives": ["Arg", "ConstInt", "Add", "Sub", "LessThan", "Equal", "If"],
        "allowed_constants": [0, 1],
        "max_ast_depth": 7,
        "max_ast_nodes": 25,
        "invariants": ["typed", "pure", "deterministic", "resource_bounded"],
    }


def counted_work(work: SynthesisWork, result: CEGISResult) -> int:
    """A transparent additive work index, not an estimate of CPU instructions."""
    return (
        work.primitive_subterms
        + work.primitive_predicates
        + work.probe_evaluations
        + work.auxiliary_scoring_steps
        + result.total_shapes_attempted
        + result.verifier_invocations
    )


def build_distractors() -> MacroRegistry:
    """Twenty distinct, typed affine functions, unrelated by intended use."""
    base_terms = [
        {"op": "Arg", "index": 0},
        {"op": "Arg", "index": 1},
        {"op": "Sub", "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 1}]},
        {"op": "Sub", "args": [{"op": "Arg", "index": 1}, {"op": "Arg", "index": 0}]},
    ]
    registry = MacroRegistry()
    for idx in range(20):
        body = base_terms[idx // 5]
        for _ in range(idx % 5 + 1):
            body = {"op": "Add", "args": [body, {"op": "ConstInt", "value": 1}]}
        normalized, arity = normalize_args(body)
        fingerprint = canonical_hash(normalized)
        registry.register(
            Macro(
                name=f"distractor_{idx:02d}",
                arity=arity,
                body=normalized,
                origin_hash=fingerprint,
                metadata={"provenance": "synthetic_stress_distractor"},
            )
        )
    return registry


def split_macro_ablation(library: dict) -> tuple[dict, dict]:
    """Isolate full-program transfer from proper-subtree reuse."""
    whole = {
        name: macro
        for name, macro in library.items()
        if macro["metadata"]["complete_training_program"]
    }
    proper = {
        name: macro
        for name, macro in library.items()
        if not macro["metadata"]["complete_training_program"]
    }
    return whole, proper


def make_sum_task(arity: int) -> SyGuSTask:
    """Additional arithmetic high-arity stress without pretending it is heldout."""
    if arity not in (5, 8):
        raise ValueError("This frozen stress fixture contains only sum5 and sum8")
    import z3

    return SyGuSTask(
        name=f"sum{arity}",
        category="LIA",
        arity=arity,
        variable_names=[f"x{i}" for i in range(arity)],
        z3_spec=lambda xs, result: result == z3.Sum(xs),
        reference_oracle=lambda *xs: sum(xs),
        initial_seed_cases=(
            tuple(range(arity)),
            tuple(range(arity, 0, -1)),
            tuple([0] * arity),
        ),
    )


def _resource_mib() -> float:
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # macOS exposes bytes, Linux reports KiB.
    return round(peak / (1024 * 1024 if sys.platform == "darwin" else 1024), 2)


def _record(task_name: str, macro_data: dict) -> dict:
    task = (
        make_sum_task(int(task_name[3:]))
        if task_name in ("sum5", "sum8")
        else get_sygus_task(task_name)
    )
    work = SynthesisWork()
    registry = MacroRegistry.from_dict(macro_data) if macro_data else None
    result = run_cegis_loop(
        task,
        make_base_config(task.arity),
        macro_registry=registry,
        max_rounds=CEGIS_ROUNDS,
        timeout_sec=SOFT_ROUND_TIMEOUT,
        work=work,
    )
    return {
        "task": task_name,
        "status": result.status,
        "proof": result.z3_verdict.status if result.z3_verdict else None,
        "proof_scope": result.z3_verdict.proof_scope if result.z3_verdict else None,
        "iterations": result.iterations,
        "shapes": result.total_shapes_attempted,
        "candidate_evaluations": result.total_evaluations,
        "work": asdict(work),
        "verifier_invocations": result.verifier_invocations,
        "verifier_ms": round(result.verifier_elapsed_ms, 2),
        "elapsed_ms": round(result.elapsed_ms, 2),
        "peak_rss_mib": _resource_mib(),
        "work_units": counted_work(work, result),
        "expression_hash": canonical_hash(result.expression) if result.expression else None,
        "macro_count": len(macro_data),
    }


def _worker(queue: mp.Queue, task_name: str, macro_data: dict) -> None:
    try:
        queue.put({"record": _record(task_name, macro_data)})
    except Exception as exc:
        queue.put({"error": f"{type(exc).__name__}: {exc}"})


def run_bounded(task_name: str, macro_data: dict, hard_timeout: float) -> dict:
    """Isolate each attempt so a soft CEGIS limit cannot freeze the machine."""
    context = mp.get_context("spawn")
    queue = context.Queue()
    process = context.Process(target=_worker, args=(queue, task_name, macro_data))
    started = time.perf_counter()
    process.start()
    process.join(timeout=hard_timeout)
    elapsed = round((time.perf_counter() - started) * 1000, 2)
    if process.is_alive():
        process.terminate()
        process.join(timeout=2)
        if process.is_alive():
            process.kill()
            process.join()
        output = {
            "task": task_name,
            "status": "TIMEOUT",
            "proof": None,
            "elapsed_ms": elapsed,
            "work_units": None,
            "work": None,
            "verifier_invocations": None,
            "verifier_ms": None,
            "peak_rss_mib": None,
            "macro_count": len(macro_data),
            "note": "Worker terminated; partial counters unavailable",
        }
    else:
        try:
            message = queue.get(timeout=1)
        except (OSError, EOFError, ValueError):
            message = {"error": "Worker did not send results"}
        except Exception:
            message = {"error": "Worker result queue empty"}
        if "record" in message:
            output = message["record"]
            output["process_wall_ms"] = elapsed
        else:
            output = {
                "task": task_name,
                "status": "WORKER_FAILED",
                "proof": None,
                "elapsed_ms": elapsed,
                "work_units": None,
                "work": None,
                "verifier_invocations": None,
                "verifier_ms": None,
                "peak_rss_mib": None,
                "macro_count": len(macro_data),
                "note": message["error"],
            }
    queue.close()
    queue.join_thread()
    work = output.get("work_units")
    output["eligible_under_work_threshold"] = (
        output["status"] == "PROVED" and work is not None and work <= WORK_THRESHOLD
    )
    if output["status"] == "PROVED" and work is not None and work > WORK_THRESHOLD:
        output["budget_outcome"] = "OVER_THRESHOLD"
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1])
    parser.add_argument("--hard-timeout", type=float, default=HARD_TASK_TIMEOUT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if not HAS_Z3:
        raise RuntimeError("The exploratory benchmark requires z3-solver")
    if args.hard_timeout <= 0:
        parser.error("--hard-timeout must be positive")

    validate_open_manifest(OPEN_PILOT_TRAIN, OPEN_PILOT_HOLDOUT)
    freeze = {
        "train": OPEN_PILOT_TRAIN,
        "heldout": OPEN_PILOT_HOLDOUT,
        "seeds": args.seeds,
        "max_rounds": CEGIS_ROUNDS,
        "soft_round_timeout_sec": SOFT_ROUND_TIMEOUT,
        "hard_timeout_sec": args.hard_timeout,
        "work_threshold": WORK_THRESHOLD,
        "grammar": make_base_config(2)["allowed_primitives"],
    }
    print("OPEN DISCOVERY PILOT", canonical_hash(freeze), flush=True)

    training = []
    for name in OPEN_PILOT_TRAIN:
        # The formal result is used to admit syntax, never the task name as a hint.
        task = get_sygus_task(name)
        work = SynthesisWork()
        result = run_cegis_loop(
            task,
            make_base_config(task.arity),
            max_rounds=CEGIS_ROUNDS,
            timeout_sec=SOFT_ROUND_TIMEOUT,
            work=work,
        )
        # Keep the audited outcome from the same run whose expression was mined.
        record = {
            "task": name,
            "status": result.status,
            "proof": result.z3_verdict.status if result.z3_verdict else None,
            "proof_scope": result.z3_verdict.proof_scope if result.z3_verdict else None,
            "iterations": result.iterations,
            "shapes": result.total_shapes_attempted,
            "candidate_evaluations": result.total_evaluations,
            "work": asdict(work),
            "verifier_invocations": result.verifier_invocations,
            "verifier_ms": round(result.verifier_elapsed_ms, 2),
            "elapsed_ms": round(result.elapsed_ms, 2),
            "peak_rss_mib": _resource_mib(),
            "work_units": counted_work(work, result),
            "expression_hash": canonical_hash(result.expression) if result.expression else None,
        }
        training.append((name, result, record))
        print(f"train {name}: {result.status} | work {record['work_units']}", flush=True)

    started = time.perf_counter()
    frozen_registry, mining_work = discover_open_macros(
        [(name, result) for name, result, _ in training]
    )
    mining_elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    # Freeze the exact library here; task objects in the holdout are loaded in workers.
    frozen = frozen_registry.to_dict()
    print(f"discovered {len(frozen)} typed subprograms in {mining_elapsed_ms} ms", flush=True)

    heldout = []
    for seed in args.seeds:
        task_order = list(OPEN_PILOT_HOLDOUT)
        random.Random(seed).shuffle(task_order)
        for index, task_name in enumerate(task_order):
            arms = [("no_inheritance", {}), ("open_inheritance", frozen)]
            if (seed + index) % 2:
                arms.reverse()
            for arm, library in arms:
                record = run_bounded(task_name, library, args.hard_timeout)
                record.update(seed=seed, arm=arm, category="heldout")
                heldout.append(record)
                print(
                    f"seed={seed} {task_name} {arm}: {record['status']} "
                    f"| work={record['work_units']} | {record['elapsed_ms']}ms",
                    flush=True,
                )

    stress = []
    distractions = build_distractors().to_dict()
    for task_name in ("clamp3", "sum5", "sum8"):
        for arm, library in (
            ("no_inheritance", {}),
            ("20_distractors", distractions),
        ):
            record = run_bounded(task_name, library, args.hard_timeout)
            record.update(seed=0, arm=arm, category="stress")
            stress.append(record)
            print(
                f"stress {task_name} {arm}: {record['status']} "
                f"| work={record['work_units']} | {record['elapsed_ms']}ms",
                flush=True,
            )

    # Post-hoc diagnostic: added after the initial exploratory run identified
    # gains on max3/min3. This is never represented as a pre-registered endpoint.
    ablation = []
    whole, proper = split_macro_ablation(frozen)
    for task_name in ("max3", "min3"):
        for arm, library in (
            ("whole_program_only", whole),
            ("proper_subtrees_only", proper),
        ):
            record = run_bounded(task_name, library, args.hard_timeout)
            record.update(seed=0, arm=arm, category="posthoc_ablation")
            ablation.append(record)
            print(
                f"ablation {task_name} {arm}: {record['status']} "
                f"| work={record['work_units']} | {record['elapsed_ms']}ms",
                flush=True,
            )

    report = {
        "stage": "exploratory_not_confirmatory",
        "freeze": freeze,
        "freeze_sha256": canonical_hash(freeze),
        "host": {
            "platform": platform.platform(),
            "python": sys.version,
            "pid": os.getpid(),
            "git_revision": subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip(),
        },
        "training": [record for _, _, record in training],
        "mining": {
            "elapsed_ms": mining_elapsed_ms,
            "peak_rss_mib_cumulative": _resource_mib(),
            "counters": mining_work,
            "library_hash": canonical_hash(frozen),
            "macro_inventory": frozen,
            "note": "Only inherited expressions are mined; no task-name guidance",
        },
        "heldout": heldout,
        "stress": stress,
        "posthoc_ablation": ablation,
        "interpretation_notes": [
            "Small, related exploratory task sample; no causal or generalization claim",
            "Common work index threshold is post-execution, not a hard resource governor",
            "Wall-time limit is hard per worker; interrupted work counters are unavailable",
            "The five observed work categories are reported separately from Z3 solver latency",
            "Whole proved programs and all typed subtrees are eligible regardless of utility",
            "The base CIN generator currently consumes unary/binary macros only",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise FileExistsError(f"Will not overwrite experimental evidence: {args.output}")
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("saved", args.output, flush=True)


if __name__ == "__main__":
    main()
