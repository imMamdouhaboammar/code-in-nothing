"""H0 falsification harness contracts: provenance, search fidelity, and no invented hardware win."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from cin.contracts import load_genome
from experiments.hardware.profile_signature_search import (
    amdahl_search_ceiling,
    load_manifest,
    run_study,
    run_workload,
    validate_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "experiments/hardware/manifest.v0.1.json"
BASE = load_genome(ROOT / "examples/seed-genome.v0.1.yaml")["genome"]["base"]


def test_frozen_manifest_includes_worlds_exhaustion_and_multi_input_probes():
    manifest = load_manifest(MANIFEST)
    assert manifest["protocol"] == "cin.hardware.h0.manifest/v0.1"
    workloads = {item["id"]: item for item in manifest["workloads"]}
    assert {"max2", "min2", "absdiff", "exhaustion", "search3"} <= workloads.keys()
    assert workloads["search3"]["kind"] == "search_only"
    assert workloads["search3"]["arity"] == 3
    assert workloads["exhaustion"]["max_proposals"] == 1
    assert len(manifest["screen_points"]) == 6


@pytest.mark.parametrize(
    "mutate",
    [
        lambda x: x.update(protocol="other"),
        lambda x: x["workloads"].append(copy.deepcopy(x["workloads"][0])),
        lambda x: x["workloads"][0].update(max_proposals=True),
        lambda x: x["workloads"][0].update(max_proposals=0),
        lambda x: x["workloads"][0].update(world="../private.yaml"),
        lambda x: x["workloads"][0].update(world="missing.yaml"),
        lambda x: x["workloads"][0].update(kind="search_only", world="world-max2.v0.1.yaml"),
        lambda x: x["workloads"][0].update(kind="world", arity=3),
        lambda x: x.update(screen_points=[]),
    ],
)
def test_manifest_rejects_invalid_and_unsafe_contracts(mutate):
    manifest = load_manifest(MANIFEST)
    mutate(manifest)
    with pytest.raises(ValueError):
        validate_manifest(manifest)


def test_repeated_world_search_is_identical_except_timing():
    workload = {"id": "exhaustion", "kind": "world", "world": "world-min2.v0.1.yaml",
                "arity": 2, "seed": 0, "max_proposals": 1}
    first = run_workload(workload, BASE)
    second = run_workload(workload, BASE)
    assert first["status"] == second["status"] == "UNKNOWN"
    assert first["proposals_seen"] == second["proposals_seen"] == 1
    assert first["trace_sha256"] == second["trace_sha256"]
    assert first["logical_counters"] == second["logical_counters"]
    assert first["candidate_hash"] is None
    assert first["times_ns"]["total_wall"] > 0
    assert first["times_ns"]["search_wall"] > 0
    assert first["attribution"]["signature_eligible_fraction"] == "UNRESOLVED"


def test_three_input_probe_workload_never_claims_world_verification():
    workload = {"id": "search3", "kind": "search_only", "arity": 3,
                "seed": 1, "max_proposals": 12}
    result = run_workload(workload, BASE)
    assert result["status"] == "SEARCH_ONLY"
    assert result["verifier_calls"] == 0
    assert result["logical_counters"]["probe_evaluations"] > 0
    assert result["candidate_hash"] is None


def test_study_uses_unprofiled_primary_samples_and_separate_profile_probe():
    source = load_manifest(MANIFEST)
    manifest = {**source, "workloads": [
        {"id": "exhaustion", "kind": "world", "world": "world-min2.v0.1.yaml",
         "arity": 2, "seed": 0, "max_proposals": 1}
    ]}
    result = run_study(manifest, repetitions=2, profile=True)
    assert result["protocol"] == "cin.hardware.h0.report/v0.1"
    assert len(result["runs"]) == 1
    run = result["runs"][0]
    assert len(run["samples"]) == 2
    assert run["samples"][0]["trace_sha256"] == run["samples"][1]["trace_sha256"]
    assert run["profile_diagnostic"]["trace_sha256"] == run["samples"][0]["trace_sha256"]
    assert run["profile_diagnostic"]["mode"] == "instrumented_cprofile"
    assert run["samples"][0]["profile"] is None
    assert run["amdahl_scope"] == "entire_search_stage_optimistic_upper_bound"
    assert result["hardware_speedup_claim"] == "NOT_MEASURED"
    assert json.dumps(result, allow_nan=False)


def test_amdahl_math_rejects_invalid_cases_and_unbounded_limit():
    assert amdahl_search_ceiling(0, 100) == 1.0
    assert amdahl_search_ceiling(50, 100) == 2.0
    assert amdahl_search_ceiling(100, 100) is None
    for values in [(0, 0), (-1, 10), (11, 10), (True, 10)]:
        with pytest.raises(ValueError):
            amdahl_search_ceiling(*values)


def test_study_rejects_invalid_repetition_count():
    manifest = load_manifest(MANIFEST)
    with pytest.raises(ValueError):
        run_study(manifest, repetitions=0, profile=False)
