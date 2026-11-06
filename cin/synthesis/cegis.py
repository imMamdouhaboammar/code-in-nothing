"""Counterexample-Guided Inductive Synthesis (CEGIS) engine powered by Z3.

Eliminates the artificial restriction of hiding failure points:
In each round, the SMT verifier (Z3) checks the synthesized candidate against the
unbounded formal specification. If a counterexample exists, it is extracted and
injected directly into the inductive training set until the candidate is formally proved.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from .decision import DecisionResult, synthesize_conditional_tree
from .library import MacroRegistry
from .sygus import SyGuSTask
from .z3_verifier import HAS_Z3, Z3Verdict, verify_spec_with_z3


@dataclass
class CEGISResult:
    """Outcome of a Counterexample-Guided Inductive Synthesis execution."""

    status: str  # "PROVED", "EXHAUSTED", "SYNTHESIS_FAILED", "UNSUPPORTED"
    expression: dict | None
    iterations: int
    counterexamples: list[tuple[int, ...]] = field(default_factory=list)
    total_shapes_attempted: int = 0
    total_evaluations: int = 0
    elapsed_ms: float = 0.0
    z3_verdict: Z3Verdict | None = None
    ast_nodes: int = 0
    ast_depth: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "expression": self.expression,
            "iterations": self.iterations,
            "counterexamples_count": len(self.counterexamples),
            "counterexamples": self.counterexamples,
            "total_shapes_attempted": self.total_shapes_attempted,
            "total_evaluations": self.total_evaluations,
            "elapsed_ms": self.elapsed_ms,
            "z3_verdict": self.z3_verdict.to_dict() if self.z3_verdict else None,
            "ast_nodes": self.ast_nodes,
            "ast_depth": self.ast_depth,
        }


def run_cegis_loop(
    task: SyGuSTask,
    base: dict,
    *,
    macro_registry: MacroRegistry | None = None,
    max_rounds: int = 15,
    timeout_sec: float = 30.0,
) -> CEGISResult:
    """Executes a full CEGIS loop for a given SyGuS task using Z3.

    Args:
        task: Formal SyGuS benchmark task.
        base: Organism base genome configuration.
        macro_registry: Optional MacroRegistry containing inherited functional abstractions.
        max_rounds: Maximum counterexample refinement rounds.
        timeout_sec: Maximum wall-clock time in seconds.

    Returns:
        CEGISResult with formal mathematical verification outcome.
    """
    if not HAS_Z3:
        return CEGISResult(
            status="UNSUPPORTED",
            expression=None,
            iterations=0,
            elapsed_ms=0.0,
        )

    t0 = time.perf_counter()
    arity = task.arity

    # Only admitted points constrain the inductive synthesis phase.
    # Public task preconditions are the source of admissibility, not an output oracle.
    from .z3_verifier import z3

    def in_precondition(point: tuple[int, ...]) -> bool:
        if len(point) != arity:
            return False
        if task.precondition is None:
            return True
        solver = z3.Solver()
        solver.add(task.precondition([z3.IntVal(value) for value in point]))
        return solver.check() == z3.sat

    candidates = list(task.initial_seed_cases)
    if not candidates:
        candidates = [tuple([0] * arity)]
        for i in range(arity):
            point = [0] * arity
            point[i] = 1
            candidates.append(tuple(point))

    active_points: list[tuple[int, ...]] = list(
        dict.fromkeys(point for point in candidates if in_precondition(point))
    )
    if not active_points and task.precondition is not None:
        solver = z3.Solver()
        symbolic = [z3.Int(f"seed_{i}") for i in range(arity)]
        solver.add(task.precondition(symbolic))
        if solver.check() == z3.sat:
            model = solver.model()
            active_points.append(
                tuple(model.eval(value, model_completion=True).as_long() for value in symbolic)
            )
    if not active_points:
        return CEGISResult(
            status="SYNTHESIS_FAILED",
            expression=None,
            iterations=0,
            elapsed_ms=(time.perf_counter() - t0) * 1000,
        )

    seen_points: set[tuple[int, ...]] = set(active_points)
    total_shapes = 0
    total_evals = 0
    rounds_started = 0

    for rnd in range(1, max_rounds + 1):
        if time.perf_counter() - t0 > timeout_sec:
            break
        rounds_started = rnd

        # Calculate oracle values for current active points
        cases_tuple = tuple(active_points)
        target_outputs = tuple(task.reference_oracle(*pt) for pt in cases_tuple)

        # Inductive Synthesis Phase: synthesize program covering active points
        res: DecisionResult | None = synthesize_conditional_tree(
            cases_tuple,
            target_outputs,
            base,
            macro_registry=macro_registry,
        )

        if res is None:
            elapsed = (time.perf_counter() - t0) * 1000
            return CEGISResult(
                status="SYNTHESIS_FAILED",
                expression=None,
                iterations=rnd,
                counterexamples=active_points,
                total_shapes_attempted=total_shapes,
                total_evaluations=total_evals,
                elapsed_ms=elapsed,
            )

        total_shapes += res.shapes_attempted
        total_evals += res.candidate_evaluations
        candidate_expr = res.expression

        # Formal Verification Phase: Query Z3 across unbounded Z^k
        z3_verdict = verify_spec_with_z3(
            candidate_expr,
            task.z3_spec,
            arity=task.arity,
            var_names=task.variable_names,
            precondition=task.precondition,
        )

        # Condition 1: Formally Proved
        if z3_verdict.status == "SYMBOLIC_PROVED":
            elapsed = (time.perf_counter() - t0) * 1000
            return CEGISResult(
                status="PROVED",
                expression=candidate_expr,
                iterations=rnd,
                counterexamples=active_points,
                total_shapes_attempted=total_shapes,
                total_evaluations=total_evals,
                elapsed_ms=elapsed,
                z3_verdict=z3_verdict,
                ast_nodes=res.nodes,
                ast_depth=res.depth,
            )

        # Condition 2: Counterexample found
        if z3_verdict.status == "COUNTEREXAMPLE" and z3_verdict.counterexample is not None:
            ce = z3_verdict.counterexample
            if ce in seen_points:
                # Same counterexample repeated: avoid cycle
                break
            seen_points.add(ce)
            active_points.append(ce)
        else:
            # Solver timed out or returned unknown
            break

    elapsed = (time.perf_counter() - t0) * 1000
    return CEGISResult(
        status="EXHAUSTED",
        expression=None,
        iterations=rounds_started,
        counterexamples=active_points,
        total_shapes_attempted=total_shapes,
        total_evaluations=total_evals,
        elapsed_ms=elapsed,
    )
