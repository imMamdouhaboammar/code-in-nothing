"""Single-process reservation ledger for finite, per-actor experiment resources."""

from __future__ import annotations

from dataclasses import dataclass, fields


class BudgetExceeded(ValueError):
    """An operation cannot be admitted under the remaining resource limits."""


@dataclass(frozen=True)
class Cost:
    candidate_evaluations: int = 0
    admission_candidates: int = 0
    verifier_calls: int = 0
    interpreter_operations: int = 0
    search_shapes: int = 0
    probe_evaluations: int = 0
    training_cases: int = 0
    training_interpreter_operations: int = 0
    predicate_evaluations: int = 0
    selection_operations: int = 0

    def __post_init__(self) -> None:
        if any(
            type(getattr(self, field.name)) is not int or getattr(self, field.name) < 0
            for field in fields(self)
        ):
            raise ValueError("cost dimensions must be nonnegative integers")

    def __add__(self, other: Cost) -> Cost:
        return Cost(
            **{f.name: getattr(self, f.name) + getattr(other, f.name) for f in fields(self)}
        )

    def __sub__(self, other: Cost) -> Cost:
        return Cost(
            **{f.name: getattr(self, f.name) - getattr(other, f.name) for f in fields(self)}
        )

    def fits(self, limit: Cost) -> bool:
        return all(getattr(self, f.name) <= getattr(limit, f.name) for f in fields(self))


@dataclass(frozen=True)
class Grant:
    actor_id: str
    sequence: int
    owner: object


class Governor:
    """Reserve an upper bound before work, then account for its actual usage.

    Reservation and settlement happen in a single sequential process. Journal-
    backed restore and atomic persistence are deferred to P1-03.
    """

    def __init__(self, global_limit: Cost):
        self._global_limit = global_limit
        self._limits: dict[str, Cost] = {}
        self._spent: dict[str, Cost] = {}
        self._reserved: dict[str, Cost] = {}
        self._stopped: dict[str, str] = {}
        self._pending: dict[int, tuple[Grant, Cost]] = {}
        self._next_sequence = 0
        self._identity = object()

    def register(self, actor_id: str, limit: Cost) -> None:
        if not isinstance(actor_id, str) or not actor_id or actor_id in self._limits:
            raise ValueError("missing or duplicate actor ID")
        if not limit.fits(self._global_limit):
            raise ValueError("actor limit exceeds global limit")
        self._limits[actor_id] = limit
        self._spent[actor_id] = Cost()
        self._reserved[actor_id] = Cost()

    def _require_active(self, actor_id: str) -> None:
        if actor_id not in self._limits or actor_id in self._stopped:
            raise ValueError("unknown or terminated actor")

    def _global_used(self) -> Cost:
        used = Cost()
        for actor in self._limits:
            used += self._spent[actor] + self._reserved[actor]
        return used

    def reserve(self, actor_id: str, proposed: Cost) -> Grant:
        self._require_active(actor_id)
        if not (self._spent[actor_id] + self._reserved[actor_id] + proposed).fits(
            self._limits[actor_id]
        ) or not (self._global_used() + proposed).fits(self._global_limit):
            raise BudgetExceeded("reservation exceeds actor or cohort resource policy")
        grant = Grant(actor_id, self._next_sequence, self._identity)
        self._next_sequence += 1
        self._reserved[actor_id] += proposed
        self._pending[grant.sequence] = (grant, proposed)
        return grant

    def settle(self, grant: Grant, actual: Cost) -> None:
        if (
            not isinstance(grant, Grant)
            or grant.owner is not self._identity
            or grant.sequence not in self._pending
            or self._pending[grant.sequence][0] != grant
        ):
            raise ValueError("unknown, foreign or already settled grant")
        self._require_active(grant.actor_id)
        _, reserved = self._pending[grant.sequence]
        if not actual.fits(reserved):
            self._stopped[grant.actor_id] = "GOVERNOR_VIOLATION"
            raise BudgetExceeded("actual work exceeds reserved resources")
        del self._pending[grant.sequence]
        self._reserved[grant.actor_id] -= reserved
        self._spent[grant.actor_id] += actual

    def snapshot(self, actor_id: str) -> Cost:
        if actor_id not in self._limits:
            raise ValueError("unknown actor")
        return self._spent[actor_id]

    def remaining(self, actor_id: str) -> Cost:
        if actor_id not in self._limits:
            raise ValueError("unknown actor")
        return self._limits[actor_id] - self._spent[actor_id] - self._reserved[actor_id]

    def stop(self, actor_id: str, reason: str) -> bool:
        if actor_id not in self._limits or not isinstance(reason, str) or not reason:
            raise ValueError("unknown actor or invalid stop reason")
        if actor_id in self._stopped:
            return False
        if any(grant.actor_id == actor_id for grant, _ in self._pending.values()):
            raise ValueError("cannot stop while work is unsettled")
        self._stopped[actor_id] = reason
        return True

    def stop_reason(self, actor_id: str) -> str | None:
        if actor_id not in self._limits:
            raise ValueError("unknown actor")
        return self._stopped.get(actor_id)
