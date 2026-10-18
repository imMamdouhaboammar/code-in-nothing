"""P1-02: real finite-world scheduler uses task-blind CIN candidates."""

from copy import deepcopy
from pathlib import Path

from cin.contracts import load_genome, load_world
from cin.scheduler import FiniteScheduler

ROOT = Path(__file__).resolve().parents[1]
GENOME = load_genome(ROOT / "examples/seed-genome.v0.1.yaml")
WORLD = load_world(ROOT / "examples/world-max2.v0.1.yaml")


def bounded_genome(*, epochs=3, proposals=1, plateau=5, grace=1):
    genome = deepcopy(GENOME)
    genome["genome"]["stop_station"]["max_epochs"] = epochs
    genome["genome"]["stop_station"]["plateau_consecutive_epochs"] = plateau
    genome["genome"]["stop_station"]["plateau_grace_epochs"] = grace
    genome["genome"]["directive"]["proposals_per_epoch"] = proposals
    return genome


def test_finite_epochs_use_actual_verifier_and_track_world_admission():
    runner = FiniteScheduler(bounded_genome(), WORLD, seed=0, max_evals=10)
    report = runner.run()
    assert report["world_admission"] == "ADMITTED"
    assert report["epochs"] == 3
    assert report["candidate_evaluations"] == 3
    assert report["stop_reason"] == "EPOCH_LIMIT"
    assert report["verified_capabilities"] == 0
    assert report["cost"]["admission_candidates"] > 0
    assert report["cost"]["verifier_calls"] >= report["cost"]["admission_candidates"] + 3
    assert report["cost"]["interpreter_operations"] > 0
    assert report["cost"]["search_shapes"] >= 0
    assert report["terminal_events"] == 1
    assert runner.run() == report


def test_plateau_stop_uses_configured_grace_and_does_not_continue():
    runner = FiniteScheduler(bounded_genome(epochs=6, plateau=2, grace=1), WORLD, max_evals=20)
    report = runner.run()
    assert report["stop_reason"] == "PLATEAU"
    assert report["epochs"] == 2
    assert report["candidate_evaluations"] == 2
    assert report["terminal_events"] == 1


def test_admission_exhaustion_bills_witness_search_without_candidate_success():
    runner = FiniteScheduler(bounded_genome(), WORLD, max_evals=3, admission_budget=1)
    report = runner.run()
    assert report["world_admission"] == "UNKNOWN"
    assert report["verified_capabilities"] == 0
    assert report["candidate_evaluations"] == 0
    assert report["cost"]["admission_candidates"] == 1
    assert report["cost"]["verifier_calls"] >= 1
    assert report["stop_reason"] == "WORLD_NOT_ADMITTED"


def test_candidate_budget_is_global_across_epochs_not_reset():
    runner = FiniteScheduler(bounded_genome(epochs=8), WORLD, max_evals=2)
    report = runner.run()
    assert report["candidate_evaluations"] == 2
    assert report["epochs"] == 2
    assert report["stop_reason"] == "CANDIDATE_BUDGET"
    assert report["terminal_events"] == 1


def test_verified_seed_is_not_new_synthesis_and_is_never_mutated():
    genome = bounded_genome()
    genome["genome"]["base"]["starting_expression"] = {
        "op": "If",
        "args": [
            {"op": "LessThan", "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 1}]},
            {"op": "Arg", "index": 1},
            {"op": "Arg", "index": 0},
        ],
    }
    before = deepcopy(genome)
    runner = FiniteScheduler(genome, WORLD, max_evals=2)
    report = runner.run()
    assert report["stop_reason"] == "SEED_ALREADY_SOLVED"
    assert report["verified_capabilities"] == 0
    assert report["candidate_evaluations"] == 0
    assert genome == before


def test_run_is_deterministic_with_same_seed_and_inputs():
    a = FiniteScheduler(bounded_genome(), WORLD, max_evals=3).run()
    b = FiniteScheduler(bounded_genome(), WORLD, max_evals=3).run()
    assert a == b
