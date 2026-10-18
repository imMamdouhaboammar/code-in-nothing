# ADR-0001: Verification authority remains outside evolution

- **Status:** Accepted architectural constraint; partial in-process enforcement in v0.1
- **Date:** 2026-10-18

## Context

Worlds and organisms are both allowed to evolve. If either actor can alter its own success tests, the system can promote apparent progress by weakening the tests or redefining maturity. The current prototype uses a separate Python module and data-only IR but shares one trusted host process.

## Decision

The independent verifier exclusively owns the evaluation protocol, approved world admission, promotion decisions, sealed transfer evaluation and maturity certification. Candidate organisms and world generators receive only permitted task descriptions, bounded feedback and evidence references. Future execution of less restricted code requires a separate OS-level isolation boundary; a module boundary alone is insufficient.

## Rejected alternatives

- Let a world produce both a task and the final oracle used to rank itself: permits circular verification.
- Let each organism author its own evaluator: permits benchmark gaming.
- Deploy microservices immediately: adds distributed complexity without solving the current in-process trust weakness by itself.

## Consequences

Every promotion has an evaluator version, resource accounting and independently replayable certificate. UNKNOWN and exhausted budget are not PASS. Release of hidden evaluations and promotion policy updates must be separately authorized and versioned.
