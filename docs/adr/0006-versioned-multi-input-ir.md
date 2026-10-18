# ADR 0006: Opt-in, versioned multi-input IR

**Status:** Implementation proposed in [PR #2](https://github.com/imMamdouhaboammar/code-in-nothing/pull/2), subject to CI and review.

## Decision

Keep the five exact genome genes and the existing data-only Int/Bool expression grammar. A new `cin.genome/v0.2` schema selects IR `0.2` and allows 1–8 `Int` parameters with an `Int` result. The version 0.1 schema and its two-argument meaning remain frozen. The argument count comes from `base.input_types`, not the benchmark name.

The same bounded interpreter handles every arity through `run_ir_args(node, arguments)`; the old `run_ir(node, x, y, limits, ops_counter)` delegates without altering its signature. The typed static validator rejects out-of-range indexes and unsupported signatures; the interpreter independently rejects missing arguments, boolean-as-integer inputs, invalid argument nodes, and bitwidth violations. Readable source export is derived from validated arity and remains non-executable in the CIN verifier.

## Alternatives

- **Add a hardcoded third variable:** rejected because it duplicates argument handling and breaks signature generality.
- **Rewrite the whole interpreter and existing v0.1 contracts:** rejected because it risks changing archived semantics and growth evidence.
- **Opt-in versioned interface (chosen):** additive and scoped, with an explicit legacy path.

## Verification boundary and remaining gates

This PR is **not the complete M2 gate**. It includes task-independent arity-derived candidate enumeration with bounded heuristic probes, but does not implement the v0.3 world DSL, independent three-input world verification, median3/clamp discovery, cross-task transfer, or an SMT proof. A new signature alone is not discovery. Existing finite proofs apply only to their declared two-input worlds. Before claiming M2, add versioned multi-input world admission and verification, then run independently verified, budgeted median3/clamp synthesis and publish the negative outcomes as well as successes. Probe vectors establish search deduplication only, never mathematical equivalence. The old two-input 49-point probes are intentionally unchanged.
