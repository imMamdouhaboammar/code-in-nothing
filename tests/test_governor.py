"""P1-02: governor reservations prevent debt, double settlement and post-stop work."""

import pytest

from cin.governor import BudgetExceeded, Cost, Governor


def test_reservations_charge_only_actual_work_and_preserve_global_budget():
    gov = Governor(Cost(candidate_evaluations=5, verifier_calls=5, interpreter_operations=100))
    gov.register("a", Cost(candidate_evaluations=4, verifier_calls=4, interpreter_operations=100))
    gov.register("b", Cost(candidate_evaluations=4, verifier_calls=4, interpreter_operations=100))
    grant = gov.reserve(
        "a", Cost(candidate_evaluations=4, verifier_calls=2, interpreter_operations=30)
    )
    with pytest.raises(BudgetExceeded):
        gov.reserve("b", Cost(candidate_evaluations=2))
    gov.settle(grant, Cost(candidate_evaluations=2, verifier_calls=1, interpreter_operations=17))
    assert gov.snapshot("a").candidate_evaluations == 2
    assert gov.snapshot("a").interpreter_operations == 17
    gov.reserve("b", Cost(candidate_evaluations=3))
    assert gov.snapshot("b").candidate_evaluations == 0
    assert gov.remaining("b").candidate_evaluations == 1


def test_unknown_duplicate_negative_bool_and_overbudget_fail_closed():
    gov = Governor(Cost(candidate_evaluations=2))
    with pytest.raises(ValueError):
        Cost(candidate_evaluations=True)
    with pytest.raises(ValueError):
        Cost(candidate_evaluations=-1)
    gov.register("a", Cost(candidate_evaluations=2))
    with pytest.raises(ValueError):
        gov.register("a", Cost(candidate_evaluations=2))
    with pytest.raises(ValueError):
        gov.reserve("missing", Cost(candidate_evaluations=1))
    grant = gov.reserve("a", Cost(candidate_evaluations=1))
    with pytest.raises(BudgetExceeded):
        gov.settle(grant, Cost(candidate_evaluations=2))
    assert gov.stop_reason("a") == "GOVERNOR_VIOLATION"
    with pytest.raises(ValueError):
        gov.reserve("a", Cost(candidate_evaluations=1))


def test_grants_are_single_use_and_tied_to_one_governor():
    first = Governor(Cost(candidate_evaluations=3))
    second = Governor(Cost(candidate_evaluations=3))
    first.register("same", Cost(candidate_evaluations=3))
    second.register("same", Cost(candidate_evaluations=3))
    token = first.reserve("same", Cost(candidate_evaluations=1))
    with pytest.raises(ValueError):
        second.settle(token, Cost(candidate_evaluations=1))
    first.settle(token, Cost(candidate_evaluations=1))
    with pytest.raises(ValueError):
        first.settle(token, Cost(candidate_evaluations=1))
    assert first.stop("same", "BUDGET_EXHAUSTED")
    assert not first.stop("same", "BUDGET_EXHAUSTED")
    with pytest.raises(ValueError):
        first.reserve("same", Cost(candidate_evaluations=1))
