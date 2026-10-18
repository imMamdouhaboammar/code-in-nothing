"""P1-01: deterministic manifests and independent completed-run replay."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from cin.archive import Archive
from cin.contracts import load_genome, load_world
from cin.evolution import Experiment
from cin.ir import canonical_bytes, canonical_hash

ROOT = Path(__file__).resolve().parents[1]
GENOME = load_genome(ROOT / "examples/seed-genome.v0.1.yaml")
WORLD = load_world(ROOT / "examples/world-max2.v0.1.yaml")


def run_pilot(path: Path, *, max_evals: int = 1) -> dict:
    return Experiment(
        deepcopy(GENOME),
        deepcopy(WORLD),
        Archive(path),
        seed=0,
        max_evals=max_evals,
        world_evolution=False,
        inheritance=False,
    ).run()


def rewrite_chain(path: Path, events: list[dict]) -> None:
    previous_hash = "GENESIS"
    with path.open("wb") as output:
        for sequence, event in enumerate(events):
            event["sequence"] = sequence
            event["previous_hash"] = previous_hash
            event.pop("hash", None)
            previous_hash = canonical_hash(event)
            event["hash"] = previous_hash
            output.write(canonical_bytes(event) + b"\n")


def test_completed_run_has_immutable_versioned_manifest_and_replays(tmp_path):
    report = run_pilot(tmp_path)
    assert report["archive_chain_valid"]
    manifest, trace = Archive.read_normalized_trace(tmp_path)
    assert manifest["schema_version"] == "cin.cohort/v0.1"
    assert manifest["configuration"]["seed"] == 0
    assert manifest["configuration"]["genome"] == GENOME
    assert manifest["configuration"]["world"] == WORLD
    assert manifest["configuration"]["resource_policy"]["max_evals"] == 1
    assert trace[0]["kind"] == "COHORT_MANIFEST"
    assert trace[-1]["kind"] == "ARCHIVED"

    from cin.evolution import replay_experiment

    replay_report = replay_experiment(tmp_path)
    assert replay_report["stop_reason"] == report["stop_reason"]
    assert replay_report["candidate_evaluations"] == report["candidate_evaluations"]


def test_equivalent_runs_have_identical_normalized_trace(tmp_path):
    run_pilot(tmp_path / "a")
    run_pilot(tmp_path / "b")
    assert Archive.read_normalized_trace(tmp_path / "a") == Archive.read_normalized_trace(
        tmp_path / "b"
    )


def test_replay_ignores_only_nonscientific_cpu_timing(tmp_path):
    run_pilot(tmp_path)
    journal = tmp_path / "events.jsonl"
    before = Archive.read_normalized_trace(tmp_path)
    events = [json.loads(line) for line in journal.read_text().splitlines()]
    evidence = next(event for event in events if event["kind"] == "GROWTH_EVIDENCE")
    evidence["payload"]["resources"]["cpu_ms"] += 12345
    rewrite_chain(journal, events)
    assert Archive.read_normalized_trace(tmp_path) == before

    from cin.evolution import replay_experiment

    assert replay_experiment(tmp_path)["archive_chain_valid"]


def test_missing_tampered_or_unknown_version_manifest_fails_closed(tmp_path):
    run_pilot(tmp_path)
    path = tmp_path / "manifest.json"
    original = json.loads(path.read_text())
    path.unlink()
    with pytest.raises(ValueError):
        Archive.read_normalized_trace(tmp_path)
    path.write_bytes(canonical_bytes(original) + b"\n")
    altered = deepcopy(original)
    altered["configuration"]["seed"] += 1
    path.write_bytes(canonical_bytes(altered) + b"\n")
    with pytest.raises(ValueError):
        Archive.read_normalized_trace(tmp_path)
    altered = deepcopy(original)
    altered["schema_version"] = "cin.cohort/v999"
    path.write_bytes(canonical_bytes(altered) + b"\n")
    with pytest.raises(ValueError):
        Archive.read_normalized_trace(tmp_path)


def test_truncated_or_corrupt_journal_is_not_a_completed_replay(tmp_path):
    run_pilot(tmp_path)
    journal = tmp_path / "events.jsonl"
    events = [json.loads(line) for line in journal.read_text().splitlines()]
    rewrite_chain(journal, events[:-1])
    assert Archive.verify_chain(journal)
    with pytest.raises(ValueError):
        Archive.read_normalized_trace(tmp_path)
    journal.write_text('{"partial":')
    with pytest.raises(ValueError):
        Archive.read_normalized_trace(tmp_path)


def test_replay_detects_policy_drift_even_when_hashes_are_recomputed(tmp_path):
    run_pilot(tmp_path)
    manifest_path = tmp_path / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["configuration"]["resource_policy"]["max_evals"] = 2
    manifest_path.write_bytes(canonical_bytes(manifest) + b"\n")
    journal = tmp_path / "events.jsonl"
    events = [json.loads(line) for line in journal.read_text().splitlines()]
    events[0]["payload"]["manifest_hash"] = canonical_hash(manifest)
    rewrite_chain(journal, events)

    from cin.evolution import replay_experiment

    with pytest.raises(ValueError, match="divergence"):
        replay_experiment(tmp_path)


def test_legacy_archive_chain_works_but_cannot_claim_replay(tmp_path):
    archive = Archive(tmp_path)
    archive.append("BIRTH", {"organism_id": "legacy"})
    assert Archive.verify_chain(archive.journal)
    with pytest.raises(ValueError):
        Archive.read_normalized_trace(tmp_path)
