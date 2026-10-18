"""Opt-in, single-process finite epochs on the actual CIN search and verifier."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict

from .contracts import validate_genome, validate_world
from .governor import Cost, Governor
from .ir import Limits, canonical_hash
from .search import SearchStats, _probe_inputs, candidate_stream
from .worlds import AdmissionStats, admit_world, verify_program

_ACTOR = "organism-0"
_MAX_CASES = 512
# The interpreter's per-input bounds include the instruction that exhausts it.
_PER_CASE_OPS = Limits().max_ops + 1


def _search_reservation(base: dict, proposals: int) -> Cost:
    """Conservative, enforced maxima for the existing bounded enumerator."""
    shape_limit = max(3000, 100 * proposals) + 1
    leaves = len(base.get("input_types", ["Int", "Int"])) + len(base["allowed_constants"])
    points = len(_probe_inputs(len(base.get("input_types", ["Int", "Int"]))))
    return Cost(
        search_shapes=shape_limit,
        probe_evaluations=(shape_limit + leaves + 1) * points,
    )


class FiniteScheduler:
    """A finite search/epoch controller. Does not publish offspring or checkpoints.

    P1-03 must add durable state and atomic births. This class does not turn
    widened domains into semantically new mathematical capabilities.
    """

    def __init__(
        self,
        genome: dict,
        world: dict,
        *,
        seed: int = 0,
        max_evals: int | None = None,
        admission_budget: int = 250,
    ):
        self.genome = validate_genome(genome)
        self.world = validate_world(world)
        if type(seed) is not int or seed < 0:
            raise ValueError("seed must be a nonnegative integer")
        if type(admission_budget) is not int or admission_budget < 1:
            raise ValueError("admission budget must be a positive integer")
        if max_evals is not None and (type(max_evals) is not int or max_evals < 1):
            raise ValueError("evaluation budget must be a positive integer")
        self.seed = seed
        self.admission_budget = admission_budget
        self.base = self.genome["genome"]["base"]
        self.max_evals = min(
            max_evals if max_evals is not None else 2000,
            self.genome["genome"]["stop_station"]["max_candidate_evaluations"],
        )
        self.max_epochs = self.genome["genome"]["stop_station"]["max_epochs"]
        self.epoch_proposals = self.genome["genome"]["directive"]["proposals_per_epoch"]
        self.plateau = self.genome["genome"]["stop_station"]["plateau_consecutive_epochs"]
        self.grace = self.genome["genome"]["stop_station"]["plateau_grace_epochs"]
        self._report: dict | None = None

    def run(self) -> dict:
        if self._report is not None:
            return deepcopy(self._report)

        admission_shape = _search_reservation(self.base, self.admission_budget)
        candidate_shape = _search_reservation(self.base, self.max_evals)
        # 1 seed check + up to N candidate checks + 1 independent success replay.
        potential_calls = self.admission_budget + self.max_evals + 2
        verifier_cap = potential_calls * _MAX_CASES * _PER_CASE_OPS
        policy = Cost(
            candidate_evaluations=self.max_evals,
            admission_candidates=self.admission_budget,
            verifier_calls=potential_calls,
            interpreter_operations=verifier_cap,
            search_shapes=admission_shape.search_shapes + candidate_shape.search_shapes,
            probe_evaluations=(
                admission_shape.probe_evaluations + candidate_shape.probe_evaluations
            ),
        )
        governor = Governor(policy)
        governor.register(_ACTOR, policy)

        admission_grant = governor.reserve(
            _ACTOR,
            Cost(
                admission_candidates=self.admission_budget,
                verifier_calls=self.admission_budget,
                interpreter_operations=self.admission_budget * _MAX_CASES * _PER_CASE_OPS,
                search_shapes=admission_shape.search_shapes,
                probe_evaluations=admission_shape.probe_evaluations,
            ),
        )
        admission_stats = AdmissionStats()
        admitted = admit_world(
            self.world,
            self.base,
            max_proposals=self.admission_budget,
            max_cases=_MAX_CASES,
            stats=admission_stats,
        )
        governor.settle(
            admission_grant,
            Cost(
                admission_candidates=admitted.candidates_checked,
                verifier_calls=admission_stats.verifier_calls,
                interpreter_operations=admission_stats.interpreter_operations,
                search_shapes=admission_stats.search_shapes,
                probe_evaluations=admission_stats.probe_evaluations,
            ),
        )

        epochs = 0
        evaluated = 0
        epoch_evaluations: list[int] = []
        acquired_hash = None
        reason = "WORLD_NOT_ADMITTED"
        if admitted.status == "ADMITTED":
            seed_verdict = self._verify_governed(
                governor, self.base["starting_expression"]
            )
            if seed_verdict.status == "PASS":
                reason = "SEED_ALREADY_SOLVED"
            else:
                reason, epochs, evaluated, epoch_evaluations, acquired_hash = self._search(
                    governor
                )

        governor.stop(_ACTOR, reason)
        report = {
            "scheduler_version": "cin.scheduler/v0.1",
            "seed": self.seed,
            "finite_domain_only": True,
            "world_admission": admitted.status,
            "epochs": epochs,
            "epoch_evaluations": epoch_evaluations,
            "candidate_evaluations": evaluated,
            "verified_capabilities": int(acquired_hash is not None),
            "accepted_program_hash": acquired_hash,
            "stop_reason": reason,
            "terminal_events": 1,
            "cost": asdict(governor.snapshot(_ACTOR)),
            "accounting_scope": "bounded search proposals, probes, admission and verifier calls",
            "durable_resume": "NOT_IMPLEMENTED",
        }
        self._report = deepcopy(report)
        return report

    def _verify_governed(self, governor: Governor, expression: dict):
        # The maximum is deliberately conservative; actual interpreter work
        # is charged on settlement, including FAIL and UNKNOWN outcomes.
        upper = Cost(verifier_calls=1, interpreter_operations=_MAX_CASES * _PER_CASE_OPS)
        grant = governor.reserve(_ACTOR, upper)
        verdict = verify_program(expression, self.world, self.base, max_cases=_MAX_CASES)
        governor.settle(
            grant,
            Cost(verifier_calls=1, interpreter_operations=verdict.operations),
        )
        return verdict

    def _search(self, governor: Governor) -> tuple[str, int, int, list[int], str | None]:
        reservation = _search_reservation(self.base, self.max_evals)
        grant = governor.reserve(_ACTOR, reservation)
        stats = SearchStats()
        stream = candidate_stream(
            self.base["starting_expression"],
            self.base,
            seed=self.seed,
            max_proposals=self.max_evals,
            stats=stats,
        )
        evaluated = 0
        epochs = 0
        counts: list[int] = []
        found = None
        reason = "EPOCH_LIMIT"
        try:
            for epoch in range(1, self.max_epochs + 1):
                this_epoch = 0
                for _ in range(min(self.epoch_proposals, self.max_evals - evaluated)):
                    try:
                        proposal = next(stream)
                    except StopIteration:
                        reason = "SEARCH_EXHAUSTED"
                        break
                    cost_grant = governor.reserve(_ACTOR, Cost(candidate_evaluations=1))
                    governor.settle(cost_grant, Cost(candidate_evaluations=1))
                    evaluated += 1
                    this_epoch += 1
                    verdict = self._verify_governed(governor, proposal.expression)
                    if verdict.status == "PASS":
                        replay = self._verify_governed(governor, proposal.expression)
                        if replay.status == "PASS":
                            found = canonical_hash(proposal.expression)
                            reason = "VERIFIED_ACQUISITION"
                            break
                if this_epoch:
                    epochs += 1
                    counts.append(this_epoch)
                if found or reason == "SEARCH_EXHAUSTED":
                    break
                if evaluated >= self.max_evals:
                    reason = "CANDIDATE_BUDGET"
                    break
                if epoch >= self.grace and epoch >= self.plateau:
                    reason = "PLATEAU"
                    break
        finally:
            governor.settle(
                grant,
                Cost(
                    search_shapes=stats.attempted_shapes,
                    probe_evaluations=stats.probe_evaluations,
                ),
            )
            stream.close()
        return reason, epochs, evaluated, counts, found
