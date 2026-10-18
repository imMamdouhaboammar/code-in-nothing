"""Opt-in public training feedback must not weaken finite-domain verification."""

from copy import deepcopy
from pathlib import Path

import pytest

from cin.contracts import load_genome, load_world
from cin.governor import Cost
from cin.ir import Limits, canonical_hash, check_tree
from cin.training import GuidedFrontier, PublicTrainingPanel, evaluate_training
from cin.worlds import verify_program

ROOT = Path(__file__).resolve().parents[1]
BASE = load_genome(ROOT / "examples/seed-genome.v0.1.yaml")["genome"]["base"]
WORLD = load_world(ROOT / "examples/world-min2.v0.1.yaml")
LEFT = {"op": "Arg", "index": 0}
RIGHT = {"op": "Arg", "index": 1}
CASES = ((-4, -1), (1, -4), (0, 0), (-2, 3), (3, -2))


def test_three_of_five_is_graded_but_not_a_proof():
    panel = PublicTrainingPanel(WORLD, CASES)
    score = evaluate_training(LEFT, panel, BASE)
    assert score.status == "COMPLETE"
    assert score.applicable_cases == 5
    assert score.satisfied_cases == 3
    assert score.pass_fraction == 0.6
    assert score.case_errors == (0, 1, 0, 0, 1)
    assert score.candidate_hash == canonical_hash(LEFT)
    assert score.panel_hash == panel.digest
    assert score.cost.training_cases == 5
    assert score.cost.training_interpreter_operations >= 5
    assert score.cost.predicate_evaluations >= 5
    assert verify_program(LEFT, WORLD, BASE).status == "FAIL"


def test_per_case_vector_distinguishes_equal_aggregate_scores():
    panel = PublicTrainingPanel(WORLD, CASES)
    left = evaluate_training(LEFT, panel, BASE)
    right = evaluate_training(RIGHT, panel, BASE)
    assert left.pass_fraction == right.pass_fraction == 0.6
    assert left.case_errors != right.case_errors


def test_perfect_public_training_is_not_independent_verification():
    panel = PublicTrainingPanel(WORLD, ((-4, -1), (-2, 3), (0, 0)))
    score = evaluate_training(LEFT, panel, BASE)
    assert score.pass_fraction == 1.0
    assert verify_program(LEFT, WORLD, BASE).status == "FAIL"


def test_panel_immutable_digest_replay_and_duplicate_rejection():
    source = deepcopy(WORLD)
    panel = PublicTrainingPanel(source, CASES)
    digest = panel.digest
    source["id"] = "tampered"
    assert panel.digest == digest
    assert panel.world["id"] == WORLD["id"]
    assert evaluate_training(LEFT, panel, BASE) == evaluate_training(LEFT, panel, BASE)
    assert PublicTrainingPanel(deepcopy(WORLD), CASES).digest == digest
    with pytest.raises(ValueError, match="duplicate"):
        PublicTrainingPanel(WORLD, (CASES[0], CASES[0]))
    with pytest.raises(ValueError):
        PublicTrainingPanel(WORLD, ())


def test_incomplete_scoring_never_fabricates_zero_fitness():
    panel = PublicTrainingPanel(WORLD, CASES)
    invalid = evaluate_training({"op": "Arg", "index": 100}, panel, BASE)
    assert invalid.status == "INVALID"
    assert invalid.pass_fraction is None
    add = {"op": "Add", "args": [LEFT, RIGHT]}
    exhausted = evaluate_training(add, panel, BASE, limits=Limits(max_ops=1))
    assert exhausted.status == "UNKNOWN"
    assert exhausted.pass_fraction is None


def test_inapplicable_cases_and_no_vacuous_fitness():
    world = deepcopy(WORLD)
    world["precondition"] = {"gte": ["x", 0]}
    panel = PublicTrainingPanel(world, ((-4, -1), (-2, 3)))
    result = evaluate_training(LEFT, panel, BASE)
    assert result.status == "VACUOUS"
    assert result.pass_fraction is None
    assert result.case_errors == (None, None)


def test_guided_frontier_changes_selected_parent_using_public_feedback():
    first = PublicTrainingPanel(WORLD, ((-4, -1), (-2, 3), (1, -4)))
    second = PublicTrainingPanel(WORLD, ((1, -4), (3, -2), (-4, -1)))
    a, b = GuidedFrontier(BASE, seed=17), GuidedFrontier(BASE, seed=17)
    for expr in (LEFT, RIGHT):
        a.add(expr, evaluate_training(expr, first, BASE))
        b.add(expr, evaluate_training(expr, second, BASE))
    parent_a, parent_b = a.select(), b.select()
    assert parent_a == LEFT
    assert parent_b == RIGHT
    assert a.select() == parent_a
    assert a.neighbors(parent_a) != b.neighbors(parent_b)
    assert all(check_tree(expr, BASE) == "Int" for expr in a.neighbors(parent_a))


def test_guided_frontier_refuses_unknown_and_foreign_training_evidence():
    panel = PublicTrainingPanel(WORLD, CASES)
    frontier = GuidedFrontier(BASE, seed=0, max_pool=3)
    with pytest.raises(ValueError):
        frontier.add(LEFT, evaluate_training({"op": "Arg", "index": 99}, panel, BASE))
    frontier.add(LEFT, evaluate_training(LEFT, panel, BASE))
    with pytest.raises(ValueError):
        frontier.add(RIGHT, evaluate_training(RIGHT, PublicTrainingPanel(WORLD, ((0, 0),)), BASE))
    assert len(frontier.neighbors(frontier.select())) <= 32
    assert Cost(training_cases=1).training_cases == 1
