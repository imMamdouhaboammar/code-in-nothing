"""R0 integrated, paired pure-Python signature materialization comparison.

This research harness cannot alter candidate acceptance or authorize a native GO.
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
from copy import deepcopy
from pathlib import Path

from cin.contracts import load_genome
from experiments.hardware.profile_signature_search import (
    GENOME,
    ROOT,
    _validate_workload,
    run_workload,
)
from experiments.native_baseline import (
    DEFAULT_MANIFEST as R0_MANIFEST,
)
from experiments.native_baseline import (
    _provenance,
    fingerprint,
    load_protocol,
)

PROTOCOL = "cin.native-python-control.manifest/v0.2"
REPORT_PROTOCOL = "cin.native-python-control.report/v0.2"
DEFAULT_MANIFEST = Path(__file__).with_name("native-python-control.v0.2.json")
REFERENCE_COMMIT = "f48b68f8d18f59515d88c87c0fa59ec7651a553f"
ARMS = ("generator", "list")
LOGICAL_FIELDS = (
    "id",
    "kind",
    "status",
    "verdict_status",
    "candidate_hash",
    "proposals_seen",
    "trace_sha256",
    "verifier_calls",
    "verification_cases",
    "verification_ir_operations",
    "screen_cases",
    "screen_ir_operations",
    "logical_counters",
    "attribution",
)


class ParityFailure(RuntimeError):
    """A failed paired control with both arm records retained for diagnosis."""

    def __init__(self, diagnostic: dict):
        self.diagnostic = diagnostic
        super().__init__(
            f"R0 composition parity failure in {diagnostic['workload']} "
            f"seed={diagnostic['seed']} repetition={diagnostic['repetition']}: "
            f"{','.join(diagnostic['mismatched_fields'])}"
        )


def validate_control_protocol(value: object) -> dict:
    """Accept only the committed comparison, not attacker-selected task paths."""
    required = {
        "protocol",
        "source_commit",
        "seeds",
        "repetitions",
        "arms",
        "order",
        "comparison",
        "decision",
        "workloads",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError("unsupported integrated R0 control manifest")
    if (
        not isinstance(value["seeds"], list)
        or any(type(seed) is not int for seed in value["seeds"])
        or type(value["repetitions"]) is not int
        or not isinstance(value["workloads"], list)
    ):
        raise ValueError("invalid integrated R0 control cells")
    for workload in value["workloads"]:
        _validate_workload(workload)
    original = load_protocol(R0_MANIFEST)
    if (
        value["protocol"] != PROTOCOL
        or value["source_commit"] != REFERENCE_COMMIT
        or value["seeds"] != original["seeds"]
        or value["repetitions"] != original["repetitions"]
        or value["arms"] != list(ARMS)
        or value["order"] != "alternate-first-arm-by-repetition-and-seed"
        or value["comparison"] != "EXACT_LOGICAL_PARITY_AND_PAIRED_END_TO_END_WALL_CPU"
        or value["decision"] != "ITERATE_R0_NO_NATIVE_GO"
        or value["workloads"] != original["workloads"]
    ):
        raise ValueError("integrated R0 control must retain the frozen reference cells")
    return deepcopy(value)


def load_control_protocol(path: Path) -> dict:
    return validate_control_protocol(json.loads(path.read_text(encoding="utf-8")))


def _logical(sample: dict) -> dict:
    """Keep all scientific outcomes and counters separate from timing fields."""
    return {key: sample[key] for key in LOGICAL_FIELDS}


def paired_workload(workload: dict, base: dict, *, seed: int, repetition: int) -> dict:
    """Run both arms with fixed alternating order; refuse semantic divergence."""
    if type(seed) is not int or seed not in (0, 1, 2):
        raise ValueError("unregistered seed")
    if type(repetition) is not int or not 0 <= repetition < 5:
        raise ValueError("unregistered repetition")
    task = {**workload, "seed": seed}
    first_arm = ARMS[(seed + repetition) % len(ARMS)]
    order = ARMS if first_arm == ARMS[0] else tuple(reversed(ARMS))
    samples: dict[str, dict] = {}
    for arm in order:
        samples[arm] = run_workload(task, base, composition_mode=arm)
    reference = _logical(samples["generator"])
    alternative = _logical(samples["list"])
    if reference != alternative:
        mismatched = [key for key in LOGICAL_FIELDS if reference[key] != alternative[key]]
        raise ParityFailure(
            {
                "workload": task["id"],
                "seed": seed,
                "repetition": repetition,
                "first_arm": first_arm,
                "mismatched_fields": mismatched,
                "samples": samples,
            }
        )
    return {
        "workload": task["id"],
        "seed": seed,
        "repetition": repetition,
        "first_arm": first_arm,
        "logical_equal": True,
        "logical_sha256": fingerprint(reference),
        "samples": samples,
    }


def _summarize(pairs: list[dict]) -> list[dict]:
    groups: dict[str, list[dict]] = {}
    for pair in pairs:
        groups.setdefault(pair["workload"], []).append(pair)
    result = []
    for workload, rows in groups.items():
        ratios = [
            row["samples"]["generator"]["times_ns"]["total_wall"]
            / row["samples"]["list"]["times_ns"]["total_wall"]
            for row in rows
        ]
        result.append(
            {
                "workload": workload,
                "paired_samples": len(rows),
                "median_wall_ratio_generator_over_list": statistics.median(ratios),
                "median_generator_wall_ns": int(
                    statistics.median(
                        row["samples"]["generator"]["times_ns"]["total_wall"] for row in rows
                    )
                ),
                "median_list_wall_ns": int(
                    statistics.median(
                        row["samples"]["list"]["times_ns"]["total_wall"] for row in rows
                    )
                ),
                "p95": "NOT_ESTIMATED_SMALL_SHARED_HOST_SAMPLE",
                "interpretation": "EXPLORATORY_UNCONTROLLED_HOST",
            }
        )
    return result


def run_control(protocol: dict) -> dict:
    """Capture provenance first; retain every ordered pair and negative result."""
    protocol = validate_control_protocol(protocol)
    provenance = _provenance()
    base = load_genome(ROOT / GENOME)["genome"]["base"]
    pairs = []
    failure = None
    try:
        for workload in protocol["workloads"]:
            for seed in protocol["seeds"]:
                for repetition in range(protocol["repetitions"]):
                    pairs.append(paired_workload(workload, base, seed=seed, repetition=repetition))
    except ParityFailure as exc:
        failure = exc.diagnostic
    report = {
        "protocol": REPORT_PROTOCOL,
        "manifest": protocol,
        "manifest_sha256": fingerprint(protocol),
        "provenance": provenance,
        "pairs": pairs,
        "summary": _summarize(pairs) if failure is None else [],
        "paired_samples": len(pairs),
        "comparisons": "WHOLE_WORKLOAD_PYTHON_ONLY",
        "memory": "PER_TRIAL_RSS_NOT_MEASURED",
        "native_speedup": "NOT_MEASURED",
        "decision": "ITERATE_R0_NO_NATIVE_GO"
        if failure is None
        else "INVALID_CONTROL_NO_NATIVE_GO",
        "remaining_r0_gates": [
            "allocation and dedup cost attribution",
            "isolated per-trial peak RSS",
            "compute-heavy controlled-host confirmatory comparison",
            "native FFI/startup cost only after an independently justified R1 GO",
        ],
    }
    if failure is not None:
        report["status"] = "INVALID"
        report["failure"] = failure
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.output.exists() or not args.output.parent.is_dir():
            raise ValueError("output must be a new path in an existing directory")
        report = run_control(load_control_protocol(args.manifest))
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
        if report.get("status") == "INVALID":
            return 2
    except (ValueError, OSError, RuntimeError, subprocess.SubprocessError) as exc:
        parser.exit(2, f"INVALID integrated R0 control: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
