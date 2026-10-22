"""Differential controls for opt-in signature tuple materialization."""

from __future__ import annotations

import copy
import json
from dataclasses import asdict
from pathlib import Path

import pytest

from cin.contracts import load_genome
from cin.ir import canonical_hash
from cin.search import SearchStats, candidate_stream
from experiments.hardware.profile_signature_search import run_workload
from experiments.native_python_control import (
    DEFAULT_MANIFEST,
    load_control_protocol,
    paired_workload,
)

ROOT = Path(__file__).resolve().parents[1]
BASE = load_genome(ROOT / "examples/seed-genome.v0.1.yaml")["genome"]["base"]


def _snapshot(seed: int, limit: int, mode: str, base: dict = BASE) -> tuple[list, dict]:
    stats = SearchStats()
    proposals = list(
        candidate_stream(
            base["starting_expression"],
            base,
            seed=seed,
            max_proposals=limit,
            stats=stats,
            _composition_mode=mode,
        )
    )
    return [(canonical_hash(p.expression), p.operator) for p in proposals], asdict(stats)


def test_control_manifest_is_frozen_and_rejects_path_injection():
    protocol = load_control_protocol(DEFAULT_MANIFEST)
    assert protocol["seeds"] == [0, 1, 2]
    assert protocol["repetitions"] == 5
    assert protocol["arms"] == ["generator", "list"]
    assert len(protocol["workloads"]) == 6
    for change in [
        lambda data: data.update(repetitions=True),
        lambda data: data.update(seeds=[0, 0, 2]),
        lambda data: data.update(seeds=[0, True, 2]),
        lambda data: data.update(arms=["list", "rust"]),
        lambda data: data["workloads"][0].update(world="../private.yaml"),
        lambda data: data["workloads"][0].update(max_proposals=99),
        lambda data: data["workloads"][3].update(max_proposals=True),
    ]:
        altered = copy.deepcopy(protocol)
        change(altered)
        from experiments.native_python_control import validate_control_protocol

        with pytest.raises(ValueError):
            validate_control_protocol(altered)


@pytest.mark.parametrize("seed", [0, 1, 3])
def test_candidate_trace_order_and_counters_match_without_changing_default(seed):
    reference, counters = _snapshot(seed, 350, "generator")
    control, control_counters = _snapshot(seed, 350, "list")
    default = list(
        candidate_stream(BASE["starting_expression"], BASE, seed=seed, max_proposals=350)
    )
    assert reference == control
    assert reference == [(canonical_hash(p.expression), p.operator) for p in default]
    assert counters == control_counters
    assert any(operator == "insert_conditional" for _, operator in reference)


def test_three_input_search_has_exact_observational_pruning_parity():
    base = copy.deepcopy(BASE)
    base["cin_ir_version"] = "0.2"
    base["input_types"] = ["Int"] * 3
    for seed in (0, 1):
        assert _snapshot(seed, 80, "generator", base) == _snapshot(seed, 80, "list", base)


def test_unrecognized_search_composition_is_rejected_without_running():
    with pytest.raises(ValueError, match="composition"):
        list(candidate_stream(BASE["starting_expression"], BASE, _composition_mode="rust"))


def test_h0_signature_profile_still_identifies_all_five_generator_sites():
    from experiments.hardware.profile_signature_search import _signature_generator_lines

    assert len(_signature_generator_lines()) == 5


@pytest.mark.parametrize("seed", [0, 1])
def test_integrated_full_workload_trace_and_cost_parity(seed):
    workload = {
        "id": "search3" if seed else "min2",
        "kind": "search_only" if seed else "world",
        "arity": 3 if seed else 2,
        "seed": seed,
        "max_proposals": 80 if seed else 100,
    }
    if seed == 0:
        workload["world"] = "world-min2.v0.1.yaml"
    a = run_workload(workload, BASE, composition_mode="generator")
    b = run_workload(workload, BASE, composition_mode="list")

    def time_independent(r):
        return {k: v for k, v in r.items() if k not in {"times_ns", "profile"}}

    assert time_independent(a) == time_independent(b)
    assert a["times_ns"]["total_wall"] > 0


def test_paired_control_retains_unknown_and_exact_per_arm_records():
    exhaustion = {
        "id": "exhaustion",
        "kind": "world",
        "world": "world-min2.v0.1.yaml",
        "arity": 2,
        "seed": 0,
        "max_proposals": 1,
    }
    pair = paired_workload(exhaustion, BASE, seed=1, repetition=0)
    assert pair["first_arm"] == "list"
    assert set(pair["samples"]) == {"generator", "list"}
    assert all(row["status"] == "UNKNOWN" for row in pair["samples"].values())
    assert pair["logical_sha256"] and pair["logical_equal"] is True
    assert json.dumps(pair, allow_nan=False)


def test_pair_refuses_silent_parity_mismatch(monkeypatch):
    import experiments.native_python_control as runner

    real_workload = runner.run_workload

    def divergent(workload, base, *, composition_mode):
        value = real_workload(workload, base, composition_mode=composition_mode)
        if composition_mode == "list":
            value["logical_counters"]["attempted_shapes"] += 1
        return value

    monkeypatch.setattr(runner, "run_workload", divergent)
    workload = {
        "id": "exhaustion",
        "kind": "world",
        "world": "world-min2.v0.1.yaml",
        "arity": 2,
        "seed": 0,
        "max_proposals": 1,
    }
    with pytest.raises(RuntimeError, match="parity"):
        paired_workload(workload, BASE, seed=0, repetition=0)


def test_cli_refuses_output_overwrite_before_any_measurement(tmp_path, monkeypatch, capsys):
    import experiments.native_python_control as runner

    target = tmp_path / "existing.json"
    target.write_text("preserved", encoding="utf-8")

    def unexpected_measurement(protocol):
        pytest.fail("existing evidence must not be overwritten or remeasured")

    monkeypatch.setattr(runner, "run_control", unexpected_measurement)
    with pytest.raises(SystemExit) as error:
        runner.main(["--output", str(target)])
    assert error.value.code == 2
    assert "new path" in capsys.readouterr().err
    assert target.read_text(encoding="utf-8") == "preserved"
