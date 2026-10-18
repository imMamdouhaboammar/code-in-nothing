# H0 CPU baseline — exploratory GitHub Actions measurement

**Date of execution:** 2026-10-18 UTC  
**Status:** **EXPLORATORY / PARTIAL H0 evidence**; not a measured hardware speedup, H0 gate not closed.  
**Workflow run:** [CI #39167823020](https://github.com/imMamdouhaboammar/code-in-nothing/actions/runs/39167823020), Python 3.12 / Ubuntu job.  
**Source branch head:** `be2ee6c11aafc5a6eb80482a1c0cc5b8a25b50b4`.  
**Frozen manifest SHA-256:** `62cbc24901c2fd7997f1b86d355a246cf1f998ae17cf57215f74682bb4d4cfeb`.  
**Raw report:** GitHub Actions artifact `h0-cpu-profile-python312` (artifact ID `12150994041`, file `h0-profile.json`; download from the workflow's Artifacts section).  
**Runtime:** CPython 3.12.15, Linux `6.17.0-1022-azure-x86_64` GitHub-hosted runner.  
**Protocol:** `cin.hardware.h0.report/v0.1`; 3 **unprofiled** repeated measurements/workload, followed by a separate diagnostic cProfile run.

## Observed output, not a prediction

| Workload | Research status | Proposals seen | Median total wall ms | Median search-stage ms | Formal verification stage ms | Entire-search Amdahl ceiling* |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| MAX2 | UNKNOWN (budget 250) | 250 | 21.743 | 7.111 | 8.832 | 1.507× |
| MIN2 | PASS (budget 250) | 59 | 7.772 | 3.910 | 2.750 | 2.016× |
| ABSDIFF | UNKNOWN (budget 1,200) | 1,200 | 65.293 | 38.506 | 0.000 | 2.548× |
| Exhaustion MIN2 | UNKNOWN (budget 1) | 1 | 0.141 | 0.113 | 0.000 | 5.307× |
| Three-input probes | SEARCH_ONLY (80 proposals) | 80 | 3.666 | 2.956 | 0.000 | 7.289× |

**`PASS` on MIN2 means independently finite-verified against the declared world, not universally proved or measured hardware performance.** MAX2 and ABSDIFF did not find a passing solution *within these specific frozen pilot budgets*. The 3-input entry evaluates search probes, not a formal 3-input world.

*The reported Amdahl value uses **all of the existing search stage** as an idealized eliminable component: `full_wall / (full_wall - search_wall)`, based on sums across the three unprofiled repetitions (not the ratio of the displayed medians). This is much broader than actual offload-eligible vector arithmetic. It ignores transport, initialization, FPGA execution, data packing, host synchronization and retained search generation, so is **not** an estimate of real accelerator speedup. Tiny 0.14-ms exhaustion runs have very high timing noise and are not useful for FPGA selection.*

## Accounting and diagnostic limits

- Unprofiled logical counters were repeatable within each workload: e.g. MAX2 attempted 1,109 intermediate shapes and 54,635 probe evaluations; MIN2 attempted 832 shapes and 41,062 probes; ABSDIFF attempted 6,060 shapes and 297,234 probes.
- The separate, instrumented cProfile pass recorded composition generator-expression *self-time* (diagnostic only): MAX2 4.350 ms; MIN2 3.228 ms; ABSDIFF 23.431 ms; exhaustion 0 ms; 3-input search 1.898 ms. **These instrumented times must not be divided by unprofiled full-run totals to infer eligible fraction.**
- The total search stage includes AST composition, Python scheduling, structure creation, signature handling and dedup; tuple allocation, hashing and dispatch are not independently and completely attributable in this version of the profiler. No direct byte-transfer model exists yet.
- World admission, archive costs, a no-pruning matched control, FPGA performance, energy, peak memory, compiler/setup time for an FPGA and profiler overhead calibration are **NOT_RUN / UNRESOLVED**. A SHA-256 trace is reproducibility evidence, not proof of functional equivalence outside search probes.
- The CI virtual machine can be noisy and is not a pinned physical performance platform; these repetitions are an exploratory pilot, not a preregistered confirmatory speedup study.

## Engineering verification observed

The above workflow completed with Ruff lint/format success, six Python 3.11–3.13 macOS/Ubuntu test jobs successful, and CodeQL succeeded for the specified head. Existing M1 synthesis control and CLI baseline jobs were exercised under the unchanged CI matrix.

## Gate decision and next falsifier

**H0: INCONCLUSIVE / PENDING PROFILING REVIEW.** The measurements establish *where wall time is spent*, but **do not establish** what fraction the proposed RTL vector unit can physically accelerate. The idealized whole-search bound exceeding 1.5× on some workloads is necessary but far from sufficient.

Before an H1 or hardware investment GO decision, design a source-faithful, measured signature-only cost instrument (or a task-controlled CPU batch comparison) with explicit tuple/dispatch effects, profile overhead calibration, fixed hardware transfer assumptions, a much larger realistic workload, and paired controls. Reproduce on a declared machine. If even the resulting realistic upper bound cannot cross the preregistered 1.5× total-speed target, close the hardware offload track with a **NO-GO** result. Do not rewrite these pilot measurements.
