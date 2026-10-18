"""External, immutable declarative contract validation."""

from __future__ import annotations

import json
import math
from copy import deepcopy
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

SCHEMAS = Path(__file__).resolve().parent / "schemas"


class ContractError(ValueError):
    pass


def _validate(value: dict, schema_name: str) -> dict:
    schema = json.loads((SCHEMAS / schema_name).read_text())
    failures = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda e: str(e.path))
    if failures:
        raise ContractError(
            "; ".join(f"{'.'.join(map(str, e.path)) or 'root'}: {e.message}" for e in failures[:3])
        )
    return value


def validate_genome(genome: dict) -> dict:
    _validate(genome, "seed-genome.v0.1.schema.json")
    weights = list(genome["genome"]["driver"]["mutation_operators"].values())
    if not math.isclose(math.fsum(weights), 1, abs_tol=1e-8):
        raise ContractError("mutation weights must sum to one")
    stop = genome["genome"]["stop_station"]
    if stop["plateau_grace_epochs"] >= stop["max_epochs"]:
        raise ContractError("plateau grace must be below max epochs")
    from .ir import IRViolation, check_tree

    try:
        check_tree(genome["genome"]["base"]["starting_expression"], genome["genome"]["base"])
    except IRViolation as exc:
        raise ContractError(str(exc)) from exc
    return deepcopy(genome)


def validate_world(world: dict) -> dict:
    version = world.get("api_version") if isinstance(world, dict) else None
    schema = "world-spec.v0.2.schema.json" if version == "cin.world/v0.2" else "world-spec.v0.1.schema.json"
    _validate(world, schema)

    def has_term(node, term):
        if isinstance(node, dict):
            return any(has_term(v, term) for v in node.values())
        if isinstance(node, list):
            return any(has_term(v, term) for v in node)
        return node == term

    if has_term(world["precondition"], "result"):
        raise ContractError("precondition must be independent of result")
    if not has_term(world["postcondition"], "result"):
        raise ContractError("postcondition must constrain result")
    domain = world["input_domain"]
    for a in ["x", "y"]:
        if domain[a]["max"] < domain[a]["min"]:
            raise ContractError("empty input domain")
    return deepcopy(world)


def _load(path: str | Path) -> dict:
    with Path(path).open(encoding="utf-8") as f:
        obj = yaml.safe_load(f)
    if not isinstance(obj, dict):
        raise ContractError("expected mapping document")
    return obj


def load_genome(path: str | Path) -> dict:
    return validate_genome(_load(path))


def load_world(path: str | Path) -> dict:
    return validate_world(_load(path))
