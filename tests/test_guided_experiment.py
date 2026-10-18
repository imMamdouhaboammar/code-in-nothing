"""Causal ablation checks: measurement alone cannot change baseline generation."""

from pathlib import Path

import pytest

from cin.contracts import load_genome, load_world
from cin.guided_experiment import ARMS, run_trial
from cin.ir import canonical_hash
from cin.training import PublicTrainingPanel

ROOT = Path(__file__).resolve().parents[1]
BASE = load_genome(ROOT / "examples/seed-genome.v0.1.yaml")["genome"]["base"]
MIN2 = load_world(ROOT / "examples/world-min2.v0.1.yaml")
MAX2 = load_world(ROOT / "examples/world-max2.v0.1.yaml")
POINTS = ((-4, -1), (1, -4), (0, 0), (-2, 3), (3, -2))


def test_measuring_fitness_does_not_change_baseline_candidate_stream():
    panel = PublicTrainingPanel(MIN2, POINTS)
    b0 = run_trial("B0", MIN2, BASE, panel, max_proposals=20)
    b1 = run_trial("B1", MIN2, BASE, panel, max_proposals=20)
    assert b0["candidate_hashes"] == b1["candidate_hashes"]
    assert b0["selected_parent_hashes"] == b1["selected_parent_hashes"] == []
    assert b0["cost"]["training_cases"] == 0
    assert b1["cost"]["training_cases"] > 0
    assert b1["cost"]["training_interpreter_operations"] > 0
    assert b0["verified_program_hash"] == b1["verified_program_hash"]
    assert b0["cost"]["verifier_calls"] == b1["cost"]["verifier_calls"]


def test_training_changes_future_search_frontier_not_just_ranking():
    panel = PublicTrainingPanel(MIN2, POINTS)
    b0 = run_trial("B0", MIN2, BASE, panel, max_proposals=24, seed=7)
    b2 = run_trial("B2", MIN2, BASE, panel, max_proposals=24, seed=7)
    bootstrap = 6
    assert b2["candidate_hashes"][:bootstrap] == b0["candidate_hashes"][:bootstrap]
    assert b2["selected_parent_hashes"], "no parent was selected from feedback"
    assert b2["candidate_hashes"][bootstrap:] != b0["candidate_hashes"][bootstrap:]
    assert b2["cost"]["selection_operations"] > 0
    assert b2["cost"]["mutation_attempts"] > 0
    assert b2["cost"]["training_cases"] > 0
    assert b2["inherited_capability"] is False


def test_replay_is_deterministic_except_cpu_timing():
    panel = PublicTrainingPanel(MIN2, POINTS)
    first = run_trial("B2", MIN2, BASE, panel, max_proposals=20, seed=3)
    second = run_trial("B2", MIN2, BASE, panel, max_proposals=20, seed=3)
    first.pop("cpu_seconds")
    second.pop("cpu_seconds")
    assert first == second


def test_all_arms_preserve_independent_verification_and_cost_bounds():
    panel = PublicTrainingPanel(MAX2, POINTS)
    for arm in ARMS:
        report = run_trial(arm, MAX2, BASE, panel, max_proposals=10)
        assert report["protocol"] == "cin.guided-ablation/v0.1"
        assert report["world_hash"] == canonical_hash(MAX2)
        assert report["proposals_evaluated"] <= 10
        assert report["cost"]["candidate_evaluations"] == report["proposals_evaluated"]
        assert report["cost"]["verifier_calls"] == report["proposals_evaluated"]
        assert report["cost"]["verifier_cases"] <= 10 * 289
        assert report["status"] in ("PASS", "UNKNOWN")
        if report["status"] == "PASS":
            assert report["verified_program_hash"]
            assert report["verdict_counts"]["PASS"] == 1
        assert report["admission"] == "not_run"


def test_invalid_arms_and_panel_mixing_are_rejected():
    panel = PublicTrainingPanel(MIN2, POINTS)
    with pytest.raises(ValueError):
        run_trial("B3", MIN2, BASE, panel)
    with pytest.raises(ValueError):
        run_trial("B0", MAX2, BASE, panel)
    with pytest.raises(ValueError):
        run_trial("B2", MIN2, BASE, panel, max_proposals=0)
