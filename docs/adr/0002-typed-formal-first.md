# ADR-0002: Formal specifications and typed IR before free-form source generation

- **Status:** Accepted, implemented for the bounded v0.1 slice
- **Date:** 2026-10-18

## Context

Unconstrained source mutation produces many syntactically invalid programs, expands attack surface and makes correctness claims hard to interpret. The project requires no pretrained coding model and independent verification.

## Decision

Represent evolving programs as a typed, pure, bounded CIN intermediate representation; admit worlds only against fixed, machine-checkable specification contracts. Export source only as a readable derivative, not as trusted execution evidence. Use exhaustive finite-domain checks in v0.1. Consider solver-backed checks later with explicitly recorded proof scopes.

## Rejected alternatives

- Execute arbitrary generated Python in the host process: unsafe and difficult to bound.
- Introduce a general multi-language compiler or runtime now: premature before the research mechanism is demonstrated.
- Treat a bounded solver failure as proof of unsatisfiability: incorrect semantics.

## Consequences

The grammar limits reachable functionality. Grammar expansion needs independent type, termination, resource, regression and migration checks. Verified results are always scoped to the admitted domain and semantics.
