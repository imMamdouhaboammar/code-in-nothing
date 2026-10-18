# ADR-0003: One modular research runtime before distributed scheduling

- **Status:** Accepted for next phase; review when isolation needs change
- **Date:** 2026-10-18

## Context

A many-service design would introduce queues, consensus, deployment, retry and reconciliation problems before the system has established that co-evolution improves held-out transfer.

## Decision

Keep research scheduling, state transitions and evidence collection in one Python runtime using explicit internal ownership boundaries. Persistent SQLite and content-addressed artifacts are proposed only when multiple generations and resume become necessary. Isolated worker processes are a security and resource boundary, not a rationale for prematurely distributing orchestration.

## Consequences

No web dashboard, microservices, broker, remote worker protocol or multi-language code generation is part of the near-term gate. Introduce distribution only after measured bottlenecks and verified recovery semantics.
