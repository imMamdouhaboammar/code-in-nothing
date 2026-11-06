"""Head-to-Head Benchmark: Blind Search vs. Z3 CEGIS vs. Neuro-Symbolic Agent Kernel.

Evaluates on randomized SyGuS (Syntax-Guided Synthesis) benchmark tasks:
  - Arm 0: Pure Blind Evolutionary Search (Hiding failure counterexamples)
  - Arm 1: Symbolic CEGIS with Z3 (Counterexample-Guided Inductive Synthesis)
  - Arm 2: Neuro-Symbolic Agent Kernel (LLM Intuitive Prior + Z3 Formal Guardian + Generational Inheritance)
"""

from __future__ import annotations

import random
import time

from cin.search import SearchStats, candidate_stream
from cin.synthesis import (
    HAS_Z3,
    CEGISResult,
    GuidanceVerdict,
    NeuroSymbolicAgentKernel,
    SyGuSTask,
    get_sygus_task,
    run_cegis_loop,
)
from cin.synthesis.z3_verifier import verify_spec_with_z3

if not HAS_Z3:
    raise RuntimeError("z3-solver is required to run this benchmark")


def make_base_config(arity: int) -> dict:
    return {
        "cin_ir_version": "0.1" if arity == 2 else "0.2",
        "organism_class": "benchmark",
        "input_types": ["Int"] * arity,
        "return_type": "Int",
        "starting_expression": {"op": "Arg", "index": 0},
        "allowed_primitives": ["Arg", "ConstInt", "Add", "Sub", "LessThan", "Equal", "If"],
        "allowed_constants": [0, 1],
        "max_ast_depth": 7,
        "max_ast_nodes": 25,
        "invariants": ["typed", "pure", "deterministic", "resource_bounded"],
    }


def measure_blind_baseline(
    task: SyGuSTask, base: dict, *, max_proposals: int = 200, time_budget_sec: float = 5.0
) -> tuple[str, int, float]:
    """Measure candidates actually tested, without feeding verifier counterexamples back."""
    started = time.perf_counter()
    stats = SearchStats()
    stream = candidate_stream(
        base["starting_expression"],
        base,
        seed=0,
        max_proposals=max_proposals,
        stats=stats,
    )
    status = "EXHAUSTED"
    for proposal in stream:
        if time.perf_counter() - started >= time_budget_sec:
            status = "TIMEOUT"
            break
        verdict = verify_spec_with_z3(
            proposal.expression,
            task.z3_spec,
            arity=task.arity,
            var_names=task.variable_names,
            precondition=task.precondition,
        )
        if verdict.status == "SYMBOLIC_PROVED":
            status = "PROVED"
            break
    elapsed_ms = (time.perf_counter() - started) * 1000
    return status, stats.attempted_shapes, elapsed_ms


def main():
    print("=" * 80)
    print("SYGUS BENCHMARK: BLIND SEARCH vs. Z3 CEGIS vs. NEURO-SYMBOLIC AGENT KERNEL")
    print("=" * 80)
    print("Formal Evaluator: Z3 SMT Solver (LIA Theory)")
    print("Verification Scope: Unbounded Integers (Z^k)")
    print("=" * 80 + "\n")

    # Randomize order to demonstrate robust generalization across SyGuS
    rng = random.Random(42)
    # Ensure foundational primitives are available before composites
    ordered_tasks = ["max2", "min2"] + rng.sample(["absdiff", "clamp3", "max3", "max4"], 4)

    print(f"Scheduled SyGuS Task Order: {ordered_tasks}\n")

    # Initialize Arm 2 Neuro-Symbolic Kernel
    agent_kernel = NeuroSymbolicAgentKernel()

    results_table = []

    for task_name in ordered_tasks:
        task: SyGuSTask = get_sygus_task(task_name)
        base = make_base_config(task.arity)

        print("--------------------------------------------------------------------------------")
        print(f"TASK: {task.name.upper()} (Arity: {task.arity}, Variables: {task.variable_names})")
        print("--------------------------------------------------------------------------------")

        # ----------------------------------------------------------------------
        # ARM 0: Blind Search, measured with fixed proposal and wall-time budgets
        # ----------------------------------------------------------------------
        arm0_status, arm0_shapes, arm0_time_ms = measure_blind_baseline(task, base)

        # ----------------------------------------------------------------------
        # ARM 1: Classical CEGIS with Z3 (Counterexample Guided, No Inherited Library)
        # ----------------------------------------------------------------------
        t0 = time.perf_counter()
        arm1_res: CEGISResult = run_cegis_loop(task, base, macro_registry=None, max_rounds=10)
        arm1_time_ms = (time.perf_counter() - t0) * 1000

        # ----------------------------------------------------------------------
        # ARM 2: Neuro-Symbolic Agent Kernel (Intuitive Prior + Z3 + Inherited Macros)
        # ----------------------------------------------------------------------
        t0 = time.perf_counter()
        arm2_verdict: GuidanceVerdict = agent_kernel.solve_and_verify(
            task, base, try_intuitive_prior=True
        )
        arm2_time_ms = (time.perf_counter() - t0) * 1000

        print(
            f"  [Arm 0] Blind Search     : Status: {arm0_status:<16} | Shapes: {str(arm0_shapes):<8} | Time: {arm0_time_ms:.1f} ms"
        )
        print(
            f"  [Arm 1] Z3 CEGIS (Pure)  : Status: {arm1_res.status:<16} | Shapes: {str(arm1_res.total_shapes_attempted):<8} | Time: {arm1_time_ms:.1f} ms (Rounds: {arm1_res.iterations})"
        )
        print(
            f"  [Arm 2] Neuro-Symbolic   : Status: {arm2_verdict.status:<16} | Provenance: {arm2_verdict.provenance:<16} | Time: {arm2_time_ms:.1f} ms"
        )

        if arm2_verdict.macro_promoted:
            print(
                f"          -> Promoted Tool : Macro '{arm2_verdict.macro_promoted.name}' permanently inherited by agent."
            )

        results_table.append(
            {
                "task": task_name,
                "measurement_order": ["arm0", "arm1", "arm2"],
                "arm0_status": arm0_status,
                "arm0_shapes": arm0_shapes,
                "arm0_time_ms": arm0_time_ms,
                "arm1_status": arm1_res.status,
                "arm1_rounds": arm1_res.iterations,
                "arm1_time_ms": arm1_time_ms,
                "arm2_status": arm2_verdict.status,
                "arm2_provenance": arm2_verdict.provenance,
                "arm2_time_ms": arm2_time_ms,
            }
        )
        print()

    print("=" * 80)
    print("EXECUTIVE BENCHMARK SUMMARY")
    print("=" * 80)
    print(
        f"{'Task':<10} | {'Arm 0 (Blind)':<15} | {'Arm 1 (Z3 CEGIS)':<18} | {'Arm 2 (Neuro-Symbolic)':<22} | {'Arm 2 Time'}"
    )
    print("-" * 80)
    for r in results_table:
        arm1_label = f"{r['arm1_status']} (r={r['arm1_rounds']})"
        arm2_label = f"{r['arm2_status']} ({r['arm2_provenance']})"
        t_ms = r["arm2_time_ms"]
        print(
            f"{r['task']:<10} | {r['arm0_status']:<15} | {arm1_label:<18} | {arm2_label:<22} | {t_ms:.2f} ms"
        )
    print("=" * 80)
    print("MEASUREMENT NOTES:")
    print(
        "  Blind baseline: up to 200 proposals and 5 seconds per task, no counterexample feedback."
    )
    print(
        "  PROVED denotes an UNSAT negated specification within the task's declared precondition."
    )
    print("  EXHAUSTED/TIMEOUT are budget outcomes, not proofs of synthesis impossibility.")
    print(
        "  Arms ran in fixed order (Arm 0, Arm 1, Arm 2); cross-arm timings are not controlled for warm-up or caching."
    )
    print("  Task ordering and inherited macros can affect later results; no generalization claim.")
    print("=" * 80)


if __name__ == "__main__":
    main()
