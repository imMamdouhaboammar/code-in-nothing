# ADR 0005 — Cost-layered observational search for tier-1 mathematics

**Date:** 2026-10-18  
**Status:** Proposed implementation in [PR #1](https://github.com/imMamdouhaboammar/code-in-nothing/pull/1), pending review  
**Scope:** M1 only, on top of [mathematical v0.5](../specs/2026-10-18-cin-mathematical-evolution-v0.5.md).

## Context and competing designs

The pre-M1 enumerator in `cin/search.py` constructed leaves, one binary
operation over leaves, and shallow conditionals with leaf branches. This
cannot construct `If(LessThan(x,y), Sub(y,x), Sub(x,y))`, so the signed
absolute-difference relation is outside its grammar.

1. **Unpruned exact-size enumeration:** simple and potentially complete under
   fixed bounds, but exhausts the number of combinations before useful nested
   conditionals appear.
2. **World-aware CEGIS:** uses task counterexamples for smarter synthesis,
   but needs a separately budgeted training-verifier interface and strict
   witness/holdout isolation; too large for this initial change.
3. **Chosen — cost-layered, typed enumeration with observational pruning:**
   reuse distinct integer and boolean subterms, ordered by AST nodes, and
   screen equivalent behavior on a fixed, task-independent input grid.

## Decision

Keep candidate generation in `cin/search.py`. Use the existing operations
`Arg`, `ConstInt`, `Add`, `Sub`, `LessThan`, `Equal`, and `If` when
enabled in the five-gene genome. Construct typed Int/Bool banks from smaller
cost layers; `If` composes an Int result from a Bool predicate and two
Int branches. Reuse a validated parent at its true AST cost. Distinguish
candidate-proposal ceiling from internal shape-attempt ceiling. Seed controls
stable operator order only; no world or verifier answers are inputs.

Prune observed-equivalent terms on the fixed 49-point grid `[-3,3]^2`.
This **sacrifices completeness**: signatures may collide for programs that
differ outside the grid. Neither an observational signature nor search
exhaustion is evidence of mathematical correctness or unsatisfiability.
The independent `cin.worlds.verify_program` remains the only accepting
behavioral gate, with a declared finite-domain scope.

Extend only the *verifier's* formal-world language in opt-in
`cin.world/v0.2` to support recursive `sub` terms. This is **not**
a built-in absolute value, a new organism primitive, or a migration of
v0.1 worlds. The existing `cin.world/v0.1` schema and five genome genes
remain unchanged.

## Ownership and controls

- `cin/ir.py`: existing typed interpretation, static resource bounds.
- `cin/search.py`: task-blind typed composition and observational pruning.
- `cin/contracts.py` / versioned JSON schema: declarative world parsing.
- `cin/worlds.py`: subtraction-term semantics and independent verification.
- `cin/evolution.py`, `cin/archive.py`: unchanged lifecycle and evidence.
- `experiments/run_m1.py`: explicitly development-only screening and
  reproducible finite-domain results; no task answers enter the generator.

## Risks and follow-up gates

The fixed-probe semantic reduction is incomplete; increasing budgets can
generate more branches without guaranteeing discovery. The current pilot
does not instrument all internal shape attempts, witness admission work,
or comparison baselines. Search resource accounting should be upgraded
before claiming relative computational efficiency. M2 must version
multi-argument signatures before attempting `median3` or `clamp`.
M3 unique-output admission, M4 cross-task inheritance, SMT M5,
and bounded iterative GCD M6 remain separately gated work.

Prior work: [Alur et al., 2017](https://www.cis.upenn.edu/~alur/Tacas17.pdf);
[Probe, OOPSLA 2020](https://cseweb.ucsd.edu/~hpeleg/probe-oopsla20.pdf).
These motivate enumeration and observational pruning; they do not prove
the CIN experiment's effectiveness.
