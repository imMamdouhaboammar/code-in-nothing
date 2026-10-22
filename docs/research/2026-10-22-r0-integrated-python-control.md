# R0 integrated pure-Python composition control v0.2

Current status: **PREREGISTERED BEFORE MEASUREMENT; EXPLORATORY RUN COMPLETED 2026-10-22; R0 STILL OPEN**. The original preregistration commit recorded the premeasurement status; its history remains intact. Research continuation of Issue #12 after the partial R0 v0.1 reference. This is not a Rust experiment or a native GO decision.

## Question and competing explanations

Does constructing signature tuples from a list comprehension instead of a generator expression reduce the wall time of a *complete* bounded search, screening and finite-world verification run, while producing byte-identical candidate traces and matching all logical costs?

- H1: list materialization reduces signature overhead enough to yield a measurable matched end-to-end gain.
- H0/alternative: the gain vanishes under AST/dedup/search/screen/verification overhead, or varies with workload/host noise. It may also regress memory or runtime.
- Irrespective of timing, any differing candidate order, trace, counter, verdict or stop reason **fails the control**. No native decision follows from these data.

## Frozen comparison before measurement

Manifest: [`native-python-control.v0.2.json`](../../experiments/native-python-control.v0.2.json). Source reference: public main after PR #13 at `f48b68f8d18f59515d88c87c0fa59ec7651a553f`. The local R0 worktree started from `8349c88ed498662eb4fd8f72784fdf910bcb181a`, whose relevant corrected R0 files match the published PR #13 files; public main also includes the independent PR #11 documentation. The comparison protocol and test implementation are committed before first research timings. The v0.1 manifest, reports, raw gzip, fixtures and H0 historical results stay untouched.

Preregistration erratum: the first protocol commit `fa7702b` recorded local-only SHA `8349c88`. Before collecting comparison data, this follow-up amendment records the fetchable merged-main SHA `f48b68f`. The cells, hypotheses, pairing, thresholds and stop rules were not changed. Both commits preserve the chronology.

| Dimension | Preregistered choice |
| --- | --- |
| Arms | Default generator-to-tuple vs opt-in list-to-tuple composition; identical typed search and independent verifier |
| Seeds | 0, 1, 2, retaining both operator-order variants |
| Repetitions | 5 paired repetitions for each workload and seed, no adaptive stop and no omitted slow/failed measurements |
| Workloads | MAX2 (250), MIN2 (250), ABSDIFF (1,200), one-proposal exhaustion, three-input search-only at 80 and 3,000 |
| Unit | One matched workload/seed/repetition pair; both arms run sequentially in the same process |
| Ordering | Alternate which arm is first using parity of seed index plus repetition, fixed in advance |
| Controls | Same genome, world, task-independent probes, screen points, limits, proposals, versioned schema and verifier |
| Primary measure | Whole-workload wall nanoseconds, including generation, screening and world verification when applicable |
| Secondary measures | Whole-workload process CPU, search-stage wall, attempted shapes, probe/scalar work, screening and verifier work |
| Parity | Exact equality for trace SHA-256, candidate hash, final statuses, all logical counters and workload counts |
| Memory | **NOT MEASURED** per trial; inherited process-lifetime RSS from R0 v0.1 is not reused as trial-level evidence |
| Decision | `ITERATE_R0_NO_NATIVE_GO`, regardless of isolated speed differences |

Each arm retains every outcome, including `UNKNOWN` and `SEARCH_ONLY`. Report all paired samples, per-workload medians and limitations, not selected winners. Ratios are descriptive in a shared host, not independent replications or confirmatory inference. Five consecutive process measurements do not establish a p95, statistical power or general speedup claim. Uncontrolled machine load/CPU frequency, warm caches, GC and cross-arm interference remain confounders despite alternating order.

The optional control changes signature tuple construction only, including Add, Sub, LessThan, Equal and conditional If. It must not alter the search frontier, admission, training feedback, verifier, inherited artifacts or core CLI. Compatibility tests compare the default against the frozen R0 characterization fixture and compare both arms across negative, three-input and If cases.

## Stopping and data integrity

- Reject malformed manifests before measurement, including unrecognized arms, changed base workloads, booleans masquerading as integers and private world paths.
- Refuse output overwrite and invalid parent paths before work begins.
- Capture source/lock/workflow hashes and working-tree provenance before measurements.
- If paired outcomes differ, **stop without publishing a performance verdict**. Preserve diagnostic mismatch metadata; do not rewrite fixtures or silently drop the offending pair.
- Do not infer a native speedup from a Python materialization test. Native FFI/startup cost remains **NOT MEASURED**.
- No modification to historical artifacts, no overwrite of runs, no retesting on selectively chosen seeds.

## Remaining gates

Independent allocation/tuple/dedup attribution, isolated per-trial peak RSS, genuinely compute-heavy end-to-end conditions and controlled-host confirmation are subsequent R0 tasks. The optional Rust R1 remains **BLOCKED** until the broader R0 decision gate is met.

## Reproduction commands (after implementation)

```bash
uv run --frozen --extra dev pytest -q
uv run --frozen --extra dev python -m cin validate
uv run --frozen --extra dev ruff check .
uv run --frozen --extra dev ruff format --check .
uv run --frozen --extra dev python -m experiments.native_python_control --output runs/new-r0-python-control.json
```

The output directory must exist and the target file must not. The final results section will distinguish raw observations from interpretation and disclose exact host/runtime provenance and any failed checks.

## Exploratory measurements

At preregistration: **NOT RUN**. The following measurements were collected afterward, from clean local commit `386fbda24ac409c6784bf776b84b24dcc9956bc1` on 2026-10-22.

Raw evidence: [`r0-python-control-20261022.json.gz`](../../experiments/native/r0-python-control-20261022.json.gz), a 13,905-byte deterministic gzip of the complete 276,341-byte JSON report.

- Compressed SHA-256: `cf1bdeaac09de4a36c2947c2ed367a99bd10d217dbf660ee6fd721e7b492baa9`.
- Decompressed SHA-256: `5ab63c20452010e45cc5fb54ff9ff305524e0fec73adab74b81edfe5481f0542`.
- Manifest SHA-256: `fd777dbbb3140fe41149acc8a8045e8c92c35163201514c7f6cba09c2aad4828`.
- Host: Linux x86_64, Python 3.12.14, Intel Xeon Platinum 8573C, 9 visible logical CPUs, shared host with uncontrolled load.
- 90 matched pairs (180 arm runs), 15 pairs per workload. All pairs retained exact candidate hashes/traces, logical counters, verdict scopes and screening/verification work. First arm: generator 48 times, list 42 times.

The ratio below is the median of paired generator/list **whole-workload wall-time** ratios: above 1 means list materialization was faster within those pairs. It is descriptive, not an independent effect estimate.

| Workload | Reference verdict | Median paired ratio | Observation |
| --- | --- | ---: | --- |
| MAX2 | UNKNOWN | 0.973 | Slightly slower list arm |
| MIN2 | PASS (finite world) | 1.118 | Slightly faster list arm |
| ABSDIFF | UNKNOWN | 1.088 | Slightly faster list arm |
| One-proposal exhaustion | UNKNOWN | 0.911 | Slower list arm |
| Three-input search (80) | SEARCH_ONLY | 1.131 | Faster list arm, no world verification |
| Three-input search (3,000) | SEARCH_ONLY | 1.105 | Faster list arm, no world verification |

The isolated v0.1 composition ratios around 1.5–1.65 did **not** translate to that scale of complete H0 workload improvement. These paired H0 runs cover search, screening and independent finite verification where applicable, but **not** full organism lifecycle, archive, admission, B0/B1/B2 training or native interop. The reference branch now includes experimental mode dispatch, so these are two arms within the same modified harness, not timing of a byte-identical prior binary. The shared host was uncontrolled, same-process samples are correlated, there is no per-trial isolated RSS, and 5 repetitions per seed do not justify p95 or statistical significance. The small ratios may be influenced by noise and order effects.

**Decision: `ITERATE_R0_NO_NATIVE_GO`.** This run supports no Rust speedup or mandatory change to Python search. Default generator behavior remains in place; other R0 gates listed above remain open. The execution SHA is a local commit: if GitHub publication creates a different commit identity, preserve this raw report and compare published source trees before claiming provenance equivalence.

### Post-measurement review hardening

The public preregistration, erratum and implementation commits retain the research sequence. The published implementation commit `f5e422206236882f47c300d850a73b64409fa442` has the same source tree for the measured Python files as local execution commit `386fbda`. Later PR review fixes leave the frozen protocol, default generator behavior and recorded successful samples unchanged.

If a future paired run detects a logical mismatch, the CLI now writes an `INVALID` report to its requested fresh output path before returning exit code 2. That artifact includes all previously completed pairs, both samples of the offending pair and the differing logical field names, with no summary or performance verdict. This failure-preservation behavior was added after the measurements above, in response to PR review; it does not retroactively change the retained raw evidence.
