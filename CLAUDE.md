# CLAUDE.md — Operating Instructions for Code-In-Nothing

See `AGENTS.md` for complete operating guide and repository invariants.

## Epistemic Integrity & Anti-Embellishment Protocol

### 1. Zero Hype & Lexical Discipline
- Never use emojis, celebratory framing, or persuasive storytelling in technical reports, summaries, commit messages, or code comments.
- Prohibited claims and phrases: "radically solved", "root solution", "solved once and for all", "complete mathematical proof", "100% guaranteed", "zero overhead", or "flawless".
- Describe every implementation strictly by its standard algorithmic name, worst-case time and space complexity, and exact domain boundaries.

### 2. Full-Cost Accounting (Anti-Metric Gaming)
- Reporting final candidate proposals alone when claiming search space reduction is classified as metric falsification.
- Every synthesis run must separately count and report:
  1. Total enumerated primitive sub-expressions and predicates.
  2. Total evaluator executions across public probes.
  3. Auxiliary search work (entropy calculations, interval propagation steps, anti-unification passes).
  4. Verifier invocations and verification runtime.
  5. End-to-end wall-clock time in milliseconds and peak memory usage.
- Hereditary library claims must include the full computational cost of discovering, compressing, validating, and indexing macros inside the total budget.

### 3. Zero-Omission Reporting (Anti-Cherry-Picking)
- Every task specification in `examples/` and every registered benchmark world must appear in every benchmark table.
- Never omit, silence, or defer a task that times out, runs slowly, or fails verification. Display `TIMEOUT`, `MEMOUT`, `UNSOUND`, or `FAILED` explicitly in the primary results table right next to passing tasks.

### 4. Anti-Curriculum Leakage & Distractor Stress Testing
- Evaluating an inherited macro immediately on a composite target built from recently solved sub-components demonstrates only that tested composition and task order. Report the curriculum exposure and use shuffled and held-out controls before claiming generalization.
- Every library-learning or inheritance claim requires two mandatory stress tests before reporting success:
  1. Shuffled task ordering across unrelated problem structures.
  2. Distractor injection: pre-loading the library with 20 valid, unrelated macros and measuring the branching-factor slowdown on tasks that gain zero benefit from them.

### 5. Mathematical & Domain Soundness Disclosure
- Explicitly separate real/rational relaxations (R, Q) from exact integer arithmetic (Z), and finite-grid witness checks from unbounded formal proofs.
- When a routine operates over rational relaxations or lacks exact integer divisibility handling, document that soundness gap. An UNSAT result for a sound overapproximation of all integer counterexamples can justify `PROVED`; satisfiable relaxations without an integer witness justify only `RATIONAL_RELAXATION_CHECKED` or `UNKNOWN`.
- State the exact grammar shapes that defeat each search heuristic (such as top-level arithmetic operations sitting above independent conditional branches in top-down decision trees).

### 6. Build Hygiene Separation
- Classify `pytest` pass counts, schema validation, and `ruff` checks strictly as build hygiene. Never cite self-authored unit tests passing as empirical evidence for a research claim.
- Pair each synthesis or verification module with adversarial tests relevant to its behavior: high arity for generators, non-unit coefficients and rational/integer gaps for numeric reasoning, nested arithmetic-over-conditionals for expression search, and cyclic or invalid macro graphs for AST transformations. Document inapplicable cases rather than testing them outside a module's contract.

### 7. Mandatory Milestone Report Schema
Respond in the user's language using strictly these five sections, without introductory or closing commentary:
1. **Mechanism & Complexity**: Modified files, exact algorithm implemented, and theoretical worst-case complexity.
2. **Complete Benchmark Matrix**: Every task in the repository with all five full-cost counters and zero omissions.
3. **Isolated Ablation**: Direct side-by-side numbers with the single target module toggled OFF vs. ON while keeping all other modules fixed.
4. **Distractor & High-Arity Stress Test**: Measurements with 20 irrelevant library macros active and tasks with 5 to 8 inputs.
5. **Failure Boundaries & Known Unsoundness**: Concrete input tuples, expression depths, or grammar shapes where the current implementation fails, times out, or produces false positives/negatives. If an adversarial search finds no concrete failure, report its tested grammar, bounds and budget explicitly and state that no failure was found within that scope. Do not invent failures or suppress results.
