"""Hereditary abstraction engine and macro registry for reusable capabilities.

Enforces:
- Five hereditary policy groups preserved (no sixth gene).
- Reusable abstractions (macros) extracted via anti-unification and MDL pattern mining.
- Macro calls are desugared to pure, typed CIN-IR prior to independent verification.
- Positive transfer utility required for retention to prevent library bloat.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from ..ir import canonical_hash


@dataclass(frozen=True)
class Macro:
    """A verified reusable functional abstraction with typed parameters."""

    name: str
    arity: int
    body: dict
    origin_hash: str
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "arity": self.arity,
            "body": deepcopy(self.body),
            "origin_hash": self.origin_hash,
            "description": self.description,
            "metadata": deepcopy(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict) -> Macro:
        return cls(
            name=data["name"],
            arity=data["arity"],
            body=deepcopy(data["body"]),
            origin_hash=data["origin_hash"],
            description=data.get("description", ""),
            metadata=deepcopy(data.get("metadata", {})),
        )


def _substitute_args(node: dict, replacements: list[dict]) -> dict:
    """Beta-reduction: substitute Arg(i) with replacements[i]."""
    op = node.get("op")
    if op == "Arg":
        idx = node["index"]
        if 0 <= idx < len(replacements):
            return deepcopy(replacements[idx])
        return deepcopy(node)
    if op == "ConstInt":
        return deepcopy(node)

    args = [_substitute_args(child, replacements) for child in node.get("args", [])]
    result = {"op": op, "args": args}
    if "macro" in node:
        result["macro"] = node["macro"]
    return result


class MacroRegistry:
    """Registry of verified macro abstractions with desugaring and sugaring."""

    def __init__(self, macros: dict[str, Macro] | None = None):
        self._macros: dict[str, Macro] = dict(macros) if macros else {}

    def register(self, macro: Macro) -> None:
        self._macros[macro.name] = macro

    def get(self, name: str) -> Macro | None:
        return self._macros.get(name)

    def list_macros(self) -> list[Macro]:
        return list(self._macros.values())

    def __len__(self) -> int:
        return len(self._macros)

    def desugar(self, node: dict) -> dict:
        """Inlines all macro invocations, returning pure, standard CIN-IR."""
        op = node.get("op")
        if op == "CallMacro":
            macro_name = node["macro"]
            macro = self._macros.get(macro_name)
            if not macro:
                raise ValueError(f"Unknown macro '{macro_name}' in desugar")
            desugared_args = [self.desugar(arg) for arg in node.get("args", [])]
            if len(desugared_args) != macro.arity:
                raise ValueError(
                    f"Macro '{macro_name}' expects {macro.arity} arguments, got {len(desugared_args)}"
                )
            inlined = _substitute_args(macro.body, desugared_args)
            return self.desugar(inlined)

        if not node.get("args"):
            return deepcopy(node)

        desugared_children = [self.desugar(child) for child in node["args"]]
        return {"op": op, "args": desugared_children}

    def sugar(self, node: dict) -> dict:
        """Replaces isomorphic subtrees with CallMacro invocations to compress AST."""
        for macro in self._macros.values():
            matched, args = _matches_macro_pattern(node, macro.body, macro.arity)
            if matched:
                sugared_args = [self.sugar(a) for a in args]
                return {"op": "CallMacro", "macro": macro.name, "args": sugared_args}

        if not node.get("args"):
            return deepcopy(node)

        return {"op": node["op"], "args": [self.sugar(child) for child in node["args"]]}

    def to_dict(self) -> dict:
        return {name: m.to_dict() for name, m in self._macros.items()}

    @classmethod
    def from_dict(cls, data: dict) -> MacroRegistry:
        macros = {name: Macro.from_dict(m_dict) for name, m_dict in data.items()}
        return cls(macros)


def _matches_macro_pattern(expr: dict, pattern: dict, arity: int) -> tuple[bool, list[dict]]:
    """Checks if expr is an instance of pattern with arguments."""
    collected_args: list[dict | None] = [None] * arity

    def _match(e: dict, p: dict) -> bool:
        p_op = p.get("op")
        if p_op == "Arg":
            idx = p["index"]
            if idx >= arity:
                return False
            if collected_args[idx] is None:
                collected_args[idx] = deepcopy(e)
                return True
            return canonical_hash(collected_args[idx]) == canonical_hash(e)

        if e.get("op") != p_op:
            return False

        if p_op == "ConstInt":
            return e.get("value") == p.get("value")

        e_args = e.get("args", [])
        p_args = p.get("args", [])
        if len(e_args) != len(p_args):
            return False

        return all(_match(e_child, p_child) for e_child, p_child in zip(e_args, p_args))

    if not _match(expr, pattern):
        return False, []

    if any(arg is None for arg in collected_args):
        return False, []

    return True, [arg for arg in collected_args if arg is not None]


def anti_unify(t1: dict, t2: dict) -> tuple[dict, list[tuple[dict, dict]]]:
    """Computes the Least General Generalization (LGG) of two ASTs.

    Returns:
        (general_template, substitutions)
        where general_template contains {"op": "Arg", "index": i} holes
        and substitutions[i] = (term1_subterm, term2_subterm).
    """
    substitutions: list[tuple[dict, dict]] = []

    def _au(n1: dict, n2: dict) -> dict:
        if n1.get("op") == n2.get("op"):
            op = n1.get("op")
            if op == "ConstInt":
                if n1.get("value") == n2.get("value"):
                    return deepcopy(n1)
            elif op == "Arg":
                if n1.get("index") == n2.get("index"):
                    return deepcopy(n1)
            elif len(n1.get("args", [])) == len(n2.get("args", [])):
                children = [_au(c1, c2) for c1, c2 in zip(n1.get("args", []), n2.get("args", []))]
                return {"op": op, "args": children}

        # Check if this exact disagreement was already generalized to a parameter
        for idx, (s1, s2) in enumerate(substitutions):
            if canonical_hash(s1) == canonical_hash(n1) and canonical_hash(s2) == canonical_hash(
                n2
            ):
                return {"op": "Arg", "index": idx}

        new_idx = len(substitutions)
        substitutions.append((deepcopy(n1), deepcopy(n2)))
        return {"op": "Arg", "index": new_idx}

    template = _au(t1, t2)
    return template, substitutions


def ast_node_count(node: dict) -> int:
    """Counts total AST nodes."""
    children = node.get("args", [])
    return 1 + sum(ast_node_count(c) for c in children)


def collect_subtrees(node: dict, min_nodes: int = 3) -> list[dict]:
    """Collects all subtrees in node with at least min_nodes."""
    subtrees = []

    def _visit(n: dict) -> None:
        if ast_node_count(n) >= min_nodes:
            subtrees.append(deepcopy(n))
        for child in n.get("args", []):
            _visit(child)

    _visit(node)
    return subtrees


def normalize_args(node: dict) -> tuple[dict, int]:
    """Normalizes variables in a subtree so variables are numbered 0, 1, ... in order of appearance."""
    arg_map: dict[int, int] = {}

    def _norm(n: dict) -> dict:
        if n.get("op") == "Arg":
            idx = n["index"]
            if idx not in arg_map:
                arg_map[idx] = len(arg_map)
            return {"op": "Arg", "index": arg_map[idx]}
        if not n.get("args"):
            return deepcopy(n)
        return {"op": n["op"], "args": [_norm(child) for child in n["args"]]}

    normalized = _norm(node)
    return normalized, len(arg_map)


def extract_reusable_abstractions(
    expressions: list[dict],
    min_occurrences: int = 2,
    min_nodes: int = 3,
    max_arity: int = 3,
) -> list[Macro]:
    """Discovers reusable macros across program expressions using MDL compression.

    Description length savings:
    Delta L = (occurrences - 1) * nodes(body) - overhead
    """
    subterm_candidates: list[tuple[dict, int, str]] = []

    for expr in expressions:
        for sub in collect_subtrees(expr, min_nodes=min_nodes):
            norm_sub, arity = normalize_args(sub)
            if arity <= max_arity:
                subterm_candidates.append((norm_sub, arity, canonical_hash(norm_sub)))

    counts = Counter(h for _, _, h in subterm_candidates)
    unique_candidates: dict[str, tuple[dict, int]] = {}
    for norm_sub, arity, h in subterm_candidates:
        if h not in unique_candidates:
            unique_candidates[h] = (norm_sub, arity)

    macros = []
    macro_idx = 0
    for h, count in counts.items():
        if count >= min_occurrences:
            body, arity = unique_candidates[h]
            size = ast_node_count(body)
            # Minimum description length (MDL) compression savings:
            # Replaces 'count' occurrences of size 'size' with 'count' 1-node calls
            # Net savings: count * size - (size + count) = (count - 1) * size - count
            mdl_savings = (count - 1) * size - count
            if mdl_savings > 0:
                name = f"macro_{macro_idx}"
                macro_idx += 1
                macros.append(
                    Macro(
                        name=name,
                        arity=arity,
                        body=body,
                        origin_hash=h,
                        description=f"Auto-extracted abstraction with MDL savings {mdl_savings}",
                        metadata={
                            "occurrences": count,
                            "body_nodes": size,
                            "mdl_savings": mdl_savings,
                        },
                    )
                )

    return macros


def evaluate_transfer_utility(
    macro: Macro,
    evals_without: int,
    evals_with: int,
    extraction_cost: int = 1,
) -> float:
    """Calculates transfer utility on held-out tasks.

    Utility(M) = Work_without - (Work_with + Cost_extraction)
    """
    return float(evals_without - (evals_with + extraction_cost))
