"""H0 CPU-only, non-invasive profiling of CIN's existing mathematical search.

No change to candidate_stream or the independent verifier. Search-stage time is
an *optimistic envelope*, not measured offload-eligible signature time.
"""

from __future__ import annotations

import argparse
import ast
import cProfile
import hashlib
import json
import os
import platform
import statistics
import sys
import time
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path

from cin.contracts import load_genome, load_world
from cin.ir import canonical_hash, run_ir
from cin.search import SearchStats, candidate_stream
from cin.worlds import check_formula, verify_program

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = Path(__file__).with_name("manifest.v0.1.json")
PROTOCOL = "cin.hardware.h0.manifest/v0.1"
REPORT_PROTOCOL = "cin.hardware.h0.report/v0.1"
GENOME = "examples/seed-genome.v0.1.yaml"
WORLDS = frozenset(
    {
        "world-max2.v0.1.yaml",
        "world-min2.v0.1.yaml",
        "world-absdiff.v0.2.yaml",
    }
)
SCREEN = ((-4, -1), (1, -4), (0, 0), (-2, 3), (3, -2), (4, 4))


def _positive_integer(value: object, *, maximum: int) -> bool:
    return type(value) is int and 1 <= value <= maximum


def _validate_workload(value: object) -> dict:
    if not isinstance(value, dict):
        raise ValueError("workload must be an object")
    kind = value.get("kind")
    expected = {"id", "kind", "arity", "seed", "max_proposals"}
    if kind == "world":
        expected.add("world")
    elif kind != "search_only":
        raise ValueError("unknown workload kind")
    if set(value) != expected:
        raise ValueError("workload must have exactly its declared fields")
    if not isinstance(value["id"], str) or not value["id"].isascii():
        raise ValueError("workload id must be ASCII text")
    if not value["id"] or not all(c.isalnum() or c in "-_" for c in value["id"]):
        raise ValueError("invalid workload id")
    if not _positive_integer(value["arity"], maximum=8):
        raise ValueError("arity must be 1..8")
    if type(value["seed"]) is not int or not 0 <= value["seed"] <= 2**32 - 1:
        raise ValueError("seed must be a bounded nonnegative integer")
    if not _positive_integer(value["max_proposals"], maximum=30000):
        raise ValueError("proposal budget must be 1..30000")
    if kind == "world":
        if value["arity"] != 2 or type(value["world"]) is not str or value["world"] not in WORLDS:
            raise ValueError("only named two-input world fixtures are allowed")
    elif value["arity"] < 3:
        raise ValueError("search-only probe extension must have at least 3 inputs")
    return value


def validate_manifest(data: object) -> dict:
    """Validate a frozen H0 manifest; no arbitrary file paths or task injection."""
    if not isinstance(data, dict):
        raise ValueError("manifest must be an object")
    if set(data) != {"protocol", "source_commit", "genome", "screen_points", "workloads"}:
        raise ValueError("unexpected manifest keys")
    if data["protocol"] != PROTOCOL or data["genome"] != GENOME:
        raise ValueError("unsupported manifest protocol or genome")
    commit = data["source_commit"]
    if not isinstance(commit, str) or len(commit) != 40:
        raise ValueError("source commit must be a full SHA-1")
    if any(c not in "0123456789abcdef" for c in commit):
        raise ValueError("source commit is not hexadecimal")
    points = data["screen_points"]
    if not isinstance(points, list) or len(points) != len(SCREEN):
        raise ValueError("expected six frozen screen points")
    if any(
        not isinstance(p, list)
        or len(p) != 2
        or any(type(coord) is not int or not -4 <= coord <= 4 for coord in p)
        for p in points
    ):
        raise ValueError("invalid screening point")
    if len({tuple(p) for p in points}) != len(points):
        raise ValueError("duplicate screening points")
    workloads = data["workloads"]
    if not isinstance(workloads, list) or not 1 <= len(workloads) <= 10:
        raise ValueError("manifest needs 1..10 workloads")
    for workload in workloads:
        _validate_workload(workload)
    names = [workload["id"] for workload in workloads]
    if len(set(names)) != len(names):
        raise ValueError("duplicate workload ids")
    return deepcopy(data)


def load_manifest(path: Path) -> dict:
    return validate_manifest(json.loads(path.read_text(encoding="utf-8")))


def amdahl_search_ceiling(search_ns: int, total_ns: int) -> float | None:
    """Upper bound when *all* search-stage time vanishes; None means unbounded."""
    if (
        type(search_ns) is not int
        or type(total_ns) is not int
        or total_ns <= 0
        or not 0 <= search_ns <= total_ns
    ):
        raise ValueError("invalid nonnegative timing interval")
    if search_ns == total_ns:
        return None
    return total_ns / (total_ns - search_ns)


def _signature_generator_lines() -> list[int]:
    """Find composition genexprs; excludes leaves and interpreter calls.

    This is a cProfile source-attribution diagnostic, not a complete sum of
    tuple allocation, hashing, dispatch or offload-eligible elapsed time.
    """
    import cin.search as search

    source = Path(search.__file__).read_text(encoding="utf-8")
    lines = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "values" for target in node.targets
        ):
            continue
        call = node.value
        if (
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Name)
            and call.func.id == "tuple"
            and len(call.args) == 1
            and isinstance(call.args[0], ast.GeneratorExp)
        ):
            lines.append(call.args[0].lineno)
    return sorted(set(lines))


def _profile_diagnostic(profiler: cProfile.Profile, trace_sha256: str) -> dict:
    """Report only instrumented function self-time, never an FPGA speedup."""
    import cin.search as search

    search_path = Path(search.__file__).resolve()
    signature_lines = set(_signature_generator_lines())
    rows = []
    signature_self_ns = 0
    for (filename, line, function), (primitive_calls, calls, self_s, cumulative_s, _) in (
        _pstats_rows(profiler)
    ):
        self_ns = int(self_s * 1_000_000_000)
        if Path(filename) == search_path and function == "<genexpr>" and line in signature_lines:
            signature_self_ns += self_ns
        if (
            filename.endswith("/cin/search.py")
            or filename.endswith("/cin/ir.py")
            or filename.endswith("/cin/worlds.py")
        ):
            rows.append(
                {
                    "file": Path(filename).name,
                    "line": line,
                    "function": function,
                    "calls": calls,
                    "self_ns": self_ns,
                    "cumulative_ns": int(cumulative_s * 1_000_000_000),
                }
            )
    return {
        "mode": "instrumented_cprofile",
        "trace_sha256": trace_sha256,
        "composition_generator_lines": sorted(signature_lines),
        "composition_genexpr_self_ns": signature_self_ns,
        "composition_coverage": "PARTIAL_EXCLUDES_TUPLE_AND_SEARCH_DISPATCH",
        "top_function_self_time": sorted(rows, key=lambda row: -row["self_ns"])[:20],
    }


def _pstats_rows(profiler: cProfile.Profile):
    import pstats

    return pstats.Stats(profiler).stats.items()


def run_workload(
    workload: dict,
    base: dict,
    *,
    screen: tuple[tuple[int, int], ...] = SCREEN,
    profile: bool = False,
) -> dict:
    """Exercise the unchanged generator; benchmark data never enters search."""
    _validate_workload(workload)
    local_base = deepcopy(base)
    world = None
    if workload["kind"] == "world":
        world = load_world(ROOT / "examples" / workload["world"])
    else:
        local_base["cin_ir_version"] = "0.2"
        local_base["input_types"] = ["Int"] * workload["arity"]

    stats = SearchStats()
    trace = hashlib.sha256()
    count = 0
    screen_cases = 0
    screen_ops = [0]
    formal_calls = 0
    formal_cases = 0
    formal_ops = 0
    candidate_hash = None
    verdict_status = "NOT_RUN"
    status = "SEARCH_ONLY" if world is None else "UNKNOWN"
    search_wall = screen_wall = verify_wall = 0
    profiler = cProfile.Profile() if profile else None
    start_wall = time.perf_counter_ns()
    start_cpu = time.process_time_ns()
    if profiler is not None:
        profiler.enable()
    try:
        stream = candidate_stream(
            local_base["starting_expression"],
            local_base,
            seed=workload["seed"],
            max_proposals=workload["max_proposals"],
            stats=stats,
        )
        while True:
            tick = time.perf_counter_ns()
            try:
                proposal = next(stream)
            except StopIteration:
                search_wall += time.perf_counter_ns() - tick
                break
            search_wall += time.perf_counter_ns() - tick
            count += 1
            digest_record = (
                canonical_hash(proposal.expression),
                proposal.operator,
                proposal.parent_hash,
                proposal.rng_seed,
            )
            trace.update(json.dumps(digest_record, separators=(",", ":")).encode() + b"\n")
            if world is None:
                continue
            accepted = True
            tick = time.perf_counter_ns()
            for x, y in screen:
                screen_cases += 1
                output = run_ir(proposal.expression, x, y, ops_counter=screen_ops)
                if not check_formula(world["postcondition"], {"x": x, "y": y, "result": output}):
                    accepted = False
                    break
            screen_wall += time.perf_counter_ns() - tick
            if not accepted:
                continue
            tick = time.perf_counter_ns()
            verdict = verify_program(proposal.expression, world, local_base, max_cases=81)
            verify_wall += time.perf_counter_ns() - tick
            formal_calls += 1
            formal_cases += verdict.checked
            formal_ops += verdict.operations
            verdict_status = verdict.status
            if verdict.status == "PASS":
                status = "PASS"
                candidate_hash = canonical_hash(proposal.expression)
                break
        stream.close()
    finally:
        if profiler is not None:
            profiler.disable()
    cpu_ns = time.process_time_ns() - start_cpu
    total_ns = time.perf_counter_ns() - start_wall
    output = {
        "id": workload["id"],
        "kind": workload["kind"],
        "status": status,
        "verdict_status": verdict_status,
        "candidate_hash": candidate_hash,
        "proposals_seen": count,
        "trace_sha256": trace.hexdigest(),
        "verifier_calls": formal_calls,
        "verification_cases": formal_cases,
        "verification_ir_operations": formal_ops,
        "screen_cases": screen_cases,
        "screen_ir_operations": screen_ops[0],
        "logical_counters": asdict(stats),
        "times_ns": {
            "total_wall": total_ns,
            "process_cpu": cpu_ns,
            "search_wall": search_wall,
            "screen_wall": screen_wall,
            "verification_wall": verify_wall,
            "unattributed_wall": max(0, total_ns - search_wall - screen_wall - verify_wall),
        },
        "attribution": {
            "signature_eligible_fraction": "UNRESOLVED",
            "tuple_allocations": "UNRESOLVED",
            "search_dispatch_and_ast": "INCLUDED_IN_SEARCH_STAGE",
            "world_admission": "NOT_RUN",
            "archival": "NOT_RUN",
            "unpruned_control": "NOT_RUN",
        },
        "profile": None,
    }
    if profiler is not None:
        output["profile"] = _profile_diagnostic(profiler, output["trace_sha256"])
    return output


def run_study(manifest: dict, *, repetitions: int = 3, profile: bool = True) -> dict:
    """Run non-instrumented timing reps, then a distinct diagnostic profile."""
    manifest = validate_manifest(manifest)
    if not _positive_integer(repetitions, maximum=20):
        raise ValueError("repetitions must be 1..20")
    base = load_genome(ROOT / manifest["genome"])["genome"]["base"]
    screen = tuple(tuple(point) for point in manifest["screen_points"])
    runs = []
    for workload in manifest["workloads"]:
        samples = [
            run_workload(workload, base, screen=screen, profile=False) for _ in range(repetitions)
        ]
        fingerprints = {
            (
                sample["trace_sha256"],
                sample["status"],
                sample["candidate_hash"],
                json.dumps(sample["logical_counters"], sort_keys=True),
            )
            for sample in samples
        }
        if len(fingerprints) != 1:
            raise RuntimeError("non-deterministic logical search trace; refusing study")
        profile_run = run_workload(workload, base, screen=screen, profile=True) if profile else None
        if profile_run is not None:
            reference = samples[0]
            if (
                profile_run["trace_sha256"] != reference["trace_sha256"]
                or profile_run["logical_counters"] != reference["logical_counters"]
                or profile_run["status"] != reference["status"]
            ):
                raise RuntimeError("profiled run altered proposal trace or verdict")
        search_ns = sum(sample["times_ns"]["search_wall"] for sample in samples)
        total_ns = sum(sample["times_ns"]["total_wall"] for sample in samples)
        runs.append(
            {
                "id": workload["id"],
                "workload": workload,
                "samples": samples,
                "median_total_wall_ns": int(
                    statistics.median(sample["times_ns"]["total_wall"] for sample in samples)
                ),
                "amdahl_scope": "entire_search_stage_optimistic_upper_bound",
                "amdahl_search_ceiling": amdahl_search_ceiling(search_ns, total_ns),
                "profile_diagnostic": profile_run["profile"] if profile_run is not None else None,
            }
        )
    digest = hashlib.sha256(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return {
        "protocol": REPORT_PROTOCOL,
        "manifest_sha256": digest,
        "manifest_source_commit": manifest["source_commit"],
        "execution_commit": os.environ.get("GITHUB_SHA", "UNKNOWN"),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "implementation": platform.python_implementation(),
        },
        "repetitions_unprofiled": repetitions,
        "runs": runs,
        "hardware_speedup_claim": "NOT_MEASURED",
        "signature_fraction_decision": "UNRESOLVED",
        "h0_go_no_go": "PENDING_PROFILING_REVIEW",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--no-profile", action="store_true")
    parser.add_argument("--output", type=Path, help="New report file; refuses overwrites")
    args = parser.parse_args(argv)
    try:
        report = run_study(
            load_manifest(args.manifest),
            repetitions=args.repetitions,
            profile=not args.no_profile,
        )
        encoded = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
        if args.output is None:
            sys.stdout.write(encoded)
        else:
            with args.output.open("x", encoding="utf-8") as f:
                f.write(encoded)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        parser.exit(2, f"INVALID H0 study: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
