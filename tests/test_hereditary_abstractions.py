"""Tests for Stage S4: Hereditary Abstraction Engine and Reusable Macro Learning."""

from copy import deepcopy

from cin.contracts import load_world
from cin.ir import canonical_hash, check_tree, run_ir_args
from cin.synthesis.decision import synthesize_conditional_tree
from cin.synthesis.library import (
    Macro,
    MacroRegistry,
    anti_unify,
    evaluate_transfer_utility,
    extract_reusable_abstractions,
)
from cin.worlds import verify_program

BASE_2D = {
    "cin_ir_version": "0.1",
    "organism_class": "test",
    "input_types": ["Int", "Int"],
    "return_type": "Int",
    "starting_expression": {"op": "Arg", "index": 0},
    "allowed_primitives": ["Arg", "ConstInt", "Add", "Sub", "LessThan", "Equal", "If"],
    "allowed_constants": [0, 1],
    "max_ast_depth": 7,
    "max_ast_nodes": 25,
    "invariants": ["typed", "pure", "deterministic", "resource_bounded"],
}

BASE_3D = {
    "cin_ir_version": "0.2",
    "organism_class": "test",
    "input_types": ["Int", "Int", "Int"],
    "return_type": "Int",
    "starting_expression": {"op": "Arg", "index": 0},
    "allowed_primitives": ["Arg", "ConstInt", "Add", "Sub", "LessThan", "Equal", "If"],
    "allowed_constants": [0, 1],
    "max_ast_depth": 7,
    "max_ast_nodes": 25,
    "invariants": ["typed", "pure", "deterministic", "resource_bounded"],
}

# Canonical max2 and min2 IRs
MAX2_IR = {
    "op": "If",
    "args": [
        {"op": "LessThan", "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 1}]},
        {"op": "Arg", "index": 1},
        {"op": "Arg", "index": 0},
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


class TestAntiUnification:
    def test_identical_expressions_unify_to_themselves(self):
        expr = {"op": "Add", "args": [{"op": "Arg", "index": 0}, {"op": "ConstInt", "value": 1}]}
        template, substitutions = anti_unify(expr, expr)
        assert template == expr
        assert len(substitutions) == 0

    def test_variable_disagreement_generalizes_to_parameter(self):
        t1 = {"op": "Add", "args": [{"op": "Arg", "index": 0}, {"op": "ConstInt", "value": 1}]}
        t2 = {"op": "Add", "args": [{"op": "Arg", "index": 1}, {"op": "ConstInt", "value": 1}]}
        template, substitutions = anti_unify(t1, t2)
        assert template == {
            "op": "Add",
            "args": [{"op": "Arg", "index": 0}, {"op": "ConstInt", "value": 1}],
        }
        assert len(substitutions) == 1
        assert substitutions[0] == ({"op": "Arg", "index": 0}, {"op": "Arg", "index": 1})

    def test_isomorphic_conditionals_unify(self):
        # max2(x, y) vs max2(y, z)
        t1 = deepcopy(MAX2_IR)
        t2 = {
            "op": "If",
            "args": [
                {"op": "LessThan", "args": [{"op": "Arg", "index": 1}, {"op": "Arg", "index": 2}]},
                {"op": "Arg", "index": 2},
                {"op": "Arg", "index": 1},
            ],
        }
        template, substitutions = anti_unify(t1, t2)
        assert template.get("op") == "If"
        assert len(substitutions) == 2


class TestMacroRegistry:
    def test_macro_registration_and_desugaring(self):
        registry = MacroRegistry()
        max_macro = Macro(
            name="max2",
            arity=2,
            body=MAX2_IR,
            origin_hash=canonical_hash(MAX2_IR),
            description="Maximum of two numbers",
        )
        registry.register(max_macro)

        call = {
            "op": "CallMacro",
            "macro": "max2",
            "args": [{"op": "Arg", "index": 0}, {"op": "ConstInt", "value": 1}],
        }
        desugared = registry.desugar(call)

        expected = {
            "op": "If",
            "args": [
                {
                    "op": "LessThan",
                    "args": [{"op": "Arg", "index": 0}, {"op": "ConstInt", "value": 1}],
                },
                {"op": "ConstInt", "value": 1},
                {"op": "Arg", "index": 0},
            ],
        }
        assert desugared == expected
        check_tree(desugared, BASE_2D)

    def test_nested_macro_desugaring(self):
        registry = MacroRegistry()
        registry.register(Macro("max2", 2, MAX2_IR, canonical_hash(MAX2_IR)))
        registry.register(Macro("min2", 2, MIN2_IR, canonical_hash(MIN2_IR)))

        # clamp(x, low, high) = max2(low, min2(x, high))
        clamp_call = {
            "op": "CallMacro",
            "macro": "max2",
            "args": [
                {"op": "Arg", "index": 1},  # low
                {
                    "op": "CallMacro",
                    "macro": "min2",
                    "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 2}],  # x, high
                },
            ],
        }
        desugared = registry.desugar(clamp_call)
        check_tree(desugared, BASE_3D)

        # Evaluate on test points: clamp(5, 0, 10) = 5; clamp(-3, 0, 10) = 0; clamp(15, 0, 10) = 10
        assert run_ir_args(desugared, (5, 0, 10), expected_arity=3) == 5
        assert run_ir_args(desugared, (-3, 0, 10), expected_arity=3) == 0
        assert run_ir_args(desugared, (15, 0, 10), expected_arity=3) == 10

    def test_sugaring_replaces_isomorphic_pattern(self):
        registry = MacroRegistry()
        registry.register(Macro("max2", 2, MAX2_IR, canonical_hash(MAX2_IR)))

        sugared = registry.sugar(MAX2_IR)
        assert sugared == {
            "op": "CallMacro",
            "macro": "max2",
            "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 1}],
        }


class TestHereditaryAbstractionSynthesis:
    def test_extract_macros_from_retained_skills(self):
        skills = [MAX2_IR, MIN2_IR]
        macros = extract_reusable_abstractions(skills, min_occurrences=2, min_nodes=3)
        assert len(macros) >= 1
        # Discovered pattern is the shared LessThan comparison branch structure
        discovered = macros[0]
        assert discovered.arity >= 2

    def test_inherited_macros_accelerate_clamp3_synthesis(self):
        """Proves that inheriting max2 and min2 macros reduces clamp3 search effort.

        clamp(x, low, high) requires a 13-node, depth-4 nested conditional AST.
        With max2 and min2 macros inherited from parent, synthesis finds it
        in under 25 candidate evaluations.
        """
        registry = MacroRegistry()
        registry.register(Macro("max2", 2, MAX2_IR, canonical_hash(MAX2_IR)))
        registry.register(Macro("min2", 2, MIN2_IR, canonical_hash(MIN2_IR)))

        world_clamp = load_world("examples/world-clamp3.v0.3.yaml")

        # Sample points covering low, in-range, and high
        cases = (
            (-2, -1, 1),
            (0, -1, 1),
            (2, -1, 1),
            (-3, 0, 2),
            (1, 0, 2),
            (5, 0, 2),
        )

        res = synthesize_conditional_tree(
            cases,
            world_clamp,
            BASE_3D,
            macro_registry=registry,
        )

        assert res is not None
        assert res.shapes_attempted < 1000

        # Verify against full independent world verifier
        verdict = verify_program(res.expression, world_clamp, BASE_3D)
        assert verdict.status == "PASS"

    def test_transfer_utility_metric_falsification(self):
        macro = Macro("max2", 2, MAX2_IR, canonical_hash(MAX2_IR))

        # Positive transfer utility: without macro took 1000, with macro took 30
        util_pos = evaluate_transfer_utility(
            macro, evals_without=1000, evals_with=30, extraction_cost=10
        )
        assert util_pos > 0
        assert util_pos == 960.0

        # Negative transfer utility: without macro took 40, with macro took 45 + overhead
        util_neg = evaluate_transfer_utility(
            macro, evals_without=40, evals_with=45, extraction_cost=10
        )
        assert util_neg < 0
