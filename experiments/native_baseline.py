"""R0 Python-only baseline and isolated signature-composition control.

No candidate execution, verifier policy or production search is replaced.
"""

from __future__ import annotations

import argparse
import cProfile
import hashlib
import json
import os
import platform
import pstats
import statistics
import subprocess
import sys
import time
from copy import deepcopy
from pathlib import Path

from cin.contracts import load_genome, load_world
from cin.guided_experiment import ARMS, run_trial
from cin.ir import canonical_bytes, run_ir_args
from cin.search import _probe_inputs, candidate_stream
from cin.training import PublicTrainingPanel
from experiments.hardware.profile_signature_search import (
    GENOME,
    ROOT,
    SCREEN,
    run_study,
    validate_manifest,
)
from experiments.hardware.profile_signature_search import (
    PROTOCOL as H0_PROTOCOL,
)

DEFAULT_MANIFEST = Path(__file__).with_name("native-baseline.v0.1.json")
PROTOCOL = "cin.native-baseline.manifest/v0.1"
PUBLIC_CASES = ((-4, -1), (1, -4), (0, 0), (-2, 3), (3, -2))


def fingerprint(data: object) -> str:
    return hashlib.sha256(canonical_bytes(data)).hexdigest()


def load_protocol(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    keys = {
        "protocol",
        "source_commit",
        "seeds",
        "repetitions",
        "guided_arms",
        "guided_proposals",
        "composition_iterations",
        "native_go",
        "workloads",
    }
    if not isinstance(data, dict) or set(data) != keys or data["protocol"] != PROTOCOL:
        raise ValueError("unsupported R0 manifest")
    seeds = data["seeds"]
    if (
        not isinstance(seeds, list)
        or not 1 <= len(seeds) <= 5
        or any(type(s) is not int or not 0 <= s < 2**32 for s in seeds)
        or len(seeds) != len(set(seeds))
    ):
        raise ValueError("seeds must be unique bounded integers")
    for key, maximum in (
        ("repetitions", 20),
        ("guided_proposals", 30000),
        ("composition_iterations", 1000),
    ):
        if type(data[key]) is not int or not 1 <= data[key] <= maximum:
            raise ValueError(f"invalid {key}")
    if (
        data["guided_arms"] != list(ARMS)
        or data["native_go"] != "REQUIRES_END_TO_END_PARITY_AND_2X"
    ):
        raise ValueError("fixed experiment arms and decision rule required")
    validate_manifest(_h0(data, seeds[0]))
    if not any(row["kind"] == "world" and row["id"] != "exhaustion" for row in data["workloads"]):
        raise ValueError("at least one guided-compatible world workload required")
    return data


def _h0(protocol: dict, seed: int) -> dict:
    return {
        "protocol": H0_PROTOCOL,
        "source_commit": protocol["source_commit"],
        "genome": GENOME,
        "screen_points": [list(p) for p in SCREEN],
        "workloads": [{**row, "seed": seed} for row in protocol["workloads"]],
    }


def _peak_rss() -> int | None:
    try:
        import resource

        value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return int(value if sys.platform == "darwin" else value * 1024)
    except ImportError:
        return None


def measure(action) -> dict:
    wall = time.perf_counter_ns()
    cpu = time.process_time_ns()
    result = action()
    cpu = time.process_time_ns() - cpu
    wall = time.perf_counter_ns() - wall
    return {
        "result": result,
        "wall_ns": wall,
        "process_cpu_ns": cpu,
        "peak_rss_bytes": _peak_rss(),
        "rss_scope": "PROCESS_LIFETIME_HIGH_WATER_MARK",
    }


def compose_batch(pairs: tuple, op: str, arm: str) -> tuple:
    if arm not in ("generator", "list"):
        raise ValueError("unknown composition arm")
    if op not in ("Add", "Sub", "LessThan", "Equal"):
        raise ValueError("unknown composition operation")
    output = []
    for left, right in pairs:
        if op == "Add":
            row = (
                tuple(a + b for a, b in zip(left, right))
                if arm == "generator"
                else tuple([a + b for a, b in zip(left, right)])
            )
        elif op == "Sub":
            row = (
                tuple(a - b for a, b in zip(left, right))
                if arm == "generator"
                else tuple([a - b for a, b in zip(left, right)])
            )
        elif op == "LessThan":
            row = (
                tuple(a < b for a, b in zip(left, right))
                if arm == "generator"
                else tuple([a < b for a, b in zip(left, right)])
            )
        else:
            row = (
                tuple(a == b for a, b in zip(left, right))
                if arm == "generator"
                else tuple([a == b for a, b in zip(left, right)])
            )
        output.append(row)
    return tuple(output)


def paired_composition(pairs: tuple, *, repetitions: int, iterations: int) -> dict:
    records = []
    for op in ("Add", "Sub", "LessThan", "Equal"):
        expected = compose_batch(pairs, op, "generator")
        for repetition in range(repetitions):
            order = ("generator", "list") if repetition % 2 == 0 else ("list", "generator")
            samples = {}
            for arm in order:

                def action():
                    result = None
                    for _ in range(iterations):
                        result = compose_batch(pairs, op, arm)
                    return result

                sample = measure(action)
                if sample.pop("result") != expected:
                    raise RuntimeError("composition control changed exact observations")
                samples[arm] = sample
            records.append(
                {
                    "operation": op,
                    "repetition": repetition,
                    "first_arm": order[0],
                    "samples": samples,
                    "observations_sha256": fingerprint(expected),
                }
            )
    return {
        "scope": "ISOLATED_COMPOSITION_NOT_END_TO_END",
        "pairs": records,
        "input_sha256": fingerprint(pairs),
        "scalar_operations_per_sample": sum(len(a) for a, _ in pairs) * iterations,
        "iterations": iterations,
    }


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def _provenance() -> dict:
    files = [
        *ROOT.joinpath("cin").glob("*.py"),
        *ROOT.joinpath("experiments").glob("*.py"),
        ROOT / "experiments/hardware/profile_signature_search.py",
        ROOT / "uv.lock",
        ROOT / ".github/workflows/ci.yml",
    ]
    cpu_model = platform.processor()
    if not cpu_model and Path("/proc/cpuinfo").exists():
        cpu_model = next(
            (
                line.split(":", 1)[1].strip()
                for line in Path("/proc/cpuinfo").read_text().splitlines()
                if line.startswith("model name")
            ),
            "UNKNOWN",
        )
    return {
        "execution_commit": _git("rev-parse", "HEAD"),
        "working_tree_status": _git("status", "--porcelain"),
        "source_sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(files)
        },
        "python": sys.version,
        "platform": platform.platform(),
        "processor": cpu_model or "UNKNOWN",
        "machine": platform.machine(),
        "logical_cpus": os.cpu_count(),
        "host_control": "SHARED_HOST_IDLE_STATE_UNCONTROLLED",
    }


def _guided(base: dict, protocol: dict) -> list[dict]:
    records = []
    for workload in protocol["workloads"]:
        if workload["kind"] != "world" or workload["id"] == "exhaustion":
            continue
        world = load_world(ROOT / "examples" / workload["world"])
        panel = PublicTrainingPanel(world, PUBLIC_CASES)
        for seed in protocol["seeds"]:
            for repetition in range(protocol["repetitions"]):
                # Rotate paired order to reduce systematic arm/warm-cache confounding.
                arms = list(ARMS)
                shift = repetition % len(arms)
                arms = arms[shift:] + arms[:shift]
                for arm in arms:
                    sample = measure(
                        lambda: run_trial(
                            arm,
                            world,
                            base,
                            panel,
                            seed=seed,
                            max_proposals=protocol["guided_proposals"],
                        )
                    )
                    logical = {k: v for k, v in sample["result"].items() if k != "cpu_seconds"}
                    records.append(
                        {
                            "task": workload["id"],
                            "seed": seed,
                            "arm": arm,
                            "repetition": repetition,
                            "logical_sha256": fingerprint(logical),
                            **sample,
                        }
                    )
    grouped = {}
    for row in records:
        key = (row["task"], row["seed"], row["arm"])
        grouped.setdefault(key, set()).add(row["logical_sha256"])
    if any(len(values) != 1 for values in grouped.values()):
        raise RuntimeError("guided baseline changed logical outcomes across repetitions")
    return records


def _guided_summary(records: list[dict]) -> list[dict]:
    groups = {}
    for row in records:
        groups.setdefault((row["task"], row["seed"], row["arm"]), []).append(row)
    return [
        {
            "task": key[0],
            "seed": key[1],
            "arm": key[2],
            "samples": len(rows),
            "median_wall_ns": int(statistics.median(r["wall_ns"] for r in rows)),
            "min_wall_ns": min(r["wall_ns"] for r in rows),
            "max_wall_ns": max(r["wall_ns"] for r in rows),
            "status": rows[0]["result"]["status"],
            "p95": "NOT_ESTIMATED_SMALL_REPEAT_COUNT",
        }
        for key, rows in groups.items()
    ]


def run_baseline(protocol: dict) -> dict:
    base = load_genome(ROOT / GENOME)["genome"]["base"]
    h0 = [
        measure(
            lambda seed=seed: run_study(_h0(protocol, seed), repetitions=protocol["repetitions"])
        )
        for seed in protocol["seeds"]
    ]
    for wrapper in h0:
        wrapper["measurement_scope"] = "HARNESS_PLUS_CPROFILE_NOT_PRIMARY_TIMING"
        for workload in wrapper["result"]["runs"]:
            for sample in workload["samples"]:
                wall_ns = sample["times_ns"]["total_wall"]
                sample["proposals_per_second"] = sample["proposals_seen"] * 1e9 / wall_ns
                sample["first_discovery_logical_budget"] = (
                    {
                        "proposals_seen": sample["proposals_seen"],
                        "search": sample["logical_counters"],
                        "screen_ir_operations": sample["screen_ir_operations"],
                        "verification_ir_operations": sample["verification_ir_operations"],
                    }
                    if sample["status"] == "PASS"
                    else None
                )
    proposals = list(candidate_stream(base["starting_expression"], base, seed=0, max_proposals=12))
    probes = _probe_inputs(2)
    signatures = tuple(
        tuple(run_ir_args(p.expression, point, expected_arity=2) for point in probes)
        for p in proposals
    )
    pairs = tuple(zip(signatures, reversed(signatures)))
    composition = paired_composition(
        pairs, repetitions=protocol["repetitions"], iterations=protocol["composition_iterations"]
    )
    guided = _guided(base, protocol)
    diagnostic = cProfile.Profile()
    world = load_world(ROOT / "examples/world-max2.v0.1.yaml")
    panel = PublicTrainingPanel(world, PUBLIC_CASES)
    diagnostic.runcall(
        run_trial, "B2", world, base, panel, seed=0, max_proposals=protocol["guided_proposals"]
    )
    rows = [
        {
            "file": Path(file).name,
            "line": line,
            "function": fn,
            "calls": values[1],
            "self_ns": int(values[2] * 1e9),
            "cumulative_ns": int(values[3] * 1e9),
        }
        for (file, line, fn), values in pstats.Stats(diagnostic).stats.items()
        if "/cin/" in file
    ]
    return {
        "protocol": "cin.native-baseline.report/v0.1",
        "manifest": deepcopy(protocol),
        "manifest_sha256": fingerprint(protocol),
        "provenance": _provenance(),
        "h0_baselines": h0,
        "guided_baselines": guided,
        "composition_control": composition,
        "guided_profile": {
            "scope": "INSTRUMENTED_DIAGNOSTIC_NOT_PRIMARY_TIMING",
            "top_self_time": sorted(rows, key=lambda r: -r["self_ns"])[:30],
        },
        "decision": "ITERATE_R0_NO_NATIVE_GO",
        "native_speedup": "NOT_MEASURED",
        "unresolved": [
            "integrated improved-Python end-to-end comparison",
            "isolated allocator and dedup cost attribution",
            "per-trial isolated peak RSS",
            "native conversion costs",
            "controlled-host confirmatory timing",
        ],
        "guided_summary": _guided_summary(guided),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.output.exists():
            raise ValueError("refusing to overwrite experiment evidence")
        report = run_baseline(load_protocol(args.manifest))
        with args.output.open("x", encoding="utf-8") as out:
            json.dump(report, out, indent=2, sort_keys=True, allow_nan=False)
            out.write("\n")
    except (ValueError, OSError, RuntimeError) as exc:
        parser.exit(2, f"INVALID R0 baseline: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
