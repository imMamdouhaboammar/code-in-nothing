"""R0 v0.3: separate-process peak-RSS diagnostics for the frozen Python arms.

Diagnostic subprocesses execute only the project's bounded, data-only IR. This
is not an operating-system security sandbox or a native-backend benchmark.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import subprocess
import sys
import time
from copy import deepcopy
from pathlib import Path

from cin.contracts import load_genome
from experiments.hardware.profile_signature_search import GENOME, ROOT, run_workload
from experiments.native_baseline import _peak_rss, _provenance, fingerprint
from experiments.native_python_control import (
    ARMS,
    _logical,
    load_control_protocol,
)
from experiments.native_python_control import (
    DEFAULT_MANIFEST as PAIRED_MANIFEST,
)

PROTOCOL = "cin.native-rss-control.manifest/v0.3"
REPORT_PROTOCOL = "cin.native-rss-control.report/v0.3"
DEFAULT_MANIFEST = Path(__file__).with_name("native-rss-control.v0.3.json")
REFERENCE_COMMIT = "dfd0b7b44d08358808b02e9a87b218f4b6c24311"
RSS_SCOPE = "FRESH_PROCESS_LIFETIME_HIGH_WATER_INCLUDES_PYTHON_IMPORTS"
DECISION = "ITERATE_R0_NO_NATIVE_GO"


class DiagnosticFailure(RuntimeError):
    """Retain partial paired evidence after a child failure or logical mismatch."""

    def __init__(self, diagnostic: dict):
        self.diagnostic = diagnostic
        super().__init__(f"invalid isolated RSS trial: {diagnostic['reason']}")


def validate_manifest(value: object) -> dict:
    """Reject modified workload paths, arms, budgets, or other frozen cells."""
    previous = load_control_protocol(PAIRED_MANIFEST)
    expected = {
        "protocol": PROTOCOL,
        "source_commit": REFERENCE_COMMIT,
        "seeds": previous["seeds"],
        "repetitions": 2,
        "arms": list(ARMS),
        "workloads": previous["workloads"],
        "measurement": "ONE_FRESH_SUBPROCESS_PER_ARM_PER_CELL",
        "decision": DECISION,
    }
    # Canonical JSON distinguishes booleans from integers (True must not be seed 1).
    if not isinstance(value, dict) or fingerprint(value) != fingerprint(expected):
        raise ValueError("isolated RSS protocol must retain all preregistered cells")
    return deepcopy(expected)


def load_manifest(path: Path) -> dict:
    return validate_manifest(json.loads(path.read_text(encoding="utf-8")))


def _child_sample(workload_id: str, seed: int, arm: str) -> dict:
    protocol = load_manifest(DEFAULT_MANIFEST)
    if type(seed) is not int or seed not in protocol["seeds"] or arm not in ARMS:
        raise ValueError("unregistered child trial")
    matches = [row for row in protocol["workloads"] if row["id"] == workload_id]
    if len(matches) != 1:
        raise ValueError("unregistered child workload")
    base = load_genome(ROOT / GENOME)["genome"]["base"]
    rss_before = _peak_rss()
    sample = run_workload({**matches[0], "seed": seed}, base, composition_mode=arm)
    rss_after = _peak_rss()
    if (
        type(rss_before) is not int
        or type(rss_after) is not int
        or rss_before <= 0
        or rss_after <= 0
    ):
        rss_before = rss_after = None
    return {
        "sample": sample,
        "peak_rss_bytes": rss_after,
        "peak_rss_before_workload_bytes": rss_before,
        "rss_scope": RSS_SCOPE if rss_after is not None else "NOT_MEASURED_UNSUPPORTED_PLATFORM",
    }


def _run_child(workload_id: str, seed: int, arm: str) -> dict:
    # No caller-selected code/path or shell interpolation; only frozen workload IDs.
    env = {key: os.environ[key] for key in ("PATH", "SYSTEMROOT", "WINDIR") if key in os.environ}
    env.update(PYTHONHASHSEED="0", PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1")
    cmd = [
        sys.executable,
        "-m",
        "experiments.native_rss_control",
        "--child-workload",
        workload_id,
        "--seed",
        str(seed),
        "--arm",
        arm,
    ]
    start = time.perf_counter_ns()
    try:
        completed = subprocess.run(
            cmd, cwd=ROOT, env=env, capture_output=True, text=True, timeout=60, check=False
        )
    except (subprocess.SubprocessError, OSError) as exc:
        raise DiagnosticFailure(
            {"reason": "CHILD_PROCESS_ERROR", "error_type": type(exc).__name__}
        ) from exc
    process_wall_ns = time.perf_counter_ns() - start
    if completed.returncode != 0:
        raise DiagnosticFailure(
            {"reason": "CHILD_NONZERO_EXIT", "returncode": completed.returncode}
        )
    try:
        result = json.loads(completed.stdout)
        if (
            not isinstance(result, dict)
            or not isinstance(result["sample"], dict)
            or result["rss_scope"] not in (RSS_SCOPE, "NOT_MEASURED_UNSUPPORTED_PLATFORM")
        ):
            raise ValueError("malformed child result")
        if result["sample"]["id"] != workload_id:
            raise ValueError("wrong workload in child result")
        before, after = (
            result["peak_rss_before_workload_bytes"],
            result["peak_rss_bytes"],
        )
        if result["rss_scope"] == RSS_SCOPE:
            if any(type(v) is not int or v <= 0 for v in (before, after)) or after < before:
                raise ValueError("invalid process-scoped high-water RSS")
        elif before is not None or after is not None:
            raise ValueError("unsupported RSS must remain unmeasured")
        workload_ns = result["sample"]["times_ns"]["total_wall"]
        if type(workload_ns) is not int or workload_ns <= 0:
            raise ValueError("invalid workload duration")
    except (ValueError, TypeError, KeyError) as exc:
        raise DiagnosticFailure({"reason": "CHILD_INVALID_OUTPUT"}) from exc
    if process_wall_ns < workload_ns:
        raise DiagnosticFailure({"reason": "CHILD_TIMING_INCONSISTENT"})
    result["subprocess_wall_ns"] = process_wall_ns
    result["subprocess_nonworkload_wall_ns"] = process_wall_ns - workload_ns
    result["subprocess_overhead_scope"] = "IMPORT_LAUNCH_SERIALIZATION_AND_EXIT_NOT_STARTUP_ONLY"
    return result


def paired_memory_trial(workload: dict, *, seed: int, repetition: int, runner=_run_child) -> dict:
    if type(seed) is not int or seed not in (0, 1, 2):
        raise ValueError("unregistered seed")
    if type(repetition) is not int or not 0 <= repetition < 2:
        raise ValueError("unregistered repetition")
    first_arm = ARMS[(seed + repetition) % len(ARMS)]
    order = ARMS if first_arm == ARMS[0] else tuple(reversed(ARMS))
    samples: dict[str, dict] = {}
    for arm in order:
        try:
            samples[arm] = runner(workload["id"], seed, arm)
        except DiagnosticFailure as exc:
            raise DiagnosticFailure(
                {
                    **exc.diagnostic,
                    "workload": workload["id"],
                    "seed": seed,
                    "repetition": repetition,
                    "completed_samples": samples,
                }
            ) from exc
    try:
        reference = _logical(samples["generator"]["sample"])
        alternative = _logical(samples["list"]["sample"])
    except (KeyError, TypeError, ValueError) as exc:
        raise DiagnosticFailure(
            {
                "reason": "MALFORMED_LOGICAL_RECORD",
                "workload": workload["id"],
                "seed": seed,
                "repetition": repetition,
                "completed_samples": samples,
            }
        ) from exc
    if reference != alternative:
        raise DiagnosticFailure(
            {
                "reason": "LOGICAL_PARITY_MISMATCH",
                "workload": workload["id"],
                "seed": seed,
                "repetition": repetition,
                "mismatched_fields": [k for k in reference if reference[k] != alternative[k]],
                "completed_samples": samples,
            }
        )
    return {
        "workload": workload["id"],
        "seed": seed,
        "repetition": repetition,
        "first_arm": first_arm,
        "logical_equal": True,
        "logical_sha256": fingerprint(reference),
        "samples": samples,
    }


def _inputs_sha256() -> dict[str, str]:
    """Include experimental input schemas and fixtures omitted by R0 v0.1 provenance."""
    paths = sorted(
        (
            *ROOT.glob("examples/*.yaml"),
            *ROOT.glob("cin/schemas/*.json"),
            *ROOT.glob("schemas/*.json"),
        )
    )
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def run_study(protocol: dict) -> dict:
    protocol = validate_manifest(protocol)
    provenance = _provenance()
    provenance["experimental_input_sha256"] = _inputs_sha256()
    pairs = []
    failure = None
    try:
        for workload in protocol["workloads"]:
            for seed in protocol["seeds"]:
                for repetition in range(protocol["repetitions"]):
                    pairs.append(paired_memory_trial(workload, seed=seed, repetition=repetition))
    except DiagnosticFailure as exc:
        failure = exc.diagnostic
    summary = []
    if failure is None:
        for workload in protocol["workloads"]:
            rows = [p for p in pairs if p["workload"] == workload["id"]]
            median_rss = {}
            for arm in ARMS:
                values = [p["samples"][arm]["peak_rss_bytes"] for p in rows]
                median_rss[arm] = (
                    int(statistics.median(values)) if all(v is not None for v in values) else None
                )
            summary.append(
                {
                    "workload": workload["id"],
                    "paired_samples": len(rows),
                    "median_peak_rss_bytes": median_rss,
                    "interpretation": "EXPLORATORY_SHARED_HOST_PROCESS_SCOPED_NOT_ALLOCATION_COUNT",
                }
            )
    observed_scopes = {sample["rss_scope"] for pair in pairs for sample in pair["samples"].values()}
    rss_scope = (
        next(iter(observed_scopes))
        if len(observed_scopes) == 1
        else "MIXED_OR_INCOMPLETE_CHILD_RSS_SCOPES"
    )
    report = {
        "protocol": REPORT_PROTOCOL,
        "manifest": protocol,
        "manifest_sha256": fingerprint(protocol),
        "provenance": provenance,
        "pairs": pairs,
        "paired_samples": len(pairs),
        "summary": summary,
        "rss_scope": rss_scope,
        "timing_comparison": "NOT_VALID_STARTUP_AND_IMPORTS_INCLUDED",
        "native_speedup": "NOT_MEASURED",
        "decision": DECISION if failure is None else "INVALID_CONTROL_NO_NATIVE_GO",
        "remaining_r0_gates": [
            "independent tuple/allocation/dedup attribution",
            "full-lifecycle compute-heavy controlled-host comparison",
            "native FFI/startup cost only after justified R1 GO",
        ],
    }
    if failure is not None:
        report["status"] = "INVALID"
        report["failure"] = failure
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--child-workload", help=argparse.SUPPRESS)
    parser.add_argument("--seed", type=int, help=argparse.SUPPRESS)
    parser.add_argument("--arm", choices=ARMS, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        if args.child_workload is not None:
            if args.output is not None or args.manifest != DEFAULT_MANIFEST:
                raise ValueError("child mode does not accept output or alternate manifests")
            result = _child_sample(args.child_workload, args.seed, args.arm)
            print(json.dumps(result, sort_keys=True, allow_nan=False))
            return 0
        if args.seed is not None or args.arm is not None:
            raise ValueError("seed/arm are child-only arguments")
        if args.output is None or args.output.exists() or not args.output.parent.is_dir():
            raise ValueError("output must be a new file in an existing directory")
        report = run_study(load_manifest(args.manifest))
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
        return 2 if report.get("status") == "INVALID" else 0
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(2, f"INVALID isolated RSS control: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
