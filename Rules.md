# Epistemic Integrity & Anti-Embellishment Protocol

## 1. Zero Hype & Lexical Discipline
- Never use emojis, celebratory framing, or persuasive storytelling in technical reports, summaries, commit messages, or code comments.
- Prohibited claims and phrases: "radically solved", "root solution", "solved once and for all", "complete mathematical proof", "100% guaranteed", "zero overhead", or "flawless".
- Describe every implementation strictly by its standard algorithmic name, worst-case time and space complexity, and exact domain boundaries.

## 2. Full-Cost Accounting (Anti-Metric Gaming)
- Reporting final candidate proposals alone when claiming search space reduction is classified as metric falsification.
- Every synthesis run must separately count and report:
  1. Total enumerated primitive sub-expressions and predicates.
  2. Total evaluator executions across public probes.
  3. Auxiliary search work (entropy calculations, interval propagation steps, anti-unification passes).
  4. Verifier invocations and verification runtime.
  5. End-to-end wall-clock time in milliseconds and peak memory usage.
- Hereditary library claims must include the full computational cost of discovering, compressing, validating, and indexing macros inside the total budget.

## 3. Zero-Omission Reporting (Anti-Cherry-Picking)
- Every task specification in `examples/` and every registered benchmark world must appear in every benchmark table.
- Never omit, silence, or defer a task that times out, runs slowly, or fails verification. Display `TIMEOUT`, `MEMOUT`, `UNSOUND`, or `FAILED` explicitly in the primary results table right next to passing tasks.

## 4. Anti-Curriculum Leakage & Distractor Stress Testing
- Evaluating an inherited macro immediately on a composite target whose exact sub-components were solved in the preceding step counts as curriculum leakage and proves zero generalization.
- Every library-learning or inheritance claim requires two mandatory stress tests before reporting success:
  1. Shuffled task ordering across unrelated problem structures.
  2. Distractor injection: pre-loading the library with 20 valid, unrelated macros and measuring the branching-factor slowdown on tasks that gain zero benefit from them.

## 5. Mathematical & Domain Soundness Disclosure
- Explicitly separate real/rational relaxations (R, Q) from exact integer arithmetic (Z), and finite-grid witness checks from unbounded formal proofs.
- Whenever a routine (such as Fourier-Motzkin elimination) operates over rationals or lacks exact integer divisibility handling (non-integral polyhedra / dark shadows), document that soundness gap explicitly in code docstrings and milestone reports, and downgrade any `PROVED` label to `RATIONAL_RELAXATION_CHECKED`.
- State the exact grammar shapes that defeat each search heuristic (such as top-level arithmetic operations sitting above independent conditional branches in top-down decision trees).

## 6. Build Hygiene Separation
- Classify `pytest` pass counts, schema validation, and `ruff` checks strictly as build hygiene. Never cite self-authored unit tests passing as empirical evidence for a research claim.
- Pair every synthesis or verification module with an adversarial falsification test covering 5 to 8 input variables, prime coefficients greater than 1, nested arithmetic-over-conditionals, and rational regions containing zero integers.

## 7. Mandatory Milestone Report Schema
Respond in the user's language using strictly these five sections, without introductory or closing commentary:
1. **Mechanism & Complexity**: Modified files, exact algorithm implemented, and theoretical worst-case complexity.
2. **Complete Benchmark Matrix**: Every task in the repository with all five full-cost counters and zero omissions.
3. **Isolated Ablation**: Direct side-by-side numbers with the single target module toggled OFF vs. ON while keeping all other modules fixed.
4. **Distractor & High-Arity Stress Test**: Measurements with 20 irrelevant library macros active and tasks with 5 to 8 inputs.
5. **Failure Boundaries & Known Unsoundness**: Concrete input tuples, expression depths, or grammar shapes where the current implementation fails, times out, or produces false positives/negatives. If you cannot exhibit a concrete failure case, pause reporting and write a harder adversarial test until the boundary breaks.