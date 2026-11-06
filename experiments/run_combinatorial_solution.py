"""End-to-End Experimental Demonstration: Bounded CIN Synthesis Components.

Demonstrates:
  - Stage S1: Information-Theoretic Branch Decoupling (ID3 predicate selection)
  - Stage S2: Relational Deductive Inverse Constraints & Bound Pruning
  - Stage S3: Multi-Input Verification (Arities 1..8) & World DSL v0.3
  - Stage S4: Hereditary Abstraction Engine (Anti-unification, MDL, Macro Desugaring)
  - Stage S5: Unbounded Linear Integer Arithmetic (LIA) Symbolic Verification Proofs
"""

from __future__ import annotations

import time

from cin.contracts import load_world
from cin.ir import canonical_hash
from cin.synthesis import (
    Interval,
    Macro,
    MacroRegistry,
    deduce_inverse_obligations,
    extract_reusable_abstractions,
    soundly_prunes_binary_op,
    synthesize_conditional_tree,
    verify_spec_symbolic,
)
from cin.worlds import verify_program

BASE_2D = {
    "cin_ir_version": "0.1",
    "organism_class": "experiment",
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
    "organism_class": "experiment",
    "input_types": ["Int", "Int", "Int"],
    "return_type": "Int",
    "starting_expression": {"op": "Arg", "index": 0},
    "allowed_primitives": ["Arg", "ConstInt", "Add", "Sub", "LessThan", "Equal", "If"],
    "allowed_constants": [0, 1],
    "max_ast_depth": 7,
    "max_ast_nodes": 25,
    "invariants": ["typed", "pure", "deterministic", "resource_bounded"],
}


def main():
    print("================================================================================")
    print("CODE-IN-NOTHING: BOUNDED SYNTHESIS EXPERIMENT")
    print("================================================================================\n")

    # --------------------------------------------------------------------------
    # STAGE S1: Information-Theoretic Branch Decoupling (absdiff benchmark)
    # --------------------------------------------------------------------------
    print("=== [Stage S1] Information-Theoretic Conditional Synthesis on absdiff ===")
    cases_2d = tuple((x, y) for x in range(-2, 3) for y in range(-2, 3))
    target_absdiff = tuple(abs(x - y) for x, y in cases_2d)

    t0 = time.perf_counter()
    res_absdiff = synthesize_conditional_tree(cases_2d, target_absdiff, BASE_2D)
    t_absdiff = time.perf_counter() - t0

    if res_absdiff is None:
        print("  Result          : FAILED (no expression found within the search budget)")
    else:
        print(f"  Synthesized AST : {res_absdiff.expression}")
        print(
            f"  Search Shapes   : {res_absdiff.shapes_attempted} (excludes candidate generation work)"
        )
    print(f"  Synthesis Time  : {t_absdiff * 1000:.2f} ms\n")

    # --------------------------------------------------------------------------
    # STAGE S2: Relational Inverse Constraints & Deductive Bound Pruning
    # --------------------------------------------------------------------------
    print("=== [Stage S2] Relational Inverse Deductive Pruning ===")
    target_set = {10, 15}
    target_int = Interval(min(target_set), max(target_set))
    left_int = Interval(0, 5)
    right_int = Interval(-10, -5)
    prune_add = soundly_prunes_binary_op("Add", left_int, right_int, target_int)
    inv_req = deduce_inverse_obligations("Sub", left_val=5, admissible_targets=target_set)

    print(f"  Target Set              : {target_set}")
    print(f"  Left Interval           : {left_int}")
    print(f"  Right Interval          : {right_int}")
    print(f"  Add op Soundly Pruned   : {prune_add} (Add cannot reach {target_set})")
    print(f"  Sub required right vals : {inv_req} for left_val=5\n")

    # --------------------------------------------------------------------------
    # STAGE S3 & S4: Multi-Input Worlds & Hereditary Macro Abstraction
    # --------------------------------------------------------------------------
    print("=== [Stage S3 & S4] Multi-Input Clamp3 & Hereditary Macro Learning ===")
    max2_ir = {
        "op": "If",
        "args": [
            {"op": "LessThan", "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 1}]},
            {"op": "Arg", "index": 1},
            {"op": "Arg", "index": 0},
        ],
    }
    min2_ir = {
        "op": "If",
        "args": [
            {"op": "LessThan", "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 1}]},
            {"op": "Arg", "index": 0},
            {"op": "Arg", "index": 1},
        ],
    }

    # Discover abstractions
    discovered = extract_reusable_abstractions([max2_ir, min2_ir], min_occurrences=2, min_nodes=3)
    print(f"  Anti-Unification Extracted: {len(discovered)} reusable macro(s)")

    registry = MacroRegistry()
    registry.register(Macro("max2", 2, max2_ir, canonical_hash(max2_ir)))
    registry.register(Macro("min2", 2, min2_ir, canonical_hash(min2_ir)))

    world_clamp = load_world("examples/world-clamp3.v0.3.yaml")
    cases_clamp = (
        (-2, -1, 1),
        (0, -1, 1),
        (2, -1, 1),
        (-3, 0, 2),
        (1, 0, 2),
        (5, 0, 2),
    )

    t0 = time.perf_counter()
    res_clamp = synthesize_conditional_tree(
        cases_clamp, world_clamp, BASE_3D, macro_registry=registry
    )
    t_clamp = time.perf_counter() - t0

    if res_clamp is None:
        print("  Clamp3 Synthesis         : FAILED (no expression found within the search budget)")
    else:
        print(f"  Clamp3 Synthesized AST  : {res_clamp.expression}")
        print(f"  AST Nodes / Depth       : {res_clamp.nodes} nodes, depth {res_clamp.depth}")
        print(
            f"  Search Shapes           : {res_clamp.shapes_attempted} (excludes generation work)"
        )
        verdict_clamp = verify_program(res_clamp.expression, world_clamp, BASE_3D)
        print(
            f"  Independent World Check : {verdict_clamp.status} on {verdict_clamp.checked} cases"
        )
    print(f"  Clamp3 Synthesis Time   : {t_clamp * 1000:.2f} ms")
    print("  Macro Transfer Utility  : NOT MEASURED (no matched baseline)\n")

    # --------------------------------------------------------------------------
    # STAGE S5: Unbounded Linear Integer Arithmetic (LIA) Symbolic Verification
    # --------------------------------------------------------------------------
    print("=== [Stage S5] Unbounded Linear Integer Arithmetic (LIA) Symbolic Proof ===")
    v_max2 = verify_spec_symbolic(max2_ir, spec="max2", arity=2)
    v_abs = (
        verify_spec_symbolic(res_absdiff.expression, spec="absdiff", arity=2)
        if res_absdiff is not None
        else None
    )
    v_cl = (
        verify_spec_symbolic(res_clamp.expression, spec="clamp3", arity=3)
        if res_clamp is not None
        else None
    )

    print(
        f"  max2 Formal Proof   : {v_max2.status} ({v_max2.proof_scope}, {v_max2.feasible_regions} regions)"
    )
    print(f"  absdiff Formal Proof: {v_abs.status if v_abs is not None else 'NOT_RUN'}")
    print(f"  clamp3 Formal Proof : {v_cl.status if v_cl is not None else 'NOT_RUN'}")

    # Test counterexample detection on flawed candidate
    flawed_max = {"op": "Arg", "index": 0}
    v_flawed = verify_spec_symbolic(flawed_max, spec="max2", arity=2)
    print(
        f"  Flawed Candidate    : {v_flawed.status} (Counterexample caught: {v_flawed.counterexample})"
    )
    print(f"  Explanation         : {v_flawed.explanation}\n")

    print("================================================================================")
    verified = (
        res_absdiff is not None
        and res_clamp is not None
        and verdict_clamp is not None
        and verdict_clamp.status == "PASS"
        and all(
            verdict is not None and verdict.status == "SYMBOLIC_PROVED"
            for verdict in (v_max2, v_abs, v_cl)
        )
    )
    print(
        f"EXPERIMENT STATUS: {'ALL RECORDED CHECKS PASSED' if verified else 'INCOMPLETE OR FAILED'}"
    )
    print("================================================================================")


if __name__ == "__main__":
    main()
