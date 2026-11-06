"""Adversarial Benchmark & Epistemic Integrity Harness for Code-In-Nothing.

Strictly enforces the Epistemic Integrity & Anti-Embellishment Protocol (AGENTS.md Section 8 / CLAUDE.md):
1. Zero Hype & Lexical Discipline.
2. Full-Cost Accounting (Anti-Metric Gaming):
   - Primitive sub-expressions and predicates.
   - Evaluator probe executions.
   - Auxiliary work (entropy calculations, interval steps, anti-unification).
   - Verifier invocations and verification runtime.
   - Wall-clock time (ms) and peak RSS memory.
3. Zero-Omission Reporting:
   - All 5 example worlds evaluated with explicit TIMEOUT/FAILED states.
4. Anti-Curriculum Leakage & Distractor Stress Testing:
   - 20 distractor macros injected.
   - High-arity tasks (5 and 8 inputs).
5. Mathematical & Soundness Disclosure:
   - Arithmetic-over-conditionals failure boundary.
   - Non-integral polyhedra (dark shadows / rational vs integer gap).
6. Mandatory Milestone Report Schema:
   - Output strictly in 5 sections in Arabic.
"""

from __future__ import annotations

import hashlib
import math
import random
import resource
import signal
import stat
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from cin.contracts import load_genome, load_world
from cin.ir import Limits, canonical_hash
from cin.synthesis.decision import (
    SynthesisWork,
    _size_depth,
    generate_candidate_predicates,
    generate_candidate_subterms,
    synthesize_conditional_tree,
)
from cin.synthesis.deductive import Interval
from cin.synthesis.library import Macro, MacroRegistry
from cin.worlds import verify_program

ROOT = Path(__file__).resolve().parent.parent


def get_peak_rss_kb() -> float:
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform == "darwin":
        return raw / 1024.0
    return float(raw)


def _benchmark_manifest_entries() -> list[tuple[str, str, Path]]:
    checksum_file = ROOT / ".benchmarks" / "checksums.sha256"
    if not checksum_file.is_file():
        raise RuntimeError("Missing cryptographic manifest: .benchmarks/checksums.sha256")

    root = ROOT.resolve()
    entries = []
    for line in checksum_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected_hash, rel_path = line.split(maxsplit=1)
        target_path = (ROOT / rel_path).resolve()
        if not target_path.is_relative_to(root):
            raise RuntimeError(f"Benchmark path escapes repository: {rel_path}")
        if not target_path.is_file():
            raise RuntimeError(f"Missing benchmark file: {rel_path}")
        entries.append((expected_hash, rel_path, target_path))
    return entries


def _check_benchmark_hash(expected_hash: str, rel_path: str, target_path: Path) -> None:
    actual_hash = hashlib.sha256(target_path.read_bytes()).hexdigest()
    if actual_hash != expected_hash:
        raise ValueError(
            f"TAMPERING_DETECTED: Hash mismatch for {rel_path}!\n"
            f"Expected: {expected_hash}\nActual:   {actual_hash}"
        )


def prepare_benchmark_write_locks() -> None:
    """Explicit one-time setup for freshly checked-out benchmark inputs."""
    entries = _benchmark_manifest_entries()
    # Reject altered contents before changing any file permissions.
    for expected_hash, rel_path, target_path in entries:
        _check_benchmark_hash(expected_hash, rel_path, target_path)
    for _, _, target_path in entries:
        target_path.chmod(stat.S_IMODE(target_path.stat().st_mode) & ~0o222)


def verify_filesystem_integrity() -> None:
    for expected_hash, rel_path, target_path in _benchmark_manifest_entries():
        if stat.S_IMODE(target_path.stat().st_mode) & 0o222:
            raise PermissionError(
                f"INTEGRITY_BREACH: File {rel_path} has write permissions! "
                "Run 'python -m experiments.adversarial_harness --prepare-locks' "
                "after verifying the benchmark manifest."
            )
        _check_benchmark_hash(expected_hash, rel_path, target_path)


class TaskTimeout(Exception):
    pass


def _alarm_handler(signum, frame):
    raise TaskTimeout("PER_TASK_TIMEOUT_EXCEEDED")


@dataclass
class CostCounters:
    status: str = "UNKNOWN"
    primitive_subterms: int = 0
    primitive_predicates: int = 0
    probe_evaluations: int = 0
    auxiliary_scoring_steps: int = 0
    aux_interval_propagations: int = 0
    aux_anti_unifications: int = 0
    verifier_calls: int = 0
    verifier_time_ms: float = 0.0
    wall_clock_ms: float = 0.0
    peak_rss_kb: float = 0.0
    ast_nodes: int = 0
    ast_depth: int = 0
    failure_reason: str = ""


def instrumented_synthesize(
    world_dict: dict,
    base_genome: dict,
    *,
    macro_registry: MacroRegistry | None = None,
    timeout_sec: int = 4,
    force_naive_search: bool = False,
) -> tuple[dict | None, CostCounters]:
    counters = CostCounters()
    work = SynthesisWork()
    t_start = time.perf_counter()

    domain = world_dict.get("input_domain", {})
    arity = len(domain) if domain else len(world_dict.get("input_types", ("Int", "Int")))

    # Representative probe sample points for induction
    if arity == 2:
        cases = tuple((x, y) for x in (-4, -2, 0, 2, 4) for y in (-4, -2, 0, 2, 4))
    elif arity == 3:
        cases = (
            (-2, -1, 1),
            (0, -1, 1),
            (2, -1, 1),
            (-3, 0, 2),
            (1, 0, 2),
            (5, 0, 2),
            (0, 0, 0),
            (2, 2, 2),
            (-2, -2, -2),
        )
    else:
        cases = tuple(tuple((i + j) % 5 - 2 for j in range(arity)) for i in range(15))

    allowed = set(base_genome.get("allowed_primitives", []))
    constants = base_genome.get("allowed_constants", [0, 1])
    limits = Limits(
        max_depth=base_genome.get("max_ast_depth", 7),
        max_nodes=base_genome.get("max_ast_nodes", 25),
    )

    # Set POSIX alarm
    old_handler = signal.signal(signal.SIGALRM, _alarm_handler)
    signal.alarm(timeout_sec)

    try:
        if force_naive_search:
            from cin.search import candidate_stream

            parent = base_genome.get("starting_expression", {"op": "Arg", "index": 0})
            gen = candidate_stream(parent, base_genome, seed=0, max_proposals=400)
            solved_expr = None
            max_proposals = 400
            for _ in range(max_proposals):
                try:
                    cand = next(gen)
                except StopIteration:
                    break
                counters.primitive_subterms += 1
                t_v0 = time.perf_counter()
                verdict = verify_program(cand.expression, world_dict, base_genome)
                t_v1 = time.perf_counter()
                counters.verifier_calls += 1
                counters.verifier_time_ms += (t_v1 - t_v0) * 1000.0

                if verdict.status == "PASS":
                    solved_expr = cand.expression
                    counters.status = "PASS"
                    counters.ast_nodes, counters.ast_depth = _size_depth(solved_expr)
                    break
            if counters.status == "UNKNOWN":
                counters.status = "EXHAUSTED"
                counters.failure_reason = (
                    f"Exhausted search after {counters.primitive_subterms} evaluated proposals "
                    f"(cap {max_proposals}) without proof"
                )

            signal.alarm(0)
            counters.wall_clock_ms = (time.perf_counter() - t_start) * 1000.0
            counters.peak_rss_kb = get_peak_rss_kb()
            return solved_expr, counters

        # Information-Theoretic Branch Decoupling
        subterms = generate_candidate_subterms(
            arity,
            allowed,
            constants,
            cases,
            max_depth=3,
            limits=limits,
            macro_registry=macro_registry,
            work=work,
        )

        atomic_terms = [t for t in subterms if _size_depth(t)[1] <= 2]
        predicates = []
        if "If" in allowed:
            predicates = generate_candidate_predicates(
                atomic_terms,
                allowed,
                cases,
                arity,
                limits=limits,
                macro_registry=macro_registry,
                work=work,
            )

        res = synthesize_conditional_tree(
            cases,
            world_dict,
            base_genome,
            subterms=subterms,
            predicates=predicates,
            macro_registry=macro_registry,
            max_tree_depth=base_genome.get("max_ast_depth", 7),
            work=work,
        )

        signal.alarm(0)

        if res is None:
            counters.status = "FAILED"
            counters.failure_reason = "No covering decision tree found within depth bounds"
            counters.wall_clock_ms = (time.perf_counter() - t_start) * 1000.0
            counters.peak_rss_kb = get_peak_rss_kb()
            return None, counters

        # Verify candidate on the full independent world verifier
        t_v0 = time.perf_counter()
        verdict = verify_program(res.expression, world_dict, base_genome)
        t_v1 = time.perf_counter()
        counters.verifier_calls = 1
        counters.verifier_time_ms = (t_v1 - t_v0) * 1000.0

        if verdict.status == "PASS":
            counters.status = "PASS"
            counters.ast_nodes = res.nodes
            counters.ast_depth = res.depth
        else:
            counters.status = "FAILED"
            counters.failure_reason = f"Verifier returned {verdict.status}: {verdict.reason}"

        counters.wall_clock_ms = (time.perf_counter() - t_start) * 1000.0
        counters.peak_rss_kb = get_peak_rss_kb()
        return res.expression, counters

    except TaskTimeout:
        counters.status = "TIMEOUT"
        counters.failure_reason = f"Exceeded {timeout_sec}s timeout ceiling"
        counters.wall_clock_ms = (time.perf_counter() - t_start) * 1000.0
        counters.peak_rss_kb = get_peak_rss_kb()
        return None, counters
    except Exception as exc:
        signal.alarm(0)
        counters.status = "FAILED"
        counters.failure_reason = f"{type(exc).__name__}: {exc}"
        counters.wall_clock_ms = (time.perf_counter() - t_start) * 1000.0
        counters.peak_rss_kb = get_peak_rss_kb()
        return None, counters
    finally:
        if not force_naive_search:
            counters.primitive_subterms = work.primitive_subterms
            counters.primitive_predicates = work.primitive_predicates
            counters.probe_evaluations = work.probe_evaluations
            counters.auxiliary_scoring_steps = work.auxiliary_scoring_steps
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


def generate_20_distractor_macros() -> list[Macro]:
    distractors: list[Macro] = []
    m1 = {"op": "Add", "args": [{"op": "Arg", "index": 0}, {"op": "ConstInt", "value": 5}]}
    distractors.append(Macro("distract_add5", 1, m1, canonical_hash(m1)))

    m2 = {"op": "Sub", "args": [{"op": "Arg", "index": 0}, {"op": "ConstInt", "value": 7}]}
    distractors.append(Macro("distract_sub7", 1, m2, canonical_hash(m2)))

    m3 = {"op": "Add", "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 0}]}
    distractors.append(Macro("distract_double", 1, m3, canonical_hash(m3)))

    m4 = {"op": "Add", "args": [{"op": "Arg", "index": 0}, m3]}
    distractors.append(Macro("distract_triple", 1, m4, canonical_hash(m4)))

    m5 = {"op": "Add", "args": [{"op": "Arg", "index": 0}, {"op": "ConstInt", "value": 1}]}
    distractors.append(Macro("distract_add1", 1, m5, canonical_hash(m5)))

    m6 = {"op": "Sub", "args": [{"op": "Arg", "index": 0}, {"op": "ConstInt", "value": 1}]}
    distractors.append(Macro("distract_sub1", 1, m6, canonical_hash(m6)))

    m7 = {"op": "Add", "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 1}]}
    distractors.append(Macro("distract_add_pair", 2, m7, canonical_hash(m7)))

    m8 = {"op": "Sub", "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 1}]}
    distractors.append(Macro("distract_sub_pair", 2, m8, canonical_hash(m8)))

    m9 = {
        "op": "If",
        "args": [
            {"op": "Equal", "args": [{"op": "Arg", "index": 0}, {"op": "ConstInt", "value": 0}]},
            {"op": "ConstInt", "value": 1},
            {"op": "ConstInt", "value": 0},
        ],
    }
    distractors.append(Macro("distract_if_zero", 1, m9, canonical_hash(m9)))

    m10 = {
        "op": "If",
        "args": [
            {"op": "LessThan", "args": [{"op": "ConstInt", "value": 0}, {"op": "Arg", "index": 0}]},
            {"op": "ConstInt", "value": 1},
            {"op": "ConstInt", "value": 0},
        ],
    }
    distractors.append(Macro("distract_if_pos", 1, m10, canonical_hash(m10)))

    for k in range(11, 21):
        mk = {
            "op": "Add",
            "args": [
                {"op": "Arg", "index": 0},
                {"op": "ConstInt", "value": k},
            ],
        }
        distractors.append(Macro(f"distract_const_{k}", 1, mk, canonical_hash(mk)))

    return distractors


def make_high_arity_cases(arity: int, count: int = 32) -> tuple[tuple[int, ...], ...]:
    """Use deterministic independent-axis probes instead of identical columns."""
    rng = random.Random(6000 + arity)
    return tuple(tuple(rng.randint(-3, 3) for _ in range(arity)) for _ in range(count))


def run_full_adversarial_evaluation() -> None:
    verify_filesystem_integrity()

    genome_v1 = load_genome("examples/seed-genome.v0.1.yaml")
    base_2d = dict(genome_v1["genome"]["base"])
    base_2d["max_ast_depth"] = 7
    base_2d["max_ast_nodes"] = 25

    base_3d = dict(base_2d)
    base_3d["cin_ir_version"] = "0.2"
    base_3d["input_types"] = ["Int", "Int", "Int"]
    base_3d["max_ast_depth"] = 8
    base_3d["max_ast_nodes"] = 32

    # Canonical registered tasks
    registered_tasks = [
        ("world-max2.v0.1.yaml", base_2d),
        ("world-min2.v0.1.yaml", base_2d),
        ("world-absdiff.v0.2.yaml", base_2d),
        ("world-clamp3.v0.3.yaml", base_3d),
        ("world-median3.v0.3.yaml", base_3d),
    ]

    max2_ir = {
        "op": "If",
        "args": [
            {"op": "LessThan", "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 1}]},
            {"op": "Arg", "index": 1},
            {"op": "Arg", "index": 0},
        ],
    }
    min2_ir = {
        "op": "If",
        "args": [
            {"op": "LessThan", "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 1}]},
            {"op": "Arg", "index": 0},
            {"op": "Arg", "index": 1},
        ],
    }
    macro_reg = MacroRegistry()
    macro_reg.register(Macro("max2", 2, max2_ir, canonical_hash(max2_ir)))
    macro_reg.register(Macro("min2", 2, min2_ir, canonical_hash(min2_ir)))

    matrix_results: list[tuple[str, CostCounters]] = []
    for task_file, base in registered_tasks:
        w_path = ROOT / "examples" / task_file
        world = load_world(str(w_path))
        reg = macro_reg if "3" in task_file else None
        _, counters = instrumented_synthesize(world, base, macro_registry=reg, timeout_sec=4)
        matrix_results.append((task_file, counters))

    # Isolated Ablation (Decision Tree ON vs OFF on 2D tasks)
    ablation_results: list[tuple[str, CostCounters, CostCounters]] = []
    for task_file, base in registered_tasks[:3]:
        w_path = ROOT / "examples" / task_file
        world = load_world(str(w_path))
        _, on_cost = instrumented_synthesize(world, base, force_naive_search=False, timeout_sec=4)
        _, off_cost = instrumented_synthesize(world, base, force_naive_search=True, timeout_sec=2)
        ablation_results.append((task_file, off_cost, on_cost))

    # Distractor Stress Test: 20 Unrelated Macros injected
    distractor_reg = MacroRegistry()
    for d in generate_20_distractor_macros():
        distractor_reg.register(d)
    distractor_reg.register(Macro("max2", 2, max2_ir, canonical_hash(max2_ir)))
    distractor_reg.register(Macro("min2", 2, min2_ir, canonical_hash(min2_ir)))

    w_clamp = load_world(str(ROOT / "examples" / "world-clamp3.v0.3.yaml"))
    _, clean_clamp = instrumented_synthesize(
        w_clamp, base_3d, macro_registry=macro_reg, timeout_sec=4
    )
    _, distract_clamp = instrumented_synthesize(
        w_clamp, base_3d, macro_registry=distractor_reg, timeout_sec=4
    )

    # High-Arity Tasks (5 and 8 inputs) with strict 3-second timeout
    def test_high_arity(arity: int, timeout: int = 3) -> CostCounters:
        base_hd = dict(base_2d)
        base_hd["cin_ir_version"] = "0.2"
        base_hd["input_types"] = ["Int"] * arity
        base_hd["max_ast_depth"] = 8
        base_hd["max_ast_nodes"] = 40
        cases_hd = make_high_arity_cases(arity)
        target_hd = tuple(sum(pt) for pt in cases_hd)
        c = CostCounters()
        work = SynthesisWork()
        t0 = time.perf_counter()

        old_h = signal.signal(signal.SIGALRM, _alarm_handler)
        signal.alarm(timeout)
        try:
            res = synthesize_conditional_tree(
                cases_hd, target_hd, base_hd, max_tree_depth=6, work=work
            )
            signal.alarm(0)
            if res:
                c.status = "PASS"
                c.ast_nodes = res.nodes
                c.ast_depth = res.depth
            else:
                c.status = "EXHAUSTED"
                c.failure_reason = "No covering expression found within depth and search bounds"
        except TaskTimeout:
            c.status = "TIMEOUT"
            c.failure_reason = f"Combinatorial tree explosion exceeded {timeout}s"
        except Exception as exc:
            signal.alarm(0)
            c.status = "FAILED"
            c.failure_reason = str(exc)
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_h)

        c.primitive_subterms = work.primitive_subterms
        c.primitive_predicates = work.primitive_predicates
        c.probe_evaluations = work.probe_evaluations
        c.auxiliary_scoring_steps = work.auxiliary_scoring_steps
        c.wall_clock_ms = (time.perf_counter() - t0) * 1000.0
        c.peak_rss_kb = get_peak_rss_kb()
        return c

    cost_arity5 = test_high_arity(5, timeout=3)
    cost_arity8 = test_high_arity(8, timeout=3)

    # Adversarial Falsification:
    # A) Arithmetic-over-Conditionals: f(x, y) = 3 * If(x < y, x, y) + 7 * If(x == y, 2, 0)
    cases_2d = tuple((x, y) for x in range(-2, 3) for y in range(-2, 3))
    target_arith_cond = tuple(
        (3 * (x if x < y else y)) + (7 * (2 if x == y else 0)) for x, y in cases_2d
    )
    t_break0 = time.perf_counter()
    res_break = synthesize_conditional_tree(cases_2d, target_arith_cond, base_2d, max_tree_depth=5)
    t_break_ms = (time.perf_counter() - t_break0) * 1000.0

    # B) Non-Integral Polyhedron (Dark Shadow Gap): 2x + 4y = 1
    int_x = Interval(-10, 10)
    int_y = Interval(-10, 10)
    rational_feasible = (
        (2 * int_x.min_val + 4 * int_y.min_val) <= 1 <= (2 * int_x.max_val + 4 * int_y.max_val)
    )
    has_integer_solutions = math.gcd(2, 4) == 1

    # Print strictly according to Section 7 Schema
    print("## 1. الآلية والتعقيد الحسابي (Mechanism & Complexity)")
    print(
        "- **الملفات المعدلة والمحققة**: `cin/synthesis/decision.py`, `cin/synthesis/library.py`, `cin/synthesis/deductive.py`."
    )
    print(
        "- **الخوارزمية المطبقة**: توليد تعبيرات الشروط وفصل فروع البيانات عبر تقسيم الإنتروبيا (Information-Theoretic Branch Decoupling عبر ID3) مع تقييد المجالات (Interval Propagation) وحقن تجريدات الماكرو الوراثية (Hereditary Anti-Unification)."
    )
    print("- **التعقيد النظري لأسوأ حالة (Worst-case Complexity)**:")
    print(
        "  - الزمن: $O(|P| \\cdot |\\text{cases}| + |S| \\cdot |\\text{cases}| + b^D)$ حيث $|P|$ عدد المحمولات، $|S|$ بنك التعبيرات الأولية، و $D$ عمق شجرة القرار."
    )
    print("  - المساحة: $O(|S| + |P| + |\\text{cases}|)$ لتخزين بصمات المسابر ومجموعات التغطية.")
    print(
        "- **حدود النطاق الحسابي**: التحقق محصور في فترات عددية صحيحة محدودة $\\mathbb{Z} \\cap [\\min, \\max]$ ولا يمتد تلقائياً للاستقراء غير المحدود دون برهان SMT/Z3 مستقل.\n"
    )

    print("## 2. مصفوفة الاختبارات المعيارية الكاملة (Complete Benchmark Matrix)")
    print(
        "| Task Specification | Status | Subterms + Preds | Probe Evals | Aux Work | Verifier Calls (Time) | Wall Clock (ms) | Peak RSS (KB) |"
    )
    print("|---|---|---|---|---|---|---|---|")
    for task_name, c in matrix_results:
        v_str = (
            f"{c.verifier_calls} ({c.verifier_time_ms:.1f}ms)" if c.verifier_calls else "0 (0ms)"
        )
        print(
            f"| `{task_name}` | **{c.status}** | {c.primitive_subterms + c.primitive_predicates} | {c.probe_evaluations} | {c.auxiliary_scoring_steps} | {v_str} | {c.wall_clock_ms:.2f} | {c.peak_rss_kb:.1f} |"
        )
    print()

    print("## 3. دراسة الاجتثاث المستقلة (Isolated Ablation)")
    print(
        "| Task | Module OFF (Naive Enumeration) | Module ON (Branch Decoupling) | Speedup / Reduction |"
    )
    print("|---|---|---|---|")
    for task_name, off_c, on_c in ablation_results:
        off_summary = (
            f"{off_c.status} ({off_c.wall_clock_ms:.1f}ms, {off_c.primitive_subterms} shapes)"
        )
        on_summary = f"{on_c.status} ({on_c.wall_clock_ms:.1f}ms, {on_c.probe_evaluations} evals)"
        ratio = (
            f"{off_c.wall_clock_ms / max(on_c.wall_clock_ms, 0.01):.1f}x"
            if on_c.status == "PASS"
            else "N/A"
        )
        print(f"| `{task_name}` | {off_summary} | {on_summary} | {ratio} |")
    print()

    print("## 4. اختبار الإجهاد بالمشتتات والدرجات العالية (Distractor & High-Arity Stress Test)")
    print("- **اختبار حقن 20 مشتت (Distractor Injection)** على مسألة `world-clamp3.v0.3.yaml`:")
    print(
        f"  - بدون مشتتات (2 macros): {clean_clamp.wall_clock_ms:.2f}ms | {clean_clamp.probe_evaluations} probe evals | Peak RSS: {clean_clamp.peak_rss_kb:.1f} KB."
    )
    print(
        f"  - مع 20 مشتت نشط (22 macros): {distract_clamp.wall_clock_ms:.2f}ms | {distract_clamp.probe_evaluations} probe evals | Peak RSS: {distract_clamp.peak_rss_kb:.1f} KB."
    )
    slowdown = distract_clamp.wall_clock_ms / max(clean_clamp.wall_clock_ms, 0.01)
    print(
        f"  - التباطؤ الحسابي لعامل التفرع: **{slowdown:.2f}x** زيادة في زمن التوليد بسبب تضخم فضاء البدائل في القواعد."
    )
    print("- **اختبارات الدرجات العالية (High-Arity Stress)**:")
    print(
        f"  - Arity 5 (`sum5`): الحالة = **{cost_arity5.status}** | زمن = {cost_arity5.wall_clock_ms:.2f}ms | تقييمات = {cost_arity5.probe_evaluations} | عمق = {cost_arity5.ast_depth}."
    )
    print(
        f"  - Arity 8 (`sum8`): الحالة = **{cost_arity8.status}** | زمن = {cost_arity8.wall_clock_ms:.2f}ms | تقييمات = {cost_arity8.probe_evaluations} | سبب الانهيار = `{cost_arity8.failure_reason}`.\n"
    )

    print("## 5. حدود الانهيار ونقاط عدم الإحكام المعروفة (Failure Boundaries & Known Unsoundness)")
    print("- **الحد 1: العمليات الحسابية فوق الشروط (Arithmetic over Conditionals)**:")
    print(
        "  - المعادلة الهدف: $f(x, y) = 3 \\cdot \\text{If}(x < y, x, y) + 7 \\cdot \\text{If}(x == y, 2, 0)$"
    )
    print(
        f"  - نتيجة التوليد عبر شجرة القرار (ID3): **{'FAILED' if res_break is None else 'PASS'}** (استغرق {t_break_ms:.2f}ms)."
    )
    print(
        "  - سبب الانهيار البنيوي: خوارزمية تقسيم الفروع تبني الشروط من الأعلى للأسفل بافتراض أن الجذر هو `If` وأوراقه تعبيرات حسابية صماء؛ تفشل بنيوياً عندما تعلو العمليات الحسابية فروع الشروط دون مسبار وسيط."
    )
    print(
        "- **الحد 2: الظل المظلم وفجوة الأعداد الحقيقية مقابل الصحيحة (Non-Integral Polyhedra / Dark Shadow Gap)**:"
    )
    print("  - القيد الهدف: $2x + 4y = 1$ عبر النطاق الصحيح $x, y \\in [-10, 10]$.")
    print(
        f"  - الاسترخاء الحسابي للمجالات (Interval Relaxation): **{'FEASIBLE (Soundness Gap)' if rational_feasible else 'INFEASIBLE'}** (لأن النطاق المستمر $[-60, 60]$ يحوي 1)."
    )
    print(
        f"  - التحقق الدقيق للأعداد الصحيحة (Presburger / Diophantine): **{'NO_INTEGER_SOLUTION' if not has_integer_solutions else 'INTEGER_SOLUTION_EXISTS'}** (لأن $\\gcd(2, 4) = 2 \\nmid 1$)."
    )
    print(
        "  - الخلل المنطقي: استرخاء الفترات النسبية يُعطي إيجابياً كاذباً (False Positive) بوجود حل في فضاء الأعداد الحقيقية $\\mathbb{R}$ بينما هو مستحيل في $\\mathbb{Z}$. يجب تصنيف أي ادعاء ناتج عن استرخاء المجالات بـ `RATIONAL_RELAXATION_CHECKED` وتجريده من صفة البرهان التام."
    )


if __name__ == "__main__":
    if sys.argv[1:] == ["--prepare-locks"]:
        prepare_benchmark_write_locks()
        print("Benchmark input hashes verified and files marked read-only")
    elif not sys.argv[1:]:
        run_full_adversarial_evaluation()
    else:
        raise SystemExit("Usage: python -m experiments.adversarial_harness [--prepare-locks]")
