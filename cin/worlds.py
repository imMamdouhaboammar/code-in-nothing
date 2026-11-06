"""Formal-world DSL, strict world admission, exhaustive finite-domain checks.

Witness synthesis occurs inside admission and only a witness digest is returned.
This does not establish universal validity outside the declared finite domain.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from itertools import product

from .contracts import ContractError, validate_world
from .ir import IRViolation, Limits, canonical_hash, check_tree, run_ir_args
from .search import SearchStats, candidate_stream


class WorldViolation(ValueError):
    pass


@dataclass(frozen=True)
class Verdict:
    status: str
    checked: int
    counterexample: tuple[int, int] | None = None
    reason: str = ""
    operations: int = 0


@dataclass(frozen=True)
class Admission:
    status: str
    spec_hash: str
    witness_hash: str | None
    reason: str
    candidates_checked: int


@dataclass
class AdmissionStats:
    """Public verifier-side work counters; never expose witness expressions."""

    verifier_calls: int = 0
    interpreter_operations: int = 0
    search_shapes: int = 0
    probe_evaluations: int = 0


def _term(v, values):
    if type(v) is int:
        return v
    if isinstance(v, dict) and set(v) == {"sub"}:
        a, b = v["sub"]
        return _term(a, values) - _term(b, values)
    if isinstance(v, dict) and set(v) == {"add"}:
        a, b = v["add"]
        return _term(a, values) + _term(b, values)
    if v in values:
        return values[v]
    raise WorldViolation(f"unrecognized term: {v}")


def check_formula(formula: dict, values: dict) -> bool:
    if not isinstance(formula, dict) or len(formula) != 1:
        raise WorldViolation("invalid formula")
    op, args = next(iter(formula.items()))
    if op == "and":
        return all(check_formula(part, values) for part in args)
    if op == "or":
        return any(check_formula(part, values) for part in args)
    a, b = (_term(v, values) for v in args)
    if op == "gte":
        return a >= b
    if op == "lte":
        return a <= b
    if op == "eq":
        return a == b
    raise WorldViolation("unknown formula operator")


def _inputs(world, max_cases: int):
    domain = world["input_domain"]
    var_names = list(domain.keys())
    ranges = [range(domain[k]["min"], domain[k]["max"] + 1) for k in var_names]
    count = 1
    for r in ranges:
        count *= len(r)
    if count > max_cases:
        raise WorldViolation("domain exceeds exhaustive budget")
    if count < 1:
        raise WorldViolation("empty domain")
    for pt in product(*ranges):
        yield pt


def _require_matching_signature(world: dict, base: dict) -> None:
    if world["input_types"] != base.get("input_types") or world["return_type"] != base.get(
        "return_type"
    ):
        raise WorldViolation("genome and world function signatures differ")


def verify_program(
    program: dict, world: dict, base: dict, limits: Limits = Limits(), max_cases: int = 4096
) -> Verdict:
    try:
        validate_world(world)
        _require_matching_signature(world, base)
        check_tree(program, base)
        points = list(_inputs(world, max_cases))
    except (ContractError, IRViolation, WorldViolation) as exc:
        return Verdict("INVALID", 0, reason=str(exc))
    checked = 0
    ops = [0]
    var_names = list(world["input_domain"].keys())
    arity = len(var_names)
    for point in points:
        values = {k: v for k, v in zip(var_names, point)}
        values["result"] = 0
        if not check_formula(world["precondition"], values):
            continue
        checked += 1
        try:
            values["result"] = run_ir_args(
                program, point, limits, ops_counter=ops, expected_arity=arity
            )
        except IRViolation as exc:
            return Verdict("UNKNOWN", checked, point, str(exc), ops[0])
        if not check_formula(world["postcondition"], values):
            return Verdict("FAIL", checked, point, "postcondition counterexample", ops[0])
    if checked == 0:
        return Verdict("INVALID", 0, reason="vacuous precondition")
    return Verdict("PASS", checked, operations=ops[0])


def admit_world(
    world: dict,
    base: dict,
    max_proposals: int = 1000,
    max_cases: int = 4096,
    stats: AdmissionStats | None = None,
) -> Admission:
    spec_hash = canonical_hash(world)
    try:
        validate_world(world)
        _require_matching_signature(world, base)
        points = list(_inputs(world, max_cases))
        var_names = list(world["input_domain"].keys())
        if not any(
            check_formula(
                world["precondition"], {**{k: v for k, v in zip(var_names, pt)}, "result": 0}
            )
            for pt in points
        ):
            return Admission("REJECTED", spec_hash, None, "vacuous precondition", 0)
    except (ContractError, WorldViolation) as exc:
        return Admission("REJECTED", spec_hash, None, str(exc), 0)
    checked = 0
    search_stats = SearchStats()
    # Only aggregate counters and the witness digest cross the verifier boundary.
    try:
        for proposal in candidate_stream(
            {"op": "Arg", "index": 0},
            base,
            seed=0,
            max_proposals=max_proposals,
            stats=search_stats,
        ):
            checked += 1
            verdict = verify_program(proposal.expression, world, base, max_cases=max_cases)
            if stats is not None:
                stats.verifier_calls += 1
                stats.interpreter_operations += verdict.operations
            if verdict.status == "PASS":
                return Admission(
                    "ADMITTED",
                    spec_hash,
                    canonical_hash(proposal.expression),
                    "finite-domain exhaustive witness",
                    checked,
                )
    finally:
        if stats is not None:
            stats.search_shapes += search_stats.attempted_shapes
            stats.probe_evaluations += search_stats.probe_evaluations
    return Admission(
        "UNKNOWN", spec_hash, None, "no witness within bounded search; not admitted", checked
    )


def expand_domain(world: dict, delta: int = 1) -> dict:
    """Formally specified world mutation, not a new semantic capability."""
    if type(delta) is not int or delta < 1 or delta > 16:
        raise WorldViolation("invalid mutation step")
    child = deepcopy(world)
    child["id"] = world["id"] + f".domain+{delta}"
    for symbol in ["x", "y"]:
        child["input_domain"][symbol]["min"] -= delta
        child["input_domain"][symbol]["max"] += delta
    # Preserve semantics: declared world precondition is extended only if a
    # syntactic boundary constraint exactly matches the source domain edge.
    original = world["input_domain"]

    def rewrite(tree):
        if isinstance(tree, dict):
            if len(tree) == 1:
                k, v = next(iter(tree.items()))
                if k in ("gte", "lte") and isinstance(v, list) and len(v) == 2:
                    a, b = v
                    if a in ("x", "y") and type(b) is int:
                        bound = original[a]["min"] if k == "gte" else original[a]["max"]
                        if b == bound:
                            return {k: [a, b - delta if k == "gte" else b + delta]}
            return {k: rewrite(v) for k, v in tree.items()}
        if isinstance(tree, list):
            return [rewrite(v) for v in tree]
        return tree

    child["precondition"] = rewrite(child["precondition"])
    validate_world(child)
    return child
