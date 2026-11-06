"""Information-theoretic conditional program synthesis with branch decoupling.

Decouples control flow (predicates) from data operations (subterms) via
observational coverage partitioning and decision tree induction.
Reuses observational signatures and explores a bounded set of decision partitions.
Worst-case search remains combinatorial; no polynomial-time guarantee is implied.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from cin.ir import IRViolation, Limits, canonical_hash, check_tree, run_ir_args
from cin.worlds import _ordered_input_names, check_formula


def _size_depth(node: dict) -> tuple[int, int]:
    """Calculate total AST nodes and maximum depth."""
    children = node.get("args", ())
    if not children:
        return 1, 1
    dimensions = [_size_depth(child) for child in children]
    return 1 + sum(size for size, _ in dimensions), 1 + max(depth for _, depth in dimensions)


@dataclass(frozen=True)
class DecisionResult:
    """Outcome of information-theoretic conditional synthesis."""

    expression: dict
    nodes: int
    depth: int
    candidate_evaluations: int
    shapes_attempted: int


@dataclass
class SynthesisWork:
    """Actual search work counters, including discarded program candidates."""

    primitive_subterms: int = 0
    primitive_predicates: int = 0
    subterm_representatives: int = 0
    predicate_representatives: int = 0
    probe_evaluations: int = 0
    auxiliary_scoring_steps: int = 0


def generate_candidate_subterms(
    arity: int,
    allowed: set[str],
    constants: list[int],
    probe_cases: tuple[tuple[int, ...], ...],
    max_depth: int = 3,
    limits: Limits = Limits(),
    macro_registry: Any | None = None,
    work: SynthesisWork | None = None,
) -> list[dict]:
    """Generate arithmetic subterms with observational equivalence pruning."""
    leaves: list[dict] = []
    if "Arg" in allowed:
        for i in range(arity):
            leaves.append({"op": "Arg", "index": i})
    if "ConstInt" in allowed:
        for c in constants:
            leaves.append({"op": "ConstInt", "value": c})

    bank: dict[tuple[int, ...], dict] = {}

    def try_add(expr: dict, depth: int) -> bool:
        if depth > max_depth:
            return False
        if work is not None:
            work.primitive_subterms += 1
        try:
            eval_expr = macro_registry.desugar(expr) if macro_registry is not None else expr

            def eval_probe(pt: tuple[int, ...]) -> int:
                if work is not None:
                    work.probe_evaluations += 1
                return run_ir_args(eval_expr, pt, limits, expected_arity=arity)

            sig = tuple(eval_probe(pt) for pt in probe_cases)
            if sig not in bank:
                bank[sig] = expr
                if work is not None:
                    work.subterm_representatives += 1
                return True
            existing = bank[sig]
            if _size_depth(expr)[0] < _size_depth(existing)[0]:
                bank[sig] = expr
        except (IRViolation, ValueError):
            return False
        return False

    for leaf in leaves:
        try_add(leaf, 1)

    arithmetic_ops = [op for op in ("Add", "Sub") if op in allowed]
    current_terms = list(bank.values())

    for d in range(2, max_depth + 1):
        next_terms = []
        for op in arithmetic_ops:
            for left in current_terms:
                left_depth = _size_depth(left)[1]
                left_hash = canonical_hash(left)
                for right in current_terms:
                    right_depth = _size_depth(right)[1]
                    new_depth = 1 + max(left_depth, right_depth)
                    if new_depth != d:
                        continue
                    # Commutative symmetry pruning: Add(a, b) == Add(b, a)
                    if op == "Add" and left_hash > canonical_hash(right):
                        continue
                    # Trivial identity pruning
                    if op == "Sub" and left == right:
                        continue
                    if op == "Add" and right == {"op": "ConstInt", "value": 0}:
                        continue
                    if op == "Sub" and right == {"op": "ConstInt", "value": 0}:
                        continue
                    expr = {"op": op, "args": [left, right]}
                    if try_add(expr, new_depth):
                        next_terms.append(expr)

        if macro_registry is not None:
            for macro in macro_registry.list_macros():
                if macro.arity == 1:
                    for t in current_terms:
                        new_depth = 1 + _size_depth(t)[1]
                        if new_depth == d:
                            expr = {"op": "CallMacro", "macro": macro.name, "args": [t]}
                            if try_add(expr, new_depth):
                                next_terms.append(expr)
                elif macro.arity == 2:
                    for left in current_terms:
                        left_depth = _size_depth(left)[1]
                        for right in current_terms:
                            right_depth = _size_depth(right)[1]
                            new_depth = 1 + max(left_depth, right_depth)
                            if new_depth == d:
                                expr = {
                                    "op": "CallMacro",
                                    "macro": macro.name,
                                    "args": [left, right],
                                }
                                if try_add(expr, new_depth):
                                    next_terms.append(expr)

        if not next_terms:
            break
        current_terms = list(bank.values())

    return list(bank.values())


def generate_candidate_predicates(
    atomic_terms: list[dict],
    allowed: set[str],
    probe_cases: tuple[tuple[int, ...], ...],
    arity: int,
    limits: Limits = Limits(),
    macro_registry: Any | None = None,
    work: SynthesisWork | None = None,
) -> list[dict]:
    """Generate boolean atomic comparison predicates with observational pruning."""
    comparison_ops = [op for op in ("LessThan", "Equal") if op in allowed]
    bank: dict[tuple[bool, ...], dict] = {}

    for op in comparison_ops:
        for i, left in enumerate(atomic_terms):
            for j, right in enumerate(atomic_terms):
                if left == right:
                    continue
                # Equal is symmetric: Equal(a, b) == Equal(b, a)
                if op == "Equal" and i > j:
                    continue
                pred = {"op": op, "args": [left, right]}
                if work is not None:
                    work.primitive_predicates += 1
                try:
                    eval_pred = macro_registry.desugar(pred) if macro_registry is not None else pred

                    def eval_probe(pt: tuple[int, ...]) -> bool:
                        if work is not None:
                            work.probe_evaluations += 1
                        return bool(run_ir_args(eval_pred, pt, limits, expected_arity=arity))

                    sig = tuple(eval_probe(pt) for pt in probe_cases)
                    # Filter out vacuous/trivial predicates that never branch
                    if all(sig) or not any(sig):
                        continue
                    if sig not in bank:
                        bank[sig] = pred
                        if work is not None:
                            work.predicate_representatives += 1
                    else:
                        existing = bank[sig]
                        if _size_depth(pred)[0] < _size_depth(existing)[0]:
                            bank[sig] = pred
                except (IRViolation, ValueError):
                    continue

    return list(bank.values())


def synthesize_conditional_tree(
    cases: tuple[tuple[int, ...], ...],
    target_spec: dict | tuple[int, ...] | Callable[[tuple[int, ...], int], bool],
    base: dict,
    *,
    subterms: list[dict] | None = None,
    predicates: list[dict] | None = None,
    max_tree_depth: int | None = None,
    macro_registry: Any | None = None,
    work: SynthesisWork | None = None,
) -> DecisionResult | None:
    """Synthesize a verified conditional AST via information-theoretic branch decoupling.

    Args:
        cases: Finite sample of input tuples.
        target_spec: Formal world dictionary (with 'postcondition'), tuple of expected
                     target integers, or callable check function (point, val) -> bool.
        base: Organism base genome configuration.
        subterms: Optional pre-generated integer expressions.
        predicates: Optional pre-generated boolean comparison expressions.
        max_tree_depth: Maximum tree depth allowed (defaults to base['max_ast_depth']).
        macro_registry: Optional MacroRegistry containing inherited functional abstractions.

    Returns:
        DecisionResult containing the synthesized AST, or None if no covering tree exists.
    """
    if not cases:
        return None

    allowed = set(base["allowed_primitives"])
    constants = base.get("allowed_constants", [0, 1])
    arity = len(base.get("input_types", ("Int", "Int")))
    if isinstance(target_spec, dict) and "postcondition" in target_spec:
        domain = target_spec.get("input_domain", {})
        var_names = (
            _ordered_input_names(target_spec) if domain else [f"arg{i}" for i in range(arity)]
        )
        precondition = target_spec.get("precondition")
        if precondition is not None:
            cases = tuple(
                pt
                for pt in cases
                if check_formula(
                    precondition,
                    {**dict(zip(var_names, pt)), "result": 0},
                )
            )
            if not cases:
                return None

    limits = Limits(
        max_depth=base["max_ast_depth"],
        max_nodes=base["max_ast_nodes"],
    )
    effective_max_depth = base["max_ast_depth"] if max_tree_depth is None else max_tree_depth
    if effective_max_depth < 1:
        return None

    if subterms is None:
        subterms = generate_candidate_subterms(
            arity,
            allowed,
            constants,
            cases,
            max_depth=3,
            limits=limits,
            macro_registry=macro_registry,
            work=work,
        )

    atomic_terms = [t for t in subterms if _size_depth(t)[1] <= 2]

    if predicates is None and "If" in allowed:
        predicates = generate_candidate_predicates(
            atomic_terms,
            allowed,
            cases,
            arity,
            limits=limits,
            macro_registry=macro_registry,
            work=work,
        )
    elif predicates is None:
        predicates = []

    # Prepare oracle check
    if isinstance(target_spec, tuple):
        if len(target_spec) != len(cases):
            raise ValueError("target_spec tuple length must match cases length")

        def is_correct(idx: int, val: int) -> bool:
            return val == target_spec[idx]

    elif callable(target_spec):

        def is_correct(idx: int, val: int) -> bool:
            return target_spec(cases[idx], val)

    elif isinstance(target_spec, dict) and "postcondition" in target_spec:
        post = target_spec["postcondition"]
        domain = target_spec.get("input_domain", {})
        var_names = (
            _ordered_input_names(target_spec) if domain else [f"arg{i}" for i in range(arity)]
        )

        def is_correct(idx: int, val: int) -> bool:
            pt = cases[idx]
            values = {k: v for k, v in zip(var_names, pt)}
            values["result"] = val
            return check_formula(post, values)

    else:
        raise ValueError("unsupported target_spec format")

    evaluations = 0
    shapes = 0
    universe = set(range(len(cases)))

    # Step 1: Subterm Candidate Evaluation & Coverage Mapping
    valid_subterms: list[dict] = []
    term_coverage: list[set[int]] = []

    for term in subterms:
        cov = set()
        shapes += 1
        is_term_valid = True
        for idx, pt in enumerate(cases):
            evaluations += 1
            if work is not None:
                work.probe_evaluations += 1
            try:
                eval_term = macro_registry.desugar(term) if macro_registry is not None else term
                v = run_ir_args(eval_term, pt, limits, expected_arity=arity)
                if is_correct(idx, v):
                    cov.add(idx)
            except (IRViolation, ValueError):
                is_term_valid = False
                break
        if not is_term_valid:
            continue

        # Single term completes the task with no conditionals
        if cov == universe:
            try:
                desugared = macro_registry.desugar(term) if macro_registry is not None else term
                check_tree(desugared, base)
                size, depth = _size_depth(desugared)
                if depth <= effective_max_depth:
                    return DecisionResult(
                        expression=desugared,
                        nodes=size,
                        depth=depth,
                        candidate_evaluations=evaluations,
                        shapes_attempted=shapes,
                    )
            except (IRViolation, ValueError):
                pass

        if cov:
            valid_subterms.append(term)
            term_coverage.append(cov)

    if "If" not in allowed:
        return None

    # Step 2: Boolean Truth Partitioning for Predicates
    valid_predicates: list[dict] = []
    predicate_truth_sets: list[set[int]] = []

    for pred in predicates:
        truth_set = set()
        is_pred_valid = True
        shapes += 1
        for idx, pt in enumerate(cases):
            evaluations += 1
            if work is not None:
                work.probe_evaluations += 1
            try:
                eval_pred = macro_registry.desugar(pred) if macro_registry is not None else pred
                b = run_ir_args(eval_pred, pt, limits, expected_arity=arity)
                if b:
                    truth_set.add(idx)
            except (IRViolation, ValueError):
                is_pred_valid = False
                break
        if not is_pred_valid:
            continue

        if truth_set == universe or len(truth_set) == 0:
            continue

        valid_predicates.append(pred)
        predicate_truth_sets.append(truth_set)

    # Step 3: Exact Dual-Branch Decoupled Coverage
    best_result: DecisionResult | None = None

    for i in range(len(valid_subterms)):
        cov1 = term_coverage[i]
        t1 = valid_subterms[i]
        for j in range(len(valid_subterms)):
            if i == j:
                continue
            if work is not None:
                work.auxiliary_scoring_steps += 1
            cov2 = term_coverage[j]
            t2 = valid_subterms[j]

            # Fast bitset check: union must cover all points
            if (cov1 | cov2) != universe:
                continue

            must_true = cov1 - cov2
            must_false = cov2 - cov1

            for k, pred in enumerate(valid_predicates):
                if work is not None:
                    work.auxiliary_scoring_steps += 1
                p_true = predicate_truth_sets[k]
                if must_true.issubset(p_true) and p_true.isdisjoint(must_false):
                    expr = {"op": "If", "args": [pred, t1, t2]}
                    shapes += 1
                    try:
                        desugared = (
                            macro_registry.desugar(expr) if macro_registry is not None else expr
                        )
                        check_tree(desugared, base)
                        size, depth = _size_depth(desugared)
                        if depth <= effective_max_depth:
                            res = DecisionResult(
                                expression=desugared,
                                nodes=size,
                                depth=depth,
                                candidate_evaluations=evaluations,
                                shapes_attempted=shapes,
                            )
                            if best_result is None or res.nodes < best_result.nodes:
                                best_result = res
                                if best_result.nodes <= 7:
                                    return best_result
                    except (IRViolation, ValueError):
                        continue

    if best_result is not None:
        return best_result

    # Step 4: Bounded, score-guided backtracking over conditional partitions.
    # A locally attractive ID3 split can make a subsequent branch impossible.
    branch_attempts = 0
    branch_budget = max(32, min(512, len(valid_predicates) * len(cases) * 2))
    successful_subtrees: dict[tuple[frozenset[int], int], dict] = {}

    def induce_tree(active_points: set[int], current_depth: int) -> dict | None:
        nonlocal branch_attempts, shapes
        if not active_points or current_depth > effective_max_depth:
            return None

        key = (frozenset(active_points), current_depth)
        if key in successful_subtrees:
            return successful_subtrees[key]

        # Prefer the smallest complete leaf before attempting another branch.
        matching_leaves = [
            term for term, cov in zip(valid_subterms, term_coverage) if active_points.issubset(cov)
        ]
        if matching_leaves:
            best = min(matching_leaves, key=lambda term: _size_depth(term)[0])
            successful_subtrees[key] = best
            return best

        if current_depth + 2 > effective_max_depth or branch_attempts >= branch_budget:
            return None

        ranked_splits = []
        for pred, p_true in zip(valid_predicates, predicate_truth_sets):
            true_pts = active_points & p_true
            false_pts = active_points - p_true
            if not true_pts or not false_pts:
                continue
            if work is not None:
                work.auxiliary_scoring_steps += 2 * len(term_coverage)
            max_true_cov = max((len(true_pts & cov) for cov in term_coverage), default=0)
            max_false_cov = max((len(false_pts & cov) for cov in term_coverage), default=0)
            ranked_splits.append((max_true_cov + max_false_cov, pred, true_pts, false_pts))

        ranked_splits.sort(key=lambda split: split[0], reverse=True)
        for _, pred, true_pts, false_pts in ranked_splits:
            if branch_attempts >= branch_budget:
                break
            branch_attempts += 1
            shapes += 1
            then_child = induce_tree(true_pts, current_depth + 1)
            if then_child is None:
                continue
            else_child = induce_tree(false_pts, current_depth + 1)
            if else_child is None:
                continue
            result = {"op": "If", "args": [pred, then_child, else_child]}
            successful_subtrees[key] = result
            return result
        return None

    multi_expr = induce_tree(universe, 1)
    if multi_expr is not None:
        try:
            desugared = (
                macro_registry.desugar(multi_expr) if macro_registry is not None else multi_expr
            )
            check_tree(desugared, base)
            size, depth = _size_depth(desugared)
            if depth <= effective_max_depth:
                return DecisionResult(
                    expression=desugared,
                    nodes=size,
                    depth=depth,
                    candidate_evaluations=evaluations,
                    shapes_attempted=shapes,
                )
        except (IRViolation, ValueError):
            pass

    return None
