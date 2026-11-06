"""Neuro-Symbolic Intuitive Guidance and Generational Tool Inheritance.

Integrates:
- Probabilistic guidance / LLM intuition layer to propose high-level AST sketches
  and select composed abstractions from the inherited MacroRegistry.
- The CIN + Z3 formal guardian to mathematically verify proposed sketches.
- Generational inheritance of proved functions as guaranteed agent tools.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from ..ir import canonical_hash
from .cegis import CEGISResult, run_cegis_loop
from .library import Macro, MacroRegistry
from .sygus import SyGuSTask
from .z3_verifier import Z3Verdict, verify_spec_with_z3


@dataclass
class GuidanceVerdict:
    """Outcome of an intuitive guidance proposal verified by the formal guardian."""

    task_name: str
    status: str  # "SYMBOLIC_PROVED", "COUNTEREXAMPLE", "FAILED"
    expression: dict | None
    provenance: str  # "intuitive_sketch", "cegis_synthesis", "direct_proof"
    z3_verdict: Z3Verdict | None = None
    macro_promoted: Macro | None = None
    elapsed_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_name": self.task_name,
            "status": self.status,
            "expression": self.expression,
            "provenance": self.provenance,
            "z3_verdict": self.z3_verdict.to_dict() if self.z3_verdict else None,
            "macro_promoted": self.macro_promoted.to_dict() if self.macro_promoted else None,
            "elapsed_ms": self.elapsed_ms,
        }


class NeuroSymbolicAgentKernel:
    """Agentic kernel combining an intuitive proposal guide with an SMT formal verifier."""

    def __init__(self, registry: MacroRegistry | None = None):
        self.registry = registry or MacroRegistry()
        self.verified_tools: dict[str, dict] = {}
        self.lineage_log: list[dict[str, Any]] = []

    def register_verified_tool(
        self, name: str, arity: int, expression: dict, proof_scope: str
    ) -> Macro:
        """Promotes a mathematically verified expression into a durable hereditary macro tool."""
        macro = Macro(
            name=name,
            arity=arity,
            body=expression,
            origin_hash=canonical_hash(expression),
            description=f"Formally verified by {proof_scope}",
            metadata={"status": "SYMBOLIC_PROVED", "promoted_at": time.time()},
        )
        self.registry.register(macro)
        self.verified_tools[name] = expression
        self.lineage_log.append(
            {
                "event": "TOOL_INHERITED",
                "tool_name": name,
                "arity": arity,
                "expression_hash": macro.origin_hash,
            }
        )
        return macro

    def propose_intuitive_sketches(self, task: SyGuSTask) -> list[dict]:
        """Generates high-level structural sketches and macro compositions.

        Emulates an LLM/probabilistic prior that selects and chains available
        abstractions from the inherited library rather than blindly searching ASTs.
        """
        sketches: list[dict] = []
        arity = task.arity
        macros = self.registry.list_macros()
        macro_names = {m.name: m for m in macros}

        # Pattern A: Chained binary associative macros (e.g., max2, min2)
        if "max2" in macro_names and "max" in task.name:
            if arity == 3:
                # max3(x, y, z) = max2(x, max2(y, z))
                sketches.append(
                    {
                        "op": "CallMacro",
                        "macro": "max2",
                        "args": [
                            {"op": "Arg", "index": 0},
                            {
                                "op": "CallMacro",
                                "macro": "max2",
                                "args": [{"op": "Arg", "index": 1}, {"op": "Arg", "index": 2}],
                            },
                        ],
                    }
                )
            elif arity == 4:
                # max4(x, y, z, w) = max2(max2(x, y), max2(z, w))
                sketches.append(
                    {
                        "op": "CallMacro",
                        "macro": "max2",
                        "args": [
                            {
                                "op": "CallMacro",
                                "macro": "max2",
                                "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 1}],
                            },
                            {
                                "op": "CallMacro",
                                "macro": "max2",
                                "args": [{"op": "Arg", "index": 2}, {"op": "Arg", "index": 3}],
                            },
                        ],
                    }
                )

        if "min2" in macro_names and "min" in task.name:
            if arity == 3:
                # min3(x, y, z) = min2(x, min2(y, z))
                sketches.append(
                    {
                        "op": "CallMacro",
                        "macro": "min2",
                        "args": [
                            {"op": "Arg", "index": 0},
                            {
                                "op": "CallMacro",
                                "macro": "min2",
                                "args": [{"op": "Arg", "index": 1}, {"op": "Arg", "index": 2}],
                            },
                        ],
                    }
                )

        if "max2" in macro_names and "min2" in macro_names and "clamp" in task.name:
            # clamp(x, low, high) = max2(low, min2(x, high))
            sketches.append(
                {
                    "op": "CallMacro",
                    "macro": "max2",
                    "args": [
                        {"op": "Arg", "index": 1},  # low
                        {
                            "op": "CallMacro",
                            "macro": "min2",
                            "args": [
                                {"op": "Arg", "index": 0},
                                {"op": "Arg", "index": 2},
                            ],  # x, high
                        },
                    ],
                }
            )

        return sketches

    def solve_and_verify(
        self,
        task: SyGuSTask,
        base: dict,
        *,
        try_intuitive_prior: bool = True,
        max_cegis_rounds: int = 15,
    ) -> GuidanceVerdict:
        """Solves a SyGuS task using the Neuro-Symbolic CEGIS pipeline with Z3."""
        t0 = time.perf_counter()

        # Step 1: Fast Probabilistic Intuition Phase (O(1) sketch check)
        if try_intuitive_prior:
            sketches = self.propose_intuitive_sketches(task)
            for sketch in sketches:
                desugared = self.registry.desugar(sketch)
                verdict = verify_spec_with_z3(
                    desugared,
                    task.z3_spec,
                    arity=task.arity,
                    var_names=task.variable_names,
                    precondition=task.precondition,
                )
                if verdict.status == "SYMBOLIC_PROVED":
                    promoted = self.register_verified_tool(
                        task.name, task.arity, desugared, verdict.proof_scope
                    )
                    elapsed = (time.perf_counter() - t0) * 1000
                    return GuidanceVerdict(
                        task_name=task.name,
                        status="SYMBOLIC_PROVED",
                        expression=desugared,
                        provenance="intuitive_sketch",
                        z3_verdict=verdict,
                        macro_promoted=promoted,
                        elapsed_ms=elapsed,
                    )

        # Step 2: Inductive CEGIS Synthesis Loop (Refinement with Z3 counterexamples)
        cegis_res: CEGISResult = run_cegis_loop(
            task,
            base,
            macro_registry=self.registry,
            max_rounds=max_cegis_rounds,
        )

        elapsed = (time.perf_counter() - t0) * 1000

        if cegis_res.status == "PROVED" and cegis_res.expression is not None:
            promoted = self.register_verified_tool(
                task.name,
                task.arity,
                cegis_res.expression,
                cegis_res.z3_verdict.proof_scope,  # type: ignore
            )
            return GuidanceVerdict(
                task_name=task.name,
                status="SYMBOLIC_PROVED",
                expression=cegis_res.expression,
                provenance="cegis_synthesis",
                z3_verdict=cegis_res.z3_verdict,
                macro_promoted=promoted,
                elapsed_ms=elapsed,
            )

        return GuidanceVerdict(
            task_name=task.name,
            status=cegis_res.status,
            expression=None,
            provenance="failed",
            elapsed_ms=elapsed,
        )
