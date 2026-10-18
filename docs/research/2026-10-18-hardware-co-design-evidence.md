# CIN Hardware Co-Design — source-grounded evidence and experiment register

**Research date:** 2026-10-18. **Status:** SOURCE REVIEWED / HYPOTHESES NOT TESTED. This ledger is not runtime benchmarking.
**Baseline commits:** CIN `c414a4894b29af8497801dbae0bccc941a4e1230`, openTPU `f237dab2f196855a59a083b1454786df8f01291f`, auto-arch-tournament `4a137bb1378834ca3664a1c971684777eb5f364a`.
**Product design:** [CIN Hardware Co-Design](../superpowers/specs/2026-10-18-cin-hardware-co-design.md).

## 1. Evidence ledger

| ID | Observation and authoritative source | What it justifies | What it does NOT justify |
| --- | --- | --- | --- |
| E01 | [CIN `cin/search.py`](https://github.com/imMamdouhaboammar/code-in-nothing/blob/c414a4894b29af8497801dbae0bccc941a4e1230/cin/search.py): task-independent probe vectors, arithmetic comparison/selection, cost-layered enumeration and `SearchStats` | Signature-vector operations are a real potential backend boundary | That they currently dominate total search time, or parallel offload saves time |
| E02 | [CIN `cin/ir.py`](https://github.com/imMamdouhaboammar/code-in-nothing/blob/c414a4894b29af8497801dbae0bccc941a4e1230/cin/ir.py): signed Python values, bounded `Limits`, lazy `If` | Offload must preserve exact data/error semantics and distinguish search from interpreter | That fixed-width RTL is drop-in identical |
| E03 | [CIN `cin/worlds.py`](https://github.com/imMamdouhaboammar/code-in-nothing/blob/c414a4894b29af8497801dbae0bccc941a4e1230/cin/worlds.py): independent finite-domain verifier and private witness admission | Keep hardware outside trusted correctness gate | That hardware signature equality proves a world |
| E04 | [openTPU ISA](https://github.com/FeSens/openTPU/blob/f237dab2f196855a59a083b1454786df8f01291f/docs/isa.md) and [as-built design](https://github.com/FeSens/openTPU/blob/f237dab2f196855a59a083b1454786df8f01291f/docs/superpowers/specs/2026-09-23-opentpu-design.md): explicit compiler/simulator/RTL bit-exact contract, layer-wise test structure | Design independent CPU reference, RTL differential tests and measurable host/device boundary | That CIN needs openTPU's MXU, DMA, LLM kernels or numeric fp32 ISA |
| E05 | [openTPU README](https://github.com/FeSens/openTPU/blob/f237dab2f196855a59a083b1454786df8f01291f/README.md): author-reported physical Kintex-7 inference and bit-for-bit simulator comparisons | Actual board measurements matter; simulation alone is not enough | Independent replication, CIN throughput, or suitability of that board for CIN |
| E06 | [auto-arch-tournament README](https://github.com/FeSens/auto-arch-tournament/blob/4a137bb1378834ca3664a1c971684777eb5f364a/README.md) and [I/O contract](https://github.com/FeSens/auto-arch-tournament/blob/4a137bb1378834ca3664a1c971684777eb5f364a/ARCHITECTURE.md): candidate hypothesis, worktree, gate, 3-seed P&R, champion comparison | Gated architecture experiments and immutable test reference | That its CoreMark/MHz is a correct CIN search objective |
| E07 | [Tournament methodology](https://github.com/FeSens/auto-arch-tournament/blob/4a137bb1378834ca3664a1c971684777eb5f364a/BENCH_METHODOLOGY.md) and [hard invariants](https://github.com/FeSens/auto-arch-tournament/blob/4a137bb1378834ca3664a1c971684777eb5f364a/CLAUDE.md): outcome taxonomy, static control, paired comparisons, off-limits evaluator, known ALTOPS weakening | Need explicit non-vacuous formal scope, security boundary and matched controls | Full arithmetic proofs from the loop's ALTOPS-mode verification |
| E08 | [Verilator docs](https://verilator.org/guide/latest/), [cocotb 2.1 runner](https://docs.cocotb.org/en/v2.1.0/library_reference.html), [Yosys](https://github.com/YosysHQ/yosys), [SBY](https://symbiyosys.readthedocs.io/en/latest/verilog.html) | Plausible open-source simulation, RTL unit test, synthesis and bounded formal toolchain | That these are installed, version-pinned, compatible with an unspecified FPGA or sufficient for exhaustive hardware security |
| E09 | [CIN Not Broke Rules](../architecture/NOT-BROKE-RULES.md) and [ADR 0003](../adr/0003-single-process-first.md) | No generated host code; bounded scoped correctness; single process first | Permission to move independent verification into generated RTL |

**Source acquisition:** GitHub source files read via the connected GitHub service; independent discovery and ecosystem checks via Parallel Search plugin. File-specific GitHub commit refs above are pinned to the source state, not perpetually current projects.

## 2. Unresolved research questions and falsifiers (frozen before H0 measurements)

| Hypothesis | Prediction to test | Falsifier / failure criterion | Status |
| --- | --- | --- | --- |
| HYP-A: signature operations dominate | Frozen profile shows eligible signature cost large enough for prospective whole-run win | Even infinitely fast signature work cannot reach the predefined end-to-end target by Amdahl bound; after reasonable transport estimate, benefit vanishes | UNTESTED |
| HYP-B: CPU batching is cost-effective | Same ordered signature/proposal/verdict traces, reduced host overhead vs original scalar | Parity changes; CPU vectorization slower or not worth maintenance under full run | UNTESTED |
| HYP-C: RTL/FPGA offload helps real CIN | Board-based, transport-inclusive, repeated frozen runs ≥1.5× median full-search speedup vs best valid CPU baseline | No reliable full-system benefit, data-copy dominated, mismatch or device instability | UNTESTED |
| HYP-D: RTL tournament yields robust eligible designs | Several candidate architectures evaluated under immutable correct gates and same workload; a champion improves past declared noise and constraints | No eligible positive improvements, incomplete formal/OS isolation, benchmark leakage, fabricated fitness | UNTESTED |

**Pre-registration protocol:** H0 creates immutable, versioned input manifests and tags exploratory vs confirmatory runs *before* results; future threshold changes are new experiments, not edits to the original decision. Negative/inconclusive runs stay in evidence. A self-reported result never becomes an independently confirmed CIN outcome.

## 3. Decisions and limitations

- **SELECT:** signature-vector backend and CPU-first baseline; smallest semantic surface and rollback-friendly.
- **DEFER:** physical FPGA until H0/H1/H2; H4 full candidate interpreter until real acceleration case; H5 agent tournament until OS-enforced isolation.
- **REJECT NOW:** FPGA as formal verifier, external LLM as a CIN gene, adopting openTPU's matrix compute, using token/s or CoreMark as CIN program-synthesis fitness, auto-merging unreviewed RTL.
- **OPEN:** exact board, driver, EDA toolchain versions, cost profile, FPGA data-movement strategy, physical timing/power budgets, hardware scheduling policy. These require measured data and separate scope approvals.
- **KNOWN LIMIT:** Python signature arithmetic can exceed RTL width; lazy candidate-IR `If` is not the same as eagerly composed signatures; finite probes may conflate different programs; future multi-input worlds are not implied by IR arity.
- **SECURITY LIMIT:** allowed file paths and git worktrees are not OS-level isolation. Untrusted agent actions and third-party tools need separate threat modeling.
- **VERDICT:** The cited repos support a credible *design methodology*. No experimental evidence yet confirms that CIN benefits from Verilog or that an architecture tournament improves its scientific outcomes.

## 4. How to close the research

The first H0 implementation PR must publish frozen hypotheses, exact commands and tool versions, per-workload run data, failure/exhaustion counts, experiment deviations, reproducible code/manifest hashes, and an independent evidence review. If the measured CPU-only Amdahl bound defeats HYP-A, close the hardware speedup track without inventing hardware justification. The design remains available as research.
