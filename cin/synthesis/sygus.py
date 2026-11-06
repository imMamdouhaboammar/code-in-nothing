"""Standard SyGuS (Syntax-Guided Synthesis) benchmark task definitions.

Implements official SyGuS-Comp LIA (Linear Integer Arithmetic) problems with:
- Formal relational specifications in Z3 SMT logic.
- Input arity and variable names.
- Preconditions where applicable (e.g. clamp: low <= high).
- Ground truth reference oracle functions for verification.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

try:
    import z3

    HAS_Z3 = True
except ImportError:
    z3 = None
    HAS_Z3 = False


@dataclass(frozen=True)
class SyGuSTask:
    """Formal specification of a SyGuS benchmark task."""

    name: str
    category: str  # "LIA", "PBE", "CONDITIONAL"
    arity: int
    variable_names: list[str]
    z3_spec: Callable[[list[Any], Any], Any]
    reference_oracle: Callable[..., int]
    precondition: Callable[[list[Any]], Any] | None = None
    initial_seed_cases: tuple[tuple[int, ...], ...] = ()


def _build_sygus_catalog() -> dict[str, SyGuSTask]:
    if not HAS_Z3:
        return {}

    catalog: dict[str, SyGuSTask] = {}

    # 1. max2(x, y)
    catalog["max2"] = SyGuSTask(
        name="max2",
        category="LIA",
        arity=2,
        variable_names=["x", "y"],
        z3_spec=lambda vars, res: z3.And(
            res >= vars[0],
            res >= vars[1],
            z3.Or(res == vars[0], res == vars[1]),
        ),
        reference_oracle=lambda x, y: max(x, y),
        initial_seed_cases=((0, 1), (2, -1)),
    )

    # 2. min2(x, y)
    catalog["min2"] = SyGuSTask(
        name="min2",
        category="LIA",
        arity=2,
        variable_names=["x", "y"],
        z3_spec=lambda vars, res: z3.And(
            res <= vars[0],
            res <= vars[1],
            z3.Or(res == vars[0], res == vars[1]),
        ),
        reference_oracle=lambda x, y: min(x, y),
        initial_seed_cases=((0, 1), (2, -1)),
    )

    # 3. absdiff(x, y)
    catalog["absdiff"] = SyGuSTask(
        name="absdiff",
        category="LIA",
        arity=2,
        variable_names=["x", "y"],
        z3_spec=lambda vars, res: z3.And(
            res >= 0,
            z3.Implies(vars[0] >= vars[1], res == vars[0] - vars[1]),
            z3.Implies(vars[0] < vars[1], res == vars[1] - vars[0]),
        ),
        reference_oracle=lambda x, y: abs(x - y),
        initial_seed_cases=((0, 0), (1, 3), (3, 1)),
    )

    # 4. max3(x, y, z)
    catalog["max3"] = SyGuSTask(
        name="max3",
        category="LIA",
        arity=3,
        variable_names=["x", "y", "z"],
        z3_spec=lambda vars, res: z3.And(
            res >= vars[0],
            res >= vars[1],
            res >= vars[2],
            z3.Or(res == vars[0], res == vars[1], res == vars[2]),
        ),
        reference_oracle=lambda x, y, z: max(x, y, z),
        initial_seed_cases=((1, 2, 3), (3, 2, 1), (2, 3, 1)),
    )

    # 5. min3(x, y, z)
    catalog["min3"] = SyGuSTask(
        name="min3",
        category="LIA",
        arity=3,
        variable_names=["x", "y", "z"],
        z3_spec=lambda vars, res: z3.And(
            res <= vars[0],
            res <= vars[1],
            res <= vars[2],
            z3.Or(res == vars[0], res == vars[1], res == vars[2]),
        ),
        reference_oracle=lambda x, y, z: min(x, y, z),
        initial_seed_cases=((1, 2, 3), (3, 2, 1), (2, 3, 1)),
    )

    # 6. clamp3(x, low, high)
    catalog["clamp3"] = SyGuSTask(
        name="clamp3",
        category="LIA",
        arity=3,
        variable_names=["x", "low", "high"],
        precondition=lambda vars: vars[1] <= vars[2],  # low <= high
        z3_spec=lambda vars, res: z3.And(
            z3.Implies(vars[0] < vars[1], res == vars[1]),
            z3.Implies(vars[0] > vars[2], res == vars[2]),
            z3.Implies(z3.And(vars[0] >= vars[1], vars[0] <= vars[2]), res == vars[0]),
        ),
        reference_oracle=lambda x, low, high: max(low, min(x, high)),
        initial_seed_cases=((0, -1, 1), (-2, -1, 1), (2, -1, 1)),
    )

    # 7. median3(x, y, z)
    catalog["median3"] = SyGuSTask(
        name="median3",
        category="LIA",
        arity=3,
        variable_names=["x", "y", "z"],
        z3_spec=lambda vars, res: z3.And(
            z3.Or(res == vars[0], res == vars[1], res == vars[2]),
            res
            >= z3.If(
                vars[0] < vars[1],
                z3.If(vars[0] < vars[2], vars[0], vars[2]),
                z3.If(vars[1] < vars[2], vars[1], vars[2]),
            ),
            res
            <= z3.If(
                vars[0] > vars[1],
                z3.If(vars[0] > vars[2], vars[0], vars[2]),
                z3.If(vars[1] > vars[2], vars[1], vars[2]),
            ),
        ),
        reference_oracle=lambda x, y, z: sorted([x, y, z])[1],
        initial_seed_cases=((1, 2, 3), (3, 1, 2), (2, 3, 1)),
    )

    # 8. max4(x, y, z, w)
    catalog["max4"] = SyGuSTask(
        name="max4",
        category="LIA",
        arity=4,
        variable_names=["x", "y", "z", "w"],
        z3_spec=lambda vars, res: z3.And(
            res >= vars[0],
            res >= vars[1],
            res >= vars[2],
            res >= vars[3],
            z3.Or(res == vars[0], res == vars[1], res == vars[2], res == vars[3]),
        ),
        reference_oracle=lambda x, y, z, w: max(x, y, z, w),
        initial_seed_cases=((1, 2, 3, 4), (4, 3, 2, 1)),
    )

    return catalog


SYGUS_BENCHMARKS = _build_sygus_catalog()


def get_sygus_task(name: str) -> SyGuSTask:
    if not HAS_Z3:
        raise RuntimeError("z3-solver required for SyGuS benchmarks")
    if name not in SYGUS_BENCHMARKS:
        raise KeyError(f"Unknown SyGuS task: {name}. Available: {list(SYGUS_BENCHMARKS.keys())}")
    return SYGUS_BENCHMARKS[name]
