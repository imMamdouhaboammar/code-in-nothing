"""Opt-in, public-only training feedback for experimental synthesis.

No verifier verdict, admission witness, or hidden counterexample enters this
module. All correctness claims still require cin.worlds.verify_program.
"""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from random import Random

from .contracts import validate_world
from .governor import Cost
from .ir import IRViolation, Limits, canonical_bytes, canonical_hash, check_tree, run_ir
from .worlds import check_formula

PANEL_VERSION = "cin.training-panel/v0.1"
EVALUATOR_VERSION = "cin.training-fitness/v0.1"
MAX_TRAINING_CASES = 256


@dataclass(frozen=True, init=False)
class PublicTrainingPanel:
    """Frozen, explicitly supplied public world relation and unique input pairs.

    The verifier-private witness is not an argument or a field in this type.
    The world is snapshot-serialized to prevent caller mutation after hashing.
    """

    _world_bytes: bytes
    cases: tuple[tuple[int, int], ...]
    digest: str

    def __init__(self, world: dict, cases: tuple[tuple[int, int], ...]):
        validate_world(world)
        if not isinstance(cases, (tuple, list)) or not 1 <= len(cases) <= MAX_TRAINING_CASES:
            raise ValueError("training panel must have 1..256 cases")
        domain = world["input_domain"]
        frozen = []
        for point in cases:
            if (
                not isinstance(point, (tuple, list))
                or len(point) != 2
                or any(type(value) is not int for value in point)
            ):
                raise ValueError("training cases must contain two integers")
            x, y = point
            if not (
                domain["x"]["min"] <= x <= domain["x"]["max"]
                and domain["y"]["min"] <= y <= domain["y"]["max"]
            ):
                raise ValueError("training case outside declared public world domain")
            frozen.append((x, y))
        if len(set(frozen)) != len(frozen):
            raise ValueError("duplicate public training cases")
        world_bytes = canonical_bytes(world)
        points = tuple(frozen)
        object.__setattr__(self, "_world_bytes", world_bytes)
        object.__setattr__(self, "cases", points)
        object.__setattr__(
            self,
            "digest",
            canonical_hash(
                {"version": PANEL_VERSION, "world": json.loads(world_bytes), "cases": points}
            ),
        )

    @property
    def world(self) -> dict:
        """Return an independent copy; the stored public specification cannot drift."""
        return json.loads(self._world_bytes)


@dataclass
class GuidedStats:
    """Measured bounded frontier-selection and mutation attempts."""

    selection_operations: int = 0
    mutation_attempts: int = 0


@dataclass(frozen=True)
class TrainingFitness:
    candidate_hash: str
    panel_hash: str
    status: str
    applicable_cases: int
    satisfied_cases: int
    pass_fraction: float | None
    case_errors: tuple[int | None, ...]
    cost: Cost
    evaluator_version: str = EVALUATOR_VERSION


def evaluate_training(
    expression: dict,
    panel: PublicTrainingPanel,
    base: dict,
    *,
    limits: Limits = Limits(),
) -> TrainingFitness:
    """Evaluate the full frozen public panel; never short-circuit on a FAIL.

    None means not measured (inapplicable or incomplete), not behavioral failure.
    Predicate work counts top-level formula invocations, not internal AST nodes.
    """
    if not isinstance(panel, PublicTrainingPanel):
        raise TypeError("a public training panel is required")
    candidate_hash = canonical_hash(expression)
    try:
        check_tree(expression, base)
        if panel.world["input_types"] != base.get("input_types", ["Int", "Int"]):
            raise IRViolation("training world and genome signatures differ")
    except IRViolation:
        return TrainingFitness(
            candidate_hash,
            panel.digest,
            "INVALID",
            0,
            0,
            None,
            tuple(None for _ in panel.cases),
            Cost(),
        )

    world = panel.world
    errors: list[int | None] = []
    applicable = satisfied = attempted = operations = predicates = 0
    for x, y in panel.cases:
        values = {"x": x, "y": y, "result": 0}
        predicates += 1
        if not check_formula(world["precondition"], values):
            errors.append(None)
            continue
        applicable += 1
        attempted += 1
        measured = [0]
        try:
            values["result"] = run_ir(expression, x, y, limits, ops_counter=measured)
        except IRViolation:
            operations += measured[0]
            errors.extend([None] * (len(panel.cases) - len(errors)))
            return TrainingFitness(
                candidate_hash,
                panel.digest,
                "UNKNOWN",
                applicable,
                satisfied,
                None,
                tuple(errors),
                Cost(
                    training_cases=attempted,
                    training_interpreter_operations=operations,
                    predicate_evaluations=predicates,
                ),
            )
        operations += measured[0]
        predicates += 1
        ok = check_formula(world["postcondition"], values)
        satisfied += int(ok)
        errors.append(0 if ok else 1)
    status = "COMPLETE" if applicable else "VACUOUS"
    return TrainingFitness(
        candidate_hash,
        panel.digest,
        status,
        applicable,
        satisfied,
        satisfied / applicable if applicable else None,
        tuple(errors),
        Cost(
            training_cases=attempted,
            training_interpreter_operations=operations,
            predicate_evaluations=predicates,
        ),
    )


class GuidedFrontier:
    """Bounded graded selection with case-vector diversity and typed neighbors.

    Only public TrainingFitness is accepted. The caller owns formal verification,
    resource reservations, candidate replay and lifecycle promotion.
    """

    def __init__(self, base: dict, *, seed: int = 0, max_pool: int = 32):
        if type(seed) is not int or seed < 0:
            raise ValueError("seed must be a nonnegative integer")
        if type(max_pool) is not int or not 1 <= max_pool <= 256:
            raise ValueError("max_pool must be 1..256")
        self.base = deepcopy(base)
        self.seed = seed
        self.max_pool = max_pool
        self._panel_hash: str | None = None
        self._entries: dict[str, tuple[dict, TrainingFitness]] = {}

    def add(self, expression: dict, fitness: TrainingFitness) -> None:
        if (
            not isinstance(fitness, TrainingFitness)
            or fitness.status != "COMPLETE"
            or fitness.pass_fraction is None
            or fitness.candidate_hash != canonical_hash(expression)
        ):
            raise ValueError("complete matching public training evidence required")
        check_tree(expression, self.base)
        if self._panel_hash is None:
            self._panel_hash = fitness.panel_hash
        if fitness.panel_hash != self._panel_hash:
            raise ValueError("cannot mix frozen training panels")
        self._entries[fitness.candidate_hash] = (deepcopy(expression), fitness)
        ranked = sorted(
            self._entries.items(),
            key=lambda item: (-item[1][1].pass_fraction, item[0]),
        )
        # Preserve representatives of distinct case-level failure patterns.
        retained: dict[str, tuple[dict, TrainingFitness]] = {}
        seen_vectors: set[tuple[int | None, ...]] = set()
        for key, value in ranked:
            if value[1].case_errors in seen_vectors:
                continue
            retained[key] = value
            seen_vectors.add(value[1].case_errors)
            if len(retained) >= self.max_pool:
                break
        self._entries = retained

    def select(self, *, excluded: set[str] | None = None, stats: GuidedStats | None = None) -> dict:
        eligible = (
            (key, item)
            for key, item in self._entries.items()
            if key not in (excluded if excluded is not None else ())
        )
        ranked = sorted(
            eligible,
            key=lambda item: (-item[1][1].pass_fraction, item[0]),
        )
        if not ranked:
            raise ValueError("frontier has no unexpanded parent")
        if stats is not None:
            stats.selection_operations += len(self._entries)
        return deepcopy(ranked[0][1][0])

    def neighbors(self, parent: dict, *, stats: GuidedStats | None = None) -> tuple[dict, ...]:
        """Deterministic bounded typed structural mutations of the selected parent."""
        check_tree(parent, self.base)
        arity = len(self.base.get("input_types", ("Int", "Int")))
        allowed = set(self.base["allowed_primitives"])
        leaves = []
        if "Arg" in allowed:
            leaves.extend({"op": "Arg", "index": i} for i in range(arity))
        if "ConstInt" in allowed:
            leaves.extend({"op": "ConstInt", "value": c} for c in self.base["allowed_constants"])
        leaves = leaves[:16]
        variants: list[dict] = []
        for leaf in leaves:
            for op in ("Add", "Sub"):
                if op in allowed:
                    variants.append({"op": op, "args": [deepcopy(parent), leaf]})
                    variants.append({"op": op, "args": [leaf, deepcopy(parent)]})
        if {"If", "LessThan", "Arg"}.issubset(allowed) and arity >= 2:
            condition = {
                "op": "LessThan",
                "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 1}],
            }
            for leaf in leaves:
                variants.append({"op": "If", "args": [condition, deepcopy(parent), leaf]})
                variants.append({"op": "If", "args": [condition, leaf, deepcopy(parent)]})
        if stats is not None:
            stats.mutation_attempts += len(variants)
        Random(self.seed + int(canonical_hash(parent)[:12], 16)).shuffle(variants)
        output = []
        seen = {canonical_hash(parent)}
        for expr in variants:
            digest = canonical_hash(expr)
            if digest in seen:
                continue
            try:
                check_tree(expr, self.base)
            except IRViolation:
                continue
            seen.add(digest)
            output.append(expr)
            if len(output) == 32:
                break
        return tuple(output)
