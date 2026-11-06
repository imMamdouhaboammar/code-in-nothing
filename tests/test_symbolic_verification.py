"""Tests for Stage S5: Unbounded Linear Integer Arithmetic (LIA) Symbolic Verification."""

from cin.synthesis.symbolic import (
    ast_to_piecewise_affine,
    verify_equivalence_symbolic,
    verify_spec_symbolic,
)

# Canonical IR programs
MAX2_IR_1 = {
    "op": "If",
    "args": [
        {"op": "LessThan", "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 1}]},
        {"op": "Arg", "index": 1},
        {"op": "Arg", "index": 0},
    ],
}

MAX2_IR_2 = {
    "op": "If",
    "args": [
        {"op": "LessThan", "args": [{"op": "Arg", "index": 1}, {"op": "Arg", "index": 0}]},
        {"op": "Arg", "index": 0},
        {"op": "Arg", "index": 1},
    ],
}

MIN2_IR = {
    "op": "If",
    "args": [
        {"op": "LessThan", "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 1}]},
        {"op": "Arg", "index": 0},
        {"op": "Arg", "index": 1},
    ],
}

ABSDIFF_IR = {
    "op": "If",
    "args": [
        {"op": "LessThan", "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 1}]},
        {"op": "Sub", "args": [{"op": "Arg", "index": 1}, {"op": "Arg", "index": 0}]},
        {"op": "Sub", "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 1}]},
    ],
}

# clamp(x, low, high) = If(low < If(x < high, x, high), If(x < high, x, high), low)
CLAMP3_IR = {
    "op": "If",
    "args": [
        {
            "op": "LessThan",
            "args": [
                {"op": "Arg", "index": 1},
                {
                    "op": "If",
                    "args": [
                        {
                            "op": "LessThan",
                            "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 2}],
                        },
                        {"op": "Arg", "index": 0},
                        {"op": "Arg", "index": 2},
                    ],
                },
            ],
        },
        {
            "op": "If",
            "args": [
                {
                    "op": "LessThan",
                    "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 2}],
                },
                {"op": "Arg", "index": 0},
                {"op": "Arg", "index": 2},
            ],
        },
        {"op": "Arg", "index": 1},
    ],
}


class TestPiecewiseAffineDecomposition:
    def test_leaf_variable_decomposition(self):
        leaf = {"op": "Arg", "index": 0}
        pieces = ast_to_piecewise_affine(leaf, arity=2)
        assert len(pieces) == 1
        reg, expr = pieces[0]
        assert expr.coeffs == (1, 0)
        assert expr.const == 0

    def test_conditional_partitions_domain(self):
        pieces = ast_to_piecewise_affine(MAX2_IR_1, arity=2)
        # Should produce two feasible pieces: x < y (returns y) and x >= y (returns x)
        assert len(pieces) == 2
        for reg, expr in pieces:
            feasible, witness = reg.is_feasible()
            assert feasible
            assert witness is not None


class TestSymbolicSpecificationProof:
    def test_max2_symbolic_proof(self):
        verdict = verify_spec_symbolic(MAX2_IR_1, spec="max2", arity=2)
        assert verdict.status == "SYMBOLIC_PROVED"
        assert verdict.feasible_regions >= 2

    def test_min2_symbolic_proof(self):
        verdict = verify_spec_symbolic(MIN2_IR, spec="min2", arity=2)
        assert verdict.status == "SYMBOLIC_PROVED"
        assert verdict.feasible_regions >= 2

    def test_absdiff_symbolic_proof(self):
        verdict = verify_spec_symbolic(ABSDIFF_IR, spec="absdiff", arity=2)
        assert verdict.status == "SYMBOLIC_PROVED"
        assert verdict.feasible_regions >= 2

    def test_clamp3_symbolic_proof(self):
        verdict = verify_spec_symbolic(CLAMP3_IR, spec="clamp3", arity=3)
        assert verdict.status == "SYMBOLIC_PROVED"
        assert verdict.feasible_regions >= 2


class TestSymbolicEquivalenceProof:
    def test_equivalent_max2_variants_prove_equal(self):
        verdict = verify_equivalence_symbolic(MAX2_IR_1, MAX2_IR_2, arity=2)
        assert verdict.status == "SYMBOLIC_PROVED"
        assert verdict.counterexample is None

    def test_non_equivalent_programs_detect_counterexample(self):
        # max2 vs min2: must fail with a counterexample where x != y
        verdict = verify_equivalence_symbolic(MAX2_IR_1, MIN2_IR, arity=2)
        assert verdict.status == "COUNTEREXAMPLE"
        assert verdict.counterexample is not None
        cx, cy = verdict.counterexample
        assert cx != cy


class TestRedGreenFalsification:
    def test_overfitted_program_caught_by_symbolic_proof(self):
        """A program that passes small checks but fails globally.

        e.g., identity on x instead of max2: returns x for all inputs.
        Passes when x >= y, but fails when x < y.
        """
        bogus_max = {"op": "Arg", "index": 0}
        verdict = verify_spec_symbolic(bogus_max, spec="max2", arity=2)
        assert verdict.status == "COUNTEREXAMPLE"
        assert verdict.counterexample is not None
        cx, cy = verdict.counterexample
        # Counterexample must exhibit cx < cy
        assert cx < cy
