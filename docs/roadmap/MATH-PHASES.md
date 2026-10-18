# Deeper mathematics research roadmap (v0.5)

**Status:** Proposed expansion of [P0-P6 roadmap](PHASES.md), not implementation progress. **Authority:** [math spec v0.5](../specs/2026-10-18-cin-mathematical-evolution-v0.5.md). Stage names identify evaluation gates, not calendar promises.

| Gate | Dependency | Shippable verified artifact | Hard exit criterion |
| --- | --- | --- | --- |
| M0: Baseline | existing P0 | reproducible current v0.1 outputs + frozen tests | no code/test regression; accurate facts about 2-input finite domain |
| M1: Search engine | P1 minimum accountable budgets | cost-fair typed search + tier-1 `min2`/`absdiff` specs | correct signed-input program found for two new relations; random/legacy controls run |
| M2: New type contracts | M1 | versioned IR + world v0.2 supporting 3+ input variables | old fixtures still work; `median3`, `clamp` finite-domain verified; invalid inputs rejected |
| M3: True co-evolution | M2, P2 | math relation transformation and uniqueness admission | at least 3 distinct semantic relations; duplicated domains never count as novel |
| M4: Transfer | M2/M3, P3 | macro extraction, replay inheritance, population lifecycles | verified macro reused in at least two distinct functions; cost vs no-macro control recorded |
| M5: Formal strength | M4; solver decision | optional independent SMT validity/counterexample adapter | sound explicit proof-scope tags, `UNKNOWN` handling, cross-check against finite reference |
| M6: Iterative algorithms | M5 + separate worker safety decision | bounded `gcd(a,b)` via Euclid, typed loop+mod arithmetic | signed/zero edge cases, termination/resource caps and no built-in gcd shortcut |
| M7: Mathematical generalization | M6 | optional extended-GCD typed tuple result | Bézout invariant, correctness scope, no evidence leakage, matched baselines |
| M8: Comparative study | applicable P5 gates | preregistered R0-R5 study across multiple cohorts | honest uncertainty and reproducibility, including negative results |

**Rollback and dependency discipline:** M1 must not modify verifier semantics. M2 introduces *new* versioned artifacts, not reinterpretation of stored v0.1 hashes. M5 can be abandoned if SMT adapter adds no independent evidence. M6 is intentionally not part of the first coding PR. M7 is research stretch and may be cancelled. M8 conclusions require full cost accounting and frozen independent holdouts.

**First PR scope recommendation:** Implement M1 only, plus one end-to-end tier-1 synthesis test and repeatable baseline study script, leaving the current MAX2 demo/CLI intact. M2-M8 each require separately reviewable PRs. Do not replace this roadmap with an enormous single PR.
