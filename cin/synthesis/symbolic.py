"""Symbolic verification and proof engine for Linear Integer Arithmetic (LIA).

Provides:
- Exact piecewise affine decomposition of CIN-IR ASTs.
- Exact integer polyhedral region satisfiability using an optional Z3 SMT solver.
- Conditional unbounded equivalence proofs over Z^k when Z3 returns UNSAT.
- Relational specification proof for canonical capabilities: max2, min2, absdiff, clamp3, median3.
- Distinction between FINITE_EXHAUSTIVE vs SYMBOLIC_PROVED vs UNKNOWN.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

PROOF_SCOPE_LIA = "cin.verifier/symbolic-lia-v0.1"


@dataclass(frozen=True)
class AffineExpr:
    """Affine integer expression: sum(coeffs[i] * x_i) + const."""

    coeffs: tuple[int, ...]
    const: int

    @classmethod
    def variable(cls, index: int, arity: int) -> AffineExpr:
        c = [0] * arity
        c[index] = 1
        return cls(tuple(c), 0)

    @classmethod
    def constant(cls, val: int, arity: int) -> AffineExpr:
        return cls(tuple([0] * arity), val)

    def eval(self, pt: tuple[int, ...]) -> int:
        return sum(c * x for c, x in zip(self.coeffs, pt)) + self.const

    def add(self, other: AffineExpr) -> AffineExpr:
        return AffineExpr(
            tuple(c1 + c2 for c1, c2 in zip(self.coeffs, other.coeffs)),
            self.const + other.const,
        )

    def sub(self, other: AffineExpr) -> AffineExpr:
        return AffineExpr(
            tuple(c1 - c2 for c1, c2 in zip(self.coeffs, other.coeffs)),
            self.const - other.const,
        )

    def neg(self) -> AffineExpr:
        return AffineExpr(tuple(-c for c in self.coeffs), -self.const)

    def is_zero(self) -> bool:
        return self.const == 0 and all(c == 0 for c in self.coeffs)

    def is_constant(self) -> bool:
        return all(c == 0 for c in self.coeffs)


@dataclass(frozen=True)
class LinearInequality:
    """Linear inequality: sum(coeffs[i] * x_i) + const <= 0."""

    coeffs: tuple[int, ...]
    const: int

    def eval(self, pt: tuple[int, ...]) -> int:
        return sum(c * x for c, x in zip(self.coeffs, pt)) + self.const

    def is_satisfied(self, pt: tuple[int, ...]) -> bool:
        return self.eval(pt) <= 0

    def is_trivial_true(self) -> bool:
        return all(c == 0 for c in self.coeffs) and self.const <= 0

    def is_trivial_false(self) -> bool:
        return all(c == 0 for c in self.coeffs) and self.const > 0

    def simplified(self) -> LinearInequality:
        """Divide through by gcd of coefficients if possible."""
        nz = [abs(c) for c in self.coeffs if c != 0]
        if not nz:
            return self
        g = math.gcd(*nz)
        if g > 1:
            # sum(c/g * x) <= floor(-const / g) => sum(c/g * x) - floor(-const / g) <= 0
            new_coeffs = tuple(c // g for c in self.coeffs)
            new_const = -((-self.const) // g)
            return LinearInequality(new_coeffs, new_const)
        return self


@dataclass
class PolyhedralRegion:
    """Conjunction of linear inequalities defining a region in Z^k."""

    arity: int
    constraints: list[LinearInequality] = field(default_factory=list)

    def add_constraint(self, ineq: LinearInequality) -> PolyhedralRegion:
        simp = ineq.simplified()
        if simp.is_trivial_true():
            return self
        return PolyhedralRegion(self.arity, self.constraints + [simp])

    def is_feasible(self) -> tuple[bool, tuple[int, ...] | None]:
        """Decide integer feasibility exactly using the optional Z3 solver.

        A bounded witness search cannot certify infeasibility over unbounded integers.
        Unavailable or inconclusive solver work raises instead of returning False.
        """
        from . import z3_verifier

        if not z3_verifier.HAS_Z3:
            raise RuntimeError("Exact integer feasibility requires z3-solver")

        vars_ = [z3_verifier.z3.Int(f"region_{i}") for i in range(self.arity)]
        solver = z3_verifier.z3.Solver()
        solver.set("timeout", 5000)
        for c in self.constraints:
            if len(c.coeffs) != self.arity:
                raise ValueError("Constraint arity does not match region arity")
            lhs = z3_verifier.z3.Sum(
                [coefficient * variable for coefficient, variable in zip(c.coeffs, vars_)]
            )
            solver.add(lhs + c.const <= 0)

        result = solver.check()
        if result == z3_verifier.z3.unsat:
            return False, None
        if result == z3_verifier.z3.sat:
            model = solver.model()
            witness = tuple(
                model.eval(variable, model_completion=True).as_long() for variable in vars_
            )
            return True, witness
        raise RuntimeError(f"Exact integer feasibility inconclusive: {solver.reason_unknown()}")


def ast_to_piecewise_affine(node: dict, arity: int) -> list[tuple[PolyhedralRegion, AffineExpr]]:
    """Decomposes a CIN-IR AST into a set of (PolyhedralRegion, AffineExpr) pieces."""
    op = node.get("op")

    if op == "Arg":
        idx = node["index"]
        return [(PolyhedralRegion(arity), AffineExpr.variable(idx, arity))]

    if op == "ConstInt":
        val = node["value"]
        return [(PolyhedralRegion(arity), AffineExpr.constant(val, arity))]

    if op in ("Add", "Sub"):
        left_pieces = ast_to_piecewise_affine(node["args"][0], arity)
        right_pieces = ast_to_piecewise_affine(node["args"][1], arity)
        combined = []
        for r1, e1 in left_pieces:
            for r2, e2 in right_pieces:
                new_constraints = r1.constraints + r2.constraints
                new_reg = PolyhedralRegion(arity, new_constraints)
                feasible, _ = new_reg.is_feasible()
                if feasible:
                    new_expr = e1.add(e2) if op == "Add" else e1.sub(e2)
                    combined.append((new_reg, new_expr))
        return combined

    if op == "If":
        cond = node["args"][0]
        then_node = node["args"][1]
        else_node = node["args"][2]

        cond_op = cond.get("op")
        if cond_op not in ("LessThan", "Equal"):
            raise ValueError(f"Unsupported conditional op: {cond_op}")

        left_expr = ast_to_piecewise_affine(cond["args"][0], arity)
        right_expr = ast_to_piecewise_affine(cond["args"][1], arity)

        pieces: list[tuple[PolyhedralRegion, AffineExpr]] = []

        for r_l, e_l in left_expr:
            for r_r, e_r in right_expr:
                base_constraints = r_l.constraints + r_r.constraints
                diff = e_l.sub(e_r)  # e_l - e_r

                if cond_op == "LessThan":
                    # True branch: e_l < e_r <=> e_l - e_r + 1 <= 0
                    true_ineq = LinearInequality(diff.coeffs, diff.const + 1)
                    # False branch: e_l >= e_r <=> e_r - e_l <= 0 <=> -(e_l - e_r) <= 0
                    false_ineq = LinearInequality(tuple(-c for c in diff.coeffs), -diff.const)

                    reg_true = PolyhedralRegion(arity, base_constraints + [true_ineq])
                    if reg_true.is_feasible()[0]:
                        for r_then, e_then in ast_to_piecewise_affine(then_node, arity):
                            r_comb = PolyhedralRegion(
                                arity, reg_true.constraints + r_then.constraints
                            )
                            if r_comb.is_feasible()[0]:
                                pieces.append((r_comb, e_then))

                    reg_false = PolyhedralRegion(arity, base_constraints + [false_ineq])
                    if reg_false.is_feasible()[0]:
                        for r_else, e_else in ast_to_piecewise_affine(else_node, arity):
                            r_comb = PolyhedralRegion(
                                arity, reg_false.constraints + r_else.constraints
                            )
                            if r_comb.is_feasible()[0]:
                                pieces.append((r_comb, e_else))

                elif cond_op == "Equal":
                    # True branch: diff == 0 <=> diff <= 0 and -diff <= 0
                    eq_true1 = LinearInequality(diff.coeffs, diff.const)
                    eq_true2 = LinearInequality(tuple(-c for c in diff.coeffs), -diff.const)
                    reg_true = PolyhedralRegion(arity, base_constraints + [eq_true1, eq_true2])
                    if reg_true.is_feasible()[0]:
                        for r_then, e_then in ast_to_piecewise_affine(then_node, arity):
                            r_comb = PolyhedralRegion(
                                arity, reg_true.constraints + r_then.constraints
                            )
                            if r_comb.is_feasible()[0]:
                                pieces.append((r_comb, e_then))

                    # False branch: diff != 0 <=> diff < 0 or diff > 0
                    # Split into diff + 1 <= 0 and -diff + 1 <= 0
                    f1 = LinearInequality(diff.coeffs, diff.const + 1)
                    f2 = LinearInequality(tuple(-c for c in diff.coeffs), -diff.const + 1)
                    for ineq in (f1, f2):
                        reg_false = PolyhedralRegion(arity, base_constraints + [ineq])
                        if reg_false.is_feasible()[0]:
                            for r_else, e_else in ast_to_piecewise_affine(else_node, arity):
                                r_comb = PolyhedralRegion(
                                    arity, reg_false.constraints + r_else.constraints
                                )
                                if r_comb.is_feasible()[0]:
                                    pieces.append((r_comb, e_else))

        return pieces

    raise ValueError(f"Unsupported AST node in symbolic verification: {op}")


@dataclass(frozen=True)
class SymbolicVerdict:
    """Formal mathematical verification verdict over unbounded Z^k."""

    status: str  # "SYMBOLIC_PROVED", "COUNTEREXAMPLE", "UNKNOWN"
    proof_scope: str
    feasible_regions: int
    counterexample: tuple[int, ...] | None = None
    explanation: str = ""

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "proof_scope": self.proof_scope,
            "feasible_regions": self.feasible_regions,
            "counterexample": self.counterexample,
            "explanation": self.explanation,
        }


def verify_equivalence_symbolic(prog1: dict, prog2: dict, arity: int) -> SymbolicVerdict:
    """Decide universal CIN-IR equivalence over unbounded integers with Z3.

    A solver timeout or missing optional dependency is UNKNOWN, never a proof.
    """
    from .z3_verifier import verify_equivalence_with_z3

    verdict = verify_equivalence_with_z3(prog1, prog2, arity)
    return SymbolicVerdict(
        status=verdict.status,
        proof_scope=verdict.proof_scope,
        feasible_regions=0,
        counterexample=verdict.counterexample,
        explanation=verdict.explanation,
    )


def verify_spec_symbolic(program: dict, spec: str, arity: int) -> SymbolicVerdict:
    """Verify a supported relational specification on all applicable Z^k inputs."""
    from . import z3_verifier

    supported_arity = {
        "max2": 2,
        "min2": 2,
        "absdiff": 2,
        "clamp3": 3,
        "median3": 3,
    }
    if spec not in supported_arity:
        return SymbolicVerdict(
            status="UNKNOWN",
            proof_scope=z3_verifier.PROOF_SCOPE_Z3,
            feasible_regions=0,
            explanation=f"Unknown specification: {spec}",
        )
    if arity != supported_arity[spec]:
        raise ValueError(f"{spec} requires arity {supported_arity[spec]}")
    if not z3_verifier.HAS_Z3:
        return SymbolicVerdict(
            status="UNKNOWN",
            proof_scope=z3_verifier.PROOF_SCOPE_Z3,
            feasible_regions=0,
            explanation="Exact unbounded verification requires optional z3-solver",
        )

    z3 = z3_verifier.z3

    def postcondition(v: list, output: object) -> object:
        if spec == "max2":
            return output == z3.If(v[0] >= v[1], v[0], v[1])
        if spec == "min2":
            return output == z3.If(v[0] <= v[1], v[0], v[1])
        if spec == "absdiff":
            return output == z3.If(v[0] >= v[1], v[0] - v[1], v[1] - v[0])
        if spec == "clamp3":
            return output == z3.If(
                v[0] < v[1],
                v[1],
                z3.If(v[0] > v[2], v[2], v[0]),
            )

        # Median of three integers, including equal-value and permutation cases.
        x, y, z = v
        middle = z3.If(
            x <= y,
            z3.If(y <= z, y, z3.If(x <= z, z, x)),
            z3.If(x <= z, x, z3.If(y <= z, z, y)),
        )
        return output == middle

    precondition = (lambda v: v[1] <= v[2]) if spec == "clamp3" else None
    verdict = z3_verifier.verify_spec_with_z3(
        program,
        postcondition,
        arity,
        precondition=precondition,
    )

    # This count is diagnostic only. Z3's unsatisfiability result is the proof.
    feasible_regions = 0
    if verdict.status != "UNKNOWN":
        try:
            feasible_regions = len(ast_to_piecewise_affine(program, arity))
        except (RuntimeError, ValueError, KeyError, IndexError):
            pass

    return SymbolicVerdict(
        status=verdict.status,
        proof_scope=verdict.proof_scope,
        feasible_regions=feasible_regions,
        counterexample=verdict.counterexample,
        explanation=verdict.explanation,
    )
