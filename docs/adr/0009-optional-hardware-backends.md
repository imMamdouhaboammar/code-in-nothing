# ADR 0009 — Optional hardware signatures before a CIN-ISA or RTL tournament

**Date:** 2026-10-18
**Status:** PROPOSED / awaits engineering review
**Context:** [Full design](../superpowers/specs/2026-10-18-cin-hardware-co-design.md), [gated roadmap](../roadmap/HARDWARE-PHASES.md), [research ledger](../research/2026-10-18-hardware-co-design-evidence.md).
**Relation:** Extends [ADR 0003](0003-single-process-first.md) without superseding it. Complies with [CIN Not Broke Rules](../architecture/NOT-BROKE-RULES.md).

## Context

CIN currently synthesizes and verifies small typed, bounded mathematical expressions in Python. The cost-layered search uses finite observational-signature vectors as a heuristic for duplicate elimination. There is no measured proof that these signatures dominate runtime, or that FPGA transport overhead is justified.

FeSens/openTPU demonstrates a useful discipline: explicit ISA and bit-exact simulator/RTL correspondence. FeSens/auto-arch-tournament demonstrates a useful research pattern: isolated RTL hypothesis edits, immutable correctness gates and fixed multi-seed PPA comparisons. Neither is an equivalent workload or drop-in module for CIN.

## Decision

1. **Always preserve the reference CPU semantics and independent verifier.** The new `cin.signature-batch/v0.1` (proposed) is a pure search helper, not an authority for `PASS`.
2. **Instrument first, then optimize CPU.** Only when H0/H1 profiling/trace equivalence justify it, design an optional SystemVerilog vector signature engine.
3. **Use a separate feature-gated backend** under `cin/accelerators/`; default CIN execution, genome, world, IR, archive and CLI semantics remain intact.
4. **Never change observational classes by unsigned/wrapping arithmetic.** Overflow or representability failure invokes exact CPU fallback before pruning. Known incorrect output aborts the run and quarantines hardware, not silent acceptance.
5. **Treat RTL-sim as a correctness tool, not a physical accelerator.** Hardware acceleration needs real board experiments against best optimized CPU including setup/transfer.
6. **Defer CIN-ISA and architecture tournament** until a useful net benchmark result and separate threat model. No autonomous RTL execution without OS-enforced isolation; no agent merges to production.

## Rejected choices

- Importing openTPU's MXU or entire ISA; CIN's present workload is not transformer matrix inference.
- Compiling arbitrary organism code as HDL or letting hardware perform private verifier/witness admission.
- Mandatory FPGA or HDL packages in existing Python CI.
- Distributing scheduler/governor work merely to support a device adapter.
- Tournament fitness based on ALU microbenchmarks or P&R estimates without full end-to-end CIN checks.
- Treating successful bounded formal properties as mathematical validity outside their assumptions.

## Consequences and revisit condition

Positive: backwards-compatible, testable, reversible, clear independent correctness and scientific accounting. Costs: interface maintenance, different integer representations, transport overhead, optional toolchain matrix, security work if autonomous agents are introduced.

**Revisit** after H0 profiles, H1 deterministic trace parity, H2 RTL tests/formal and H3 board evidence. Publish negative outcomes. A design-doc merge is not approval of device procurement, RTL implementation, agent execution or any scientific performance claim.
