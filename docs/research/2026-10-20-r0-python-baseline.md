# R0 Python baseline protocol v0.1

Status: **PARTIAL R0**, exploratory measurement protocol for Issue #12. No Rust implementation or native GO is authorized by these measurements.

## Frozen experiment

Manifest: [`experiments/native-baseline.v0.1.json`](../../experiments/native-baseline.v0.1.json). Reference: `934cd06bd36d7e79121fdcd36d4217fb15064a35`. The manifest and protocol are committed before the first timing run. Historical H0 artifacts remain unchanged.

| Dimension | Fixed choice |
| --- | --- |
| Seeds | 0, 1, 2; both search operator orders represented |
| Repetitions | Five uninstrumented measurements per cell; no adaptive stopping or discarded slow runs |
| Search workloads | MAX2 250, MIN2 250, ABSDIFF 1200, one-proposal exhaustion, three-input search at 80 and 3000 proposals |
| Guided controls | Existing B0/B1/B2, three two-input worlds, 250 proposals, identical existing governor limits |
| Guided order | Cyclic arm rotation by repetition; no claim of randomized independent trials |
| Public training panel | Existing five public cases; independent verifier unchanged |
| Composition control | Twelve candidate signatures on 49 task-independent search probes; generator-to-tuple versus list-to-tuple; Add/Sub/LessThan/Equal; 100 iterations per sample |
| Paired order | Alternate generator/list order by repetition; exact observation agreement required |
| Decision | ITERATE R0; microbenchmark gains never grant native GO |

## Metrics and boundaries

Uninstrumented wall and process CPU timings are primary observations. cProfile runs separately for attribution; its overhead is unsuitable for Python/native timing comparisons. H0 reports search, screening, verification, candidate hashes and trace digests, attempted shapes, scalar probes and verifier operations. Guided raw records preserve full candidate order, fitness traces, per-dimension governor costs, stop reasons and finite verification scope. Counters are separate dimensions, not additive calibrated compute.

RSS is the current process's lifetime high-water mark, in bytes where supported. It is **not** per-workload isolated peak memory. Shared-host load, CPU frequency, allocator state and caches are uncontrolled. Five same-process repetitions do not establish statistical power, independent research replication, p95 tails or cross-machine generality. The report records this uncertainty and makes no speedup claim.

The pure-Python comparison isolates exact signature arithmetic/data-shape cost. It does not replace production search, compare full experiments, cover If composition, or measure FFI. Its input corpus and output observations are hashed. Python arbitrary-size integers and Bool/Int distinctions remain exact. A later integrated control needs byte/order/counter parity and matched end-to-end measurements.

Candidate/order/hash/public-probe/counter fixtures were captured from the untouched reference checkout, independently of the new harness. Additional fixed normalized journal digest and inheritance checks freeze the existing 63-evaluation MAX2 lifecycle; only the archive's existing CPU normalization applies. Existing IR, verifier, governor, replay and guided tests remain authoritative regression coverage.

## Preregistered follow-on decision

Candidate hypothesis: batching `cin/search.py` observational signature composition might reduce time spent in tuple construction and arithmetic. The alternative is that AST construction, hashing, verification or orchestration dominate, or that a small Python data-shape change removes enough cost to make native packaging unjustified.

Before a native GO, require an integrated improved-Python control, precise signature/tuple/dedup allocation attribution, a compute-heavy end-to-end workload, per-cell controlled-host repetitions and zero unexplained semantic divergence. Only then test the Issue #12 provisional target of at least 2x end-to-end improvement including conversion/startup. Less than 2x, noisy benefit or parity failure yields ITERATE/NO-GO, retaining Python. The present microbenchmark cannot decide this gate.

Remaining R0 gates: integrated improved-Python comparison; isolated allocation/dedup attribution; isolated per-trial peak RSS; controlled-host confirmatory measurements. R1 remains blocked. Native conversion is NOT MEASURED because there is no native implementation.

## Reproduction

```bash
uv sync --frozen --extra dev
uv run --frozen --extra dev python -m experiments.native_baseline --output runs/r0-baseline-new.json
uv run --frozen --extra dev pytest -q
uv run --frozen --extra dev python -m cin validate
uv run --frozen --extra dev ruff check .
uv run --frozen --extra dev ruff format --check .
```

The output path must be new and its parent must exist. Raw output includes the frozen manifest, Git execution SHA and dirty status, SHA-256 source/lock/workflow provenance, platform, interpreter, logical CPU count, complete measurement denominator and unfavorable/UNKNOWN runs.

## Exploratory run: 2026-10-20

Raw evidence: [`r0-20261020.json.gz`](../../experiments/native/r0-20261020.json.gz), standard gzip containing the complete JSON report. Decompressed SHA-256: `164200ea717bf39fb8e30fa1cb53ac7ed6c052f98e185f87ce7d6915e4bb0000`.

The run used Python 3.12.14 on Linux x86_64, nine visible logical CPUs and an uncontrolled shared host. Other verification work overlapped part of the run. The recorded processor string is only `x86_64`; the CPU model is unknown. These are exploratory observations, not controlled performance estimates.

| Measurement | Recorded denominator / outcome |
| --- | --- |
| Uninstrumented H0 samples | 90: six workloads, three seeds, five repetitions |
| Guided samples | 135: three worlds, three seeds, three arms, five repetitions |
| Guided finite-world verdicts | 90 PASS, 45 UNKNOWN; all retained |
| Paired composition samples | 20 pairs across four operations, with both timing arms retained |
| Native execution | NOT MEASURED |
| Decision | ITERATE_R0_NO_NATIVE_GO |

All repeated guided cells retained identical normalized logical outcomes. H0 retained its trace/counter checks. Search-only workloads remain SEARCH_ONLY, not verified multi-input worlds. PASS denotes only the declared finite-world scope and is not world admission or inherited organism capability.

List-to-tuple composition was faster in this isolated run, with median paired generator/list wall-time ratios of 1.50 for Add, 1.60 for Sub, 1.57 for LessThan and 1.65 for Equal. These ratios exclude integrated search, allocation attribution, verifier, archive and FFI costs; they do not establish an end-to-end gain or justify Rust.

The raw report records the clean local preregistration commit `dead7ccd7df0a327a014e74a7b4f75bbc0db0cba`. Publication through GitHub's API created commit `c29802d8783d927cc59e30392dc414bf7891ee3d` with the identical Git tree `0c25cf460c0df98ff079b70b4e529e74d024d24a`; commit metadata differs. The local protocol was committed before measurement; remote publication occurred afterward. Raw provenance was preserved without rewriting the execution SHA. Every recorded source, lock and workflow hash was checked against the published source tree.

Validation after the run: 128 tests passed (116 existing plus 12 new); contract validation, Ruff lint/format and diff whitespace checks passed. No existing tests, core runtime, dependency locks or historical evidence changed. The remaining R0 gates listed above are open; Issue #12 is not complete and R1 remains blocked.
