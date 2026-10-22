"""Negative and subprocess tests for the frozen R0 process-scoped RSS study."""

from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path

import pytest

from experiments import native_rss_control as rss


def _exhaustion() -> dict:
    return next(
        row
        for row in rss.load_manifest(rss.DEFAULT_MANIFEST)["workloads"]
        if row["id"] == "exhaustion"
    )


def test_v03_manifest_is_frozen_and_distinguishes_bool_from_int():
    manifest = rss.load_manifest(rss.DEFAULT_MANIFEST)
    assert manifest["source_commit"] == rss.REFERENCE_COMMIT
    assert manifest["repetitions"] == 2
    assert manifest["arms"] == ["generator", "list"]
    for change in (
        lambda x: x.update(seeds=[0, True, 2]),
        lambda x: x.update(repetitions=True),
        lambda x: x.update(arms=["generator", "rust"]),
        lambda x: x["workloads"][0].update(world="../private.yaml"),
        lambda x: x["workloads"][0].update(max_proposals=9999),
        lambda x: x.update(source_commit="unreviewed"),
    ):
        altered = copy.deepcopy(manifest)
        change(altered)
        with pytest.raises(ValueError, match="preregistered"):
            rss.validate_manifest(altered)


def test_fresh_subprocess_returns_process_scoped_rss_and_original_outcome():
    child = rss._run_child("exhaustion", 0, "generator")
    sample = child["sample"]
    assert sample["status"] == "UNKNOWN"
    assert sample["verifier_calls"] == 0
    assert child["rss_scope"] in (
        rss.RSS_SCOPE,
        "NOT_MEASURED_UNSUPPORTED_PLATFORM",
    )
    if child["rss_scope"] == rss.RSS_SCOPE:
        assert child["peak_rss_bytes"] >= child["peak_rss_before_workload_bytes"] > 0
    else:
        assert child["peak_rss_bytes"] is None
    assert child["subprocess_wall_ns"] >= sample["times_ns"]["total_wall"]
    assert child["subprocess_overhead_scope"].startswith("IMPORT_LAUNCH")


def test_missing_resource_memory_measurement_is_explicit_not_measured(monkeypatch):
    monkeypatch.setattr(rss, "_peak_rss", lambda: None)
    result = rss._child_sample("exhaustion", 0, "generator")
    assert result["peak_rss_bytes"] is None
    assert result["peak_rss_before_workload_bytes"] is None
    assert result["rss_scope"] == "NOT_MEASURED_UNSUPPORTED_PLATFORM"


def test_paired_memory_trial_alternates_arms_and_preserves_logical_equality():
    calls = []

    def child(workload_id, seed, arm):
        calls.append((workload_id, seed, arm))
        return rss._child_sample(workload_id, seed, arm)

    pair = rss.paired_memory_trial(_exhaustion(), seed=1, repetition=0, runner=child)
    assert calls == [("exhaustion", 1, "list"), ("exhaustion", 1, "generator")]
    assert pair["logical_equal"] is True
    assert pair["logical_sha256"]
    assert pair["samples"]["list"]["sample"]["status"] == "UNKNOWN"


def test_parity_mismatch_retains_both_arm_samples():
    def child(workload_id, seed, arm):
        result = rss._child_sample(workload_id, seed, arm)
        if arm == "list":
            result["sample"]["logical_counters"]["attempted_shapes"] += 1
        return result

    with pytest.raises(rss.DiagnosticFailure) as error:
        rss.paired_memory_trial(_exhaustion(), seed=0, repetition=0, runner=child)
    diagnostic = error.value.diagnostic
    assert diagnostic["reason"] == "LOGICAL_PARITY_MISMATCH"
    assert diagnostic["mismatched_fields"] == ["logical_counters"]
    assert set(diagnostic["completed_samples"]) == {"generator", "list"}


def test_child_process_failure_retains_completed_arm(monkeypatch):
    def fake(workload_id, seed, arm):
        if arm == "list":
            raise rss.DiagnosticFailure({"reason": "CHILD_NONZERO_EXIT", "returncode": 7})
        return rss._child_sample(workload_id, seed, arm)

    with pytest.raises(rss.DiagnosticFailure) as error:
        rss.paired_memory_trial(_exhaustion(), seed=0, repetition=0, runner=fake)
    assert error.value.diagnostic["reason"] == "CHILD_NONZERO_EXIT"
    assert set(error.value.diagnostic["completed_samples"]) == {"generator"}

    def bad_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 1, stdout="", stderr="private data")

    monkeypatch.setattr(rss.subprocess, "run", bad_run)
    with pytest.raises(rss.DiagnosticFailure) as child_error:
        rss._run_child("exhaustion", 0, "generator")
    assert child_error.value.diagnostic == {"reason": "CHILD_NONZERO_EXIT", "returncode": 1}
    assert "private data" not in str(child_error.value.diagnostic)


def test_child_malformed_success_payload_is_an_invalid_measurement(monkeypatch):
    def bad_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args[0],
            0,
            stdout=json.dumps(
                {
                    "sample": {"id": "wrong-world", "times_ns": {"total_wall": 50}},
                    "rss_scope": rss.RSS_SCOPE,
                    "peak_rss_bytes": 100,
                    "peak_rss_before_workload_bytes": 90,
                }
            ),
            stderr="",
        )

    monkeypatch.setattr(rss.subprocess, "run", bad_run)
    with pytest.raises(rss.DiagnosticFailure) as error:
        rss._run_child("exhaustion", 0, "list")
    assert error.value.diagnostic["reason"] == "CHILD_INVALID_OUTPUT"


def test_impossible_child_timing_is_not_silently_clamped(monkeypatch):
    def bad_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args[0],
            0,
            stdout=json.dumps(
                {
                    "sample": {"id": "exhaustion", "times_ns": {"total_wall": 10**15}},
                    "rss_scope": rss.RSS_SCOPE,
                    "peak_rss_bytes": 100,
                    "peak_rss_before_workload_bytes": 90,
                }
            ),
            stderr="",
        )

    monkeypatch.setattr(rss.subprocess, "run", bad_run)
    with pytest.raises(rss.DiagnosticFailure) as error:
        rss._run_child("exhaustion", 0, "list")
    assert error.value.diagnostic["reason"] == "CHILD_TIMING_INCONSISTENT"


def test_malformed_logical_record_keeps_both_samples():
    def bad_child(workload_id, seed, arm):
        result = rss._child_sample(workload_id, seed, arm)
        if arm == "list":
            del result["sample"]["logical_counters"]
        return result

    with pytest.raises(rss.DiagnosticFailure) as error:
        rss.paired_memory_trial(_exhaustion(), seed=0, repetition=0, runner=bad_child)
    assert error.value.diagnostic["reason"] == "MALFORMED_LOGICAL_RECORD"
    assert set(error.value.diagnostic["completed_samples"]) == {"generator", "list"}


def test_study_retains_prior_pairs_and_failure_without_perf_summary(monkeypatch):
    calls = 0

    def fake(workload, *, seed, repetition):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise rss.DiagnosticFailure(
                {"reason": "LOGICAL_PARITY_MISMATCH", "completed_samples": {}}
            )
        return {"workload": workload["id"], "samples": {}}

    monkeypatch.setattr(rss, "paired_memory_trial", fake)
    result = rss.run_study(rss.load_manifest(rss.DEFAULT_MANIFEST))
    assert result["paired_samples"] == 1
    assert result["summary"] == []
    assert result["status"] == "INVALID"
    assert result["decision"] == "INVALID_CONTROL_NO_NATIVE_GO"
    assert result["failure"]["reason"] == "LOGICAL_PARITY_MISMATCH"


def test_input_hashes_cover_genome_worlds_and_schemas():
    hashes = rss._inputs_sha256()
    assert "examples/seed-genome.v0.1.yaml" in hashes
    assert "examples/world-max2.v0.1.yaml" in hashes
    assert any(path.startswith("schemas/") for path in hashes)
    assert all(len(digest) == 64 for digest in hashes.values())


def test_cli_refuses_overwrite_before_launching_children(tmp_path, monkeypatch, capsys):
    path = tmp_path / "existing.json"
    path.write_text("untouched", encoding="utf-8")

    def unexpected(*args):
        pytest.fail("should not run any child or study")

    monkeypatch.setattr(rss, "run_study", unexpected)
    with pytest.raises(SystemExit) as error:
        rss.main(["--output", str(path)])
    assert error.value.code == 2
    assert path.read_text(encoding="utf-8") == "untouched"
    assert "new file" in capsys.readouterr().err


def test_child_cli_rejects_arbitrary_workload_without_execution(capsys):
    with pytest.raises(SystemExit) as error:
        rss.main(["--child-workload", "../private.yaml", "--seed", "0", "--arm", "generator"])
    assert error.value.code == 2
    assert "unregistered" in capsys.readouterr().err


def test_child_output_remains_json_serializable():
    record = rss._child_sample("exhaustion", 0, "list")
    assert json.loads(json.dumps(record, allow_nan=False))["sample"]["status"] == "UNKNOWN"


def test_manifest_file_exists_at_repository_scoped_location():
    assert rss.DEFAULT_MANIFEST == Path(rss.__file__).with_name("native-rss-control.v0.3.json")
