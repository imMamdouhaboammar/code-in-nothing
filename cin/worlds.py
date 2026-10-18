"""Formal-world DSL, strict world admission, exhaustive finite-domain checks.

Witness synthesis occurs inside admission and only a witness digest is returned.
This does not establish universal validity outside the declared finite domain.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from itertools import product

from .contracts import ContractError, validate_world
from .ir import IRViolation, Limits, canonical_hash, check_tree, run_ir
from .search import candidate_stream


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


def _term(v, values):
    if type(v) is int:
        return v
    if v in ("x", "y", "result"):
        return values[v]
    raise WorldViolation("unrecognized term")


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
    x = domain["x"]
    y = domain["y"]
    count = (x["max"] - x["min"] + 1) * (y["max"] - y["min"] + 1)
    if count > max_cases:
        raise WorldViolation("domain exceeds exhaustive budget")
    if count < 1:
        raise WorldViolation("empty domain")
    for pair in product(range(x["min"], x["max"] + 1), range(y["min"], y["max"] + 1)):
        yield pair


def verify_program(
    program: dict, world: dict, base: dict, limits: Limits = Limits(), max_cases: int = 4096
) -> Verdict:
    try:
        validate_world(world)
        check_tree(program, base)
        points = list(_inputs(world, max_cases))
    except (ContractError, IRViolation, WorldViolation) as exc:
        return Verdict("INVALID", 0, reason=str(exc))
    checked = 0
    ops = [0]
    for x, y in points:
        values = {"x": x, "y": y, "result": 0}
        if not check_formula(world["precondition"], values):
            continue
        checked += 1
        try:
            values["result"] = run_ir(program, x, y, limits, ops_counter=ops)
        except IRViolation as exc:
            return Verdict("UNKNOWN", checked, (x, y), str(exc), ops[0])
        if not check_formula(world["postcondition"], values):
            return Verdict("FAIL", checked, (x, y), "postcondition counterexample", ops[0])
    if checked == 0:
        return Verdict("INVALID", 0, reason="vacuous precondition")
    return Verdict("PASS", checked, operations=ops[0])


def admit_world(
    world: dict, base: dict, max_proposals: int = 1000, max_cases: int = 4096
) -> Admission:
    spec_hash = canonical_hash(world)
    try:
        validate_world(world)
        points = list(_inputs(world, max_cases))
        if not any(
            check_formula(world["precondition"], {"x": x, "y": y, "result": 0}) for x, y in points
        ):
            return Admission("REJECTED", spec_hash, None, "vacuous precondition", 0)
    except (ContractError, WorldViolation) as exc:
        return Admission("REJECTED", spec_hash, None, str(exc), 0)
    checked = 0
    # The verifier-private witness is never an argument to candidate_stream.
    for proposal in candidate_stream(
        {"op": "Arg", "index": 0}, base, seed=0, max_proposals=max_proposals
    ):
        checked += 1
        verdict = verify_program(proposal.expression, world, base, max_cases=max_cases)
        if verdict.status == "PASS":
            return Admission(
                "ADMITTED",
                spec_hash,
                canonical_hash(proposal.expression),
                "finite-domain exhaustive witness",
                checked,
            )
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
