"""Bounded B0/B1/B2 synthesis ablations with an independent acceptance gate.

B0 and B1 use the exact legacy task-blind candidate stream. B1 measures
fitness without feeding it into generation. B2 expands scored, typed parents.
No verifier counterexample or admission witness is fed to selection.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import asdict

from .governor import Cost, Governor
from .ir import Limits, canonical_hash
from .search import SearchStats, _probe_inputs, candidate_stream
from .training import GuidedFrontier, GuidedStats, PublicTrainingPanel, evaluate_training
from .worlds import verify_program

ARMS = ("B0", "B1", "B2")
ACTOR = "synthesis"
MAX_WORLD_CASES = 4096


def _domain_size(world: dict) -> int:
    return (world["input_domain"]["x"]["max"] - world["input_domain"]["x"]["min"] + 1) * (
        world["input_domain"]["y"]["max"] - world["input_domain"]["y"]["min"] + 1
    )


def _search_cap(base: dict, n: int) -> Cost:
    shapes = max(3000, 100 * n) + 1
    arity = len(base.get("input_types", ("Int", "Int")))
    leaves = arity + len(base["allowed_constants"])
    probes = (shapes + leaves + 1) * len(_probe_inputs(arity))
    return Cost(search_shapes=shapes, probe_evaluations=probes)


def _limits(n: int, panel_size: int, domain_size: int, base: dict) -> Cost:
    per_case = Limits().max_nodes + 1
    search = _search_cap(base, n)
    return Cost(
        candidate_evaluations=n,
        verifier_calls=n,
        verifier_cases=n * domain_size,
        interpreter_operations=n * domain_size * per_case,
        search_shapes=search.search_shapes,
        probe_evaluations=search.probe_evaluations,
        training_cases=n * panel_size,
        training_interpreter_operations=n * panel_size * per_case,
        predicate_evaluations=n * panel_size * 2,
        selection_operations=n * 32,
        mutation_attempts=n * 96,
    )


def _charged(governor: Governor, reservation: Cost, actual: Cost) -> None:
    grant = governor.reserve(ACTOR, reservation)
    governor.settle(grant, actual)


def run_trial(
    arm: str,
    world: dict,
    base: dict,
    panel: PublicTrainingPanel,
    *,
    seed: int = 0,
    max_proposals: int = 250,
) -> dict:
    """Reproducible experimental trial under the same per-dimension quotas.

    The result is not an organism, a world admission or a universal proof.
    Counters represent distinct operations, not calibrated CPU instructions.
    """
    if arm not in ARMS:
        raise ValueError("unknown experimental arm")
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be nonnegative")
    if type(max_proposals) is not int or not 1 <= max_proposals <= 30000:
        raise ValueError("max_proposals must be 1..30000")
    if world != panel.world:
        raise ValueError("the fixed public panel must belong to the evaluation world")
    if world["input_types"] != base.get("input_types", ["Int", "Int"]):
        raise ValueError("world and genome signatures differ")
    domain_size = _domain_size(world)
    if not 1 <= domain_size <= MAX_WORLD_CASES:
        raise ValueError("world outside the existing exhaustive verifier scope")

    policy = _limits(max_proposals, len(panel.cases), domain_size, base)
    governor = Governor(policy)
    governor.register(ACTOR, policy)
    bootstrap = max_proposals if arm != "B2" else min(12, max(1, max_proposals // 4))
    stats = SearchStats()
    generator_reservation = _search_cap(base, bootstrap)
    generator_grant = governor.reserve(ACTOR, generator_reservation)
    stream = candidate_stream(
        base["starting_expression"],
        base,
        seed=seed,
        max_proposals=bootstrap,
        stats=stats,
    )
    frontier = GuidedFrontier(base, seed=seed, max_pool=32) if arm == "B2" else None
    queue: deque[dict] = deque()
    seen: set[str] = set()
    expanded: set[str] = set()
    parent_trace: list[str] = []
    candidate_hashes: list[str] = []
    fitness_trace: list[float] = []
    verdict_counts = {"PASS": 0, "FAIL": 0, "INVALID": 0, "UNKNOWN": 0}
    verified_hash = None
    evaluated = 0
    generated = 0
    stop_reason = "CANDIDATE_BUDGET"
    start = time.process_time()

    try:
        while evaluated < max_proposals:
            expression = None
            if arm != "B2" or generated < bootstrap:
                try:
                    expression = next(stream).expression
                    generated += 1
                except StopIteration:
                    stop_reason = "SEARCH_EXHAUSTED"
                    break
            else:
                assert frontier is not None
                while not queue:
                    selection_grant = governor.reserve(
                        ACTOR, Cost(selection_operations=32, mutation_attempts=96)
                    )
                    measured = GuidedStats()
                    try:
                        parent = frontier.select(excluded=expanded, stats=measured)
                        expanded.add(canonical_hash(parent))
                        parent_trace.append(canonical_hash(parent))
                        neighbors = frontier.neighbors(parent, stats=measured)
                        queue.extend(expr for expr in neighbors if canonical_hash(expr) not in seen)
                    except ValueError:
                        stop_reason = "FRONTIER_EXHAUSTED"
                    finally:
                        governor.settle(
                            selection_grant,
                            Cost(
                                selection_operations=measured.selection_operations,
                                mutation_attempts=measured.mutation_attempts,
                            ),
                        )
                    if stop_reason == "FRONTIER_EXHAUSTED":
                        break
                if not queue:
                    break
                expression = queue.popleft()

            digest = canonical_hash(expression)
            if digest in seen:
                continue
            seen.add(digest)
            candidate_hashes.append(digest)
            _charged(governor, Cost(candidate_evaluations=1), Cost(candidate_evaluations=1))
            evaluated += 1

            if arm in ("B1", "B2"):
                per_case = Limits().max_nodes + 1
                grant = governor.reserve(
                    ACTOR,
                    Cost(
                        training_cases=len(panel.cases),
                        training_interpreter_operations=len(panel.cases) * per_case,
                        predicate_evaluations=len(panel.cases) * 2,
                    ),
                )
                try:
                    fitness = evaluate_training(expression, panel, base)
                finally:
                    governor.settle(grant, fitness.cost)
                if fitness.pass_fraction is not None:
                    fitness_trace.append(fitness.pass_fraction)
                if frontier is not None and fitness.status == "COMPLETE":
                    frontier.add(expression, fitness)

            verification_grant = governor.reserve(
                ACTOR,
                Cost(
                    verifier_calls=1,
                    verifier_cases=domain_size,
                    interpreter_operations=domain_size * (Limits().max_nodes + 1),
                ),
            )
            verdict = verify_program(expression, world, base, max_cases=MAX_WORLD_CASES)
            governor.settle(
                verification_grant,
                Cost(
                    verifier_calls=1,
                    verifier_cases=verdict.checked,
                    interpreter_operations=verdict.operations,
                ),
            )
            verdict_counts[verdict.status] += 1
            if verdict.status == "PASS":
                verified_hash = digest
                stop_reason = "INDEPENDENT_PASS"
                break
    finally:
        stream.close()
        governor.settle(
            generator_grant,
            Cost(
                search_shapes=stats.attempted_shapes,
                probe_evaluations=stats.probe_evaluations,
            ),
        )

    governor.stop(ACTOR, stop_reason)
    costs = asdict(governor.snapshot(ACTOR))
    # These counts are an explicit accounting proxy, not calibrated CPU work.
    accounted_events = sum(costs.values())
    return {
        "protocol": "cin.guided-ablation/v0.1",
        "arm": arm,
        "seed": seed,
        "task_id": world["id"],
        "world_hash": canonical_hash(world),
        "training_panel_hash": panel.digest,
        "proposal_limit": max_proposals,
        "verifier_domain_size": domain_size,
        "status": "PASS" if verified_hash is not None else "UNKNOWN",
        "stop_reason": stop_reason,
        "verified_program_hash": verified_hash,
        "proposals_evaluated": evaluated,
        "verdict_counts": verdict_counts,
        "selected_parent_hashes": parent_trace,
        "candidate_hashes": candidate_hashes,
        "fitness_trajectory": fitness_trace,
        "cost": costs,
        "accounted_events": accounted_events,
        "cpu_seconds": round(time.process_time() - start, 5),
        "limits": {
            "candidate_limit": max_proposals,
            "resource_vector": asdict(policy),
        },
        "admission": "not_run",
        "inherited_capability": False,
        "proof_scope": "FINITE_EXHAUSTIVE" if verified_hash is not None else "UNKNOWN",
    }
