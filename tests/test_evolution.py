from copy import deepcopy
from pathlib import Path

from cin.archive import Archive
from cin.contracts import load_genome, load_world
from cin.evolution import Experiment, spawn_verified
from cin.ir import canonical_hash

ROOT = Path(__file__).resolve().parents[1]
GENOME = load_genome(ROOT / "examples/seed-genome.v0.1.yaml")
WORLD = load_world(ROOT / "examples/world-max2.v0.1.yaml")


def test_unverified_skill_cannot_spawn():
    parent = {"id": "parent", "genome": deepcopy(GENOME), "skills": {}}
    try:
        spawn_verified(parent, {}, [], child_id="child")
    except ValueError:
        pass
    else:
        assert False, "unverified offspring must be rejected"


def test_accepted_growth_inherited_with_frozen_contracts(tmp_path):
    ex = Experiment(deepcopy(GENOME), deepcopy(WORLD), Archive(tmp_path), seed=0, max_evals=250)
    report = ex.run()
    assert report["verified_capabilities"] >= 1, report
    assert report["world_mutation_admitted"] is True
    assert report["offspring_count"] == 1
    assert report["offspring_inherited_skill_hashes"] == report["parent_skill_hashes"]
    assert report["parents_contracts_equal"] is True
    assert report["maturity_status"] == "NOT_EVALUATED"
    kinds = [x["kind"] for x in ex.archive.events]
    assert "GROWTH_ACCEPTED" in kinds and "OFFSPRING_BORN" in kinds
    assert "ARCHIVED" in kinds


def test_budget_cutoff_and_idempotent_archive(tmp_path):
    ex = Experiment(deepcopy(GENOME), deepcopy(WORLD), Archive(tmp_path), seed=0, max_evals=1)
    report = ex.run()
    assert report["stop_reason"] == "BUDGET_EXHAUSTED"
    assert report["offspring_count"] == 0
    before = len(ex.archive.events)
    ex.archive.terminal_archive("organism-0", {"stop_reason": report["stop_reason"]})
    assert len(ex.archive.events) == before


def test_fixed_seed_replay_has_equal_outcomes(tmp_path):
    a = Experiment(
        deepcopy(GENOME), deepcopy(WORLD), Archive(tmp_path / "a"), seed=0, max_evals=250
    ).run()
    b = Experiment(
        deepcopy(GENOME), deepcopy(WORLD), Archive(tmp_path / "b"), seed=0, max_evals=250
    ).run()
    keys = (
        "verified_capabilities",
        "parent_skill_hashes",
        "offspring_inherited_skill_hashes",
        "candidate_evaluations",
        "world_mutation_admitted",
        "stop_reason",
    )
    assert {k: a[k] for k in keys} == {k: b[k] for k in keys}


def test_disable_world_evolution_is_real_ablation(tmp_path):
    ex = Experiment(
        deepcopy(GENOME),
        deepcopy(WORLD),
        Archive(tmp_path),
        seed=0,
        max_evals=250,
        world_evolution=False,
    )
    report = ex.run()
    assert report["world_mutation_admitted"] is False
    assert report["offspring_count"] == 0


def test_forged_heritability_certificates_are_rechecked(tmp_path):
    from cin.worlds import expand_domain

    bad_expr = {"op": "Arg", "index": 0}
    w2 = expand_domain(WORLD, 1)
    parent = {
        "id": "parent",
        "genome": deepcopy(GENOME),
        "skills": {canonical_hash(WORLD): bad_expr, canonical_hash(w2): bad_expr},
    }
    certificates = [
        {
            "status": "PASS",
            "world_hash": canonical_hash(w),
            "program_hash": canonical_hash(bad_expr),
        }
        for w in (WORLD, w2)
    ]
    try:
        spawn_verified(
            parent,
            {"expression": bad_expr, "hash": canonical_hash(bad_expr)},
            certificates,
            child_id="child",
            worlds=[WORLD, w2],
        )
    except ValueError:
        pass
    else:
        assert False, "a fabricated pass must not become inherited growth"


def test_archive_detects_tampering(tmp_path):
    archive = Archive(tmp_path)
    archive.append("BIRTH", {"organism_id": "x"})
    assert Archive.verify_chain(archive.journal)
    payload = archive.journal.read_text().replace('"organism_id":"x"', '"organism_id":"y"')
    archive.journal.write_text(payload)
    assert not Archive.verify_chain(archive.journal)


def test_growth_evidence_matches_v03_schema(tmp_path):
    import json

    from jsonschema import Draft202012Validator

    schema = json.loads((ROOT / "schemas/growth-evidence.v0.1.schema.json").read_text())
    ex = Experiment(deepcopy(GENOME), deepcopy(WORLD), Archive(tmp_path), seed=0, max_evals=250)
    ex.run()
    evidence = [
        event["payload"] for event in ex.archive.events if event["kind"] == "GROWTH_EVIDENCE"
    ]
    assert evidence
    assert all(not list(Draft202012Validator(schema).iter_errors(row)) for row in evidence)
    assert any(row["resources"]["interpreter_operations"] > 0 for row in evidence)


def test_single_epoch_respects_directive_proposals_per_epoch(tmp_path):
    altered = deepcopy(GENOME)
    altered["genome"]["directive"]["proposals_per_epoch"] = 10
    ex = Experiment(altered, deepcopy(WORLD), Archive(tmp_path), seed=0, max_evals=250)
    report = ex.run()
    assert report["candidate_evaluations"] == 10
    assert report["verified_capabilities"] == 0
    assert report["stop_reason"] == "EPOCH_COMPLETE"


def test_negative_rng_seed_is_rejected(tmp_path):
    import pytest

    with pytest.raises(ValueError):
        Experiment(deepcopy(GENOME), deepcopy(WORLD), Archive(tmp_path), seed=-1)
