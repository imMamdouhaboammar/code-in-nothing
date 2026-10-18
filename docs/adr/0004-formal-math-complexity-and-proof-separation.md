# ADR 0004: Math-first semantic complexity and independent proof

**Status:** Proposed for v0.5 (requires implementation gates); **Date:** 2026-10-18.

## Context

CIN's v0.1 program grammar accepts two integer parameters and finite-domain verification. Increasing AST length or domain bounds cannot establish deeper mathematical reasoning. Allowing external SMT synthesis to provide all solutions would undermine the measurement of internal evolutionary discovery. Unrestricted Python execution introduces a separate high-risk security boundary.

## Decision

Extend program expressivity through *versioned, typed IR and formal world contracts*, proceeding from nested arithmetic/conditionals and 3-variable tasks, to bounded iteration/modulo and optional tuple-returning algorithms. Verification stays outside the organism/world evolutionary actors and records exact proof scope. Solvers may disprove or certify candidates, not silently act as the organism's solution generator. Defer loops, network, plugins, web APIs, arbitrary Python and neural heuristics until separately gated.

## Alternatives rejected for initial expansion

1. Use a pretrained coding LLM or a ready-to-run SyGuS solver as the organism: changes core research question and confounds attribution.
2. Grow arbitrary executable Python files: loses typed safety and bounded semantics.
3. Build full symbolic mathematics algebra library first: unneeded complexity before Tier 1-3 results.
4. Treat code size as fitness: rewards bloat and unverified behaviors.

## Consequences

Positive: independent evidence and comparable complexity progression. Negative: expressive power will grow slowly, finite checks are not universal proofs, and formal contract migrations require tests. Future changes must update [v0.5 specification](../specs/2026-10-18-cin-mathematical-evolution-v0.5.md) and emit a new versioned protocol when semantics change.
