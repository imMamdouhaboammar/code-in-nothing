import copy
import json
import subprocess
from pathlib import Path

import pytest

from experiments import native_baseline
from experiments.native_baseline import (
    DEFAULT_MANIFEST,
    compose_batch,
    fingerprint,
    load_protocol,
    measure,
    paired_composition,
)


def test_protocol_freezes_reference_seeds_workloads_and_stopping_rule():
    protocol = load_protocol(DEFAULT_MANIFEST)
    assert protocol["seeds"] == [0, 1, 2]
    assert protocol["repetitions"] == 5
    assert protocol["guided_arms"] == ["B0", "B1", "B2"]
    assert {"max2", "min2", "absdiff", "exhaustion", "search3", "search3-large"} <= {
        row["id"] for row in protocol["workloads"]
    }
    assert protocol["native_go"] == "REQUIRES_END_TO_END_PARITY_AND_2X"


def test_manifest_cannot_change_protocol_or_inject_private_task_paths(tmp_path):
    protocol = load_protocol(DEFAULT_MANIFEST)
    for change in [
        lambda p: p.update(repetitions=True),
        lambda p: p.update(seeds=[0, 0]),
        lambda p: p["workloads"][0].update(world="../private.yaml"),
        lambda p: p.update(native_go="GO"),
    ]:
        data = copy.deepcopy(protocol)
        change(data)
        path = tmp_path / "invalid.json"
        path.write_text(json.dumps(data))
        with pytest.raises(ValueError):
            load_protocol(path)


@pytest.mark.parametrize("op", ["Add", "Sub", "LessThan", "Equal"])
def test_composition_control_matches_exact_python_values_and_types(op):
    pairs = (((-(2**70), 2**70, 0), (1, -1, 0)),)
    reference = compose_batch(pairs, op, "generator")
    candidate = compose_batch(pairs, op, "list")
    assert candidate == reference
    assert [[type(v) for v in row] for row in candidate] == [
        [type(v) for v in row] for row in reference
    ]
    assert all(type(v) is (bool if op in ("LessThan", "Equal") else int) for v in candidate[0])


def test_paired_control_counts_exact_scalar_work_and_rejects_unknown_arm():
    pairs = (((1, 2), (3, 4)), ((-1, 0), (1, 0)))
    result = paired_composition(pairs, repetitions=2, iterations=3)
    assert len(result["pairs"]) == 8
    assert result["scalar_operations_per_sample"] == 12
    assert result["scope"] == "ISOLATED_COMPOSITION_NOT_END_TO_END"
    assert {r["first_arm"] for r in result["pairs"]} == {"generator", "list"}
    with pytest.raises(ValueError):
        compose_batch(pairs, "Add", "rust")


def test_measure_keeps_outcomes_separate_from_time_and_memory():
    sample = measure(lambda: {"status": "UNKNOWN", "count": 3})
    assert sample["result"] == {"status": "UNKNOWN", "count": 3}
    assert sample["wall_ns"] > 0 and sample["process_cpu_ns"] >= 0
    assert sample["rss_scope"] == "PROCESS_LIFETIME_HIGH_WATER_MARK"
    assert fingerprint(sample["result"]) == fingerprint({"count": 3, "status": "UNKNOWN"})


def test_characterization_fixture_is_external_to_current_implementation():
    fixture = json.loads(
        Path(__file__).with_name("fixtures").joinpath("r0-search-v0.1.json").read_text()
    )
    from dataclasses import asdict

    from cin.contracts import load_genome
    from cin.ir import canonical_hash, run_ir_args
    from cin.search import SearchStats, candidate_stream

    root = Path(__file__).resolve().parents[1]
    base = load_genome(root / "examples/seed-genome.v0.1.yaml")["genome"]["base"]
    for corpus in fixture["corpora"]:
        stats = SearchStats()
        proposals = list(
            candidate_stream(
                base["starting_expression"],
                base,
                seed=corpus["seed"],
                max_proposals=12,
                stats=stats,
            )
        )
        observed = [
            {
                "hash": canonical_hash(p.expression),
                "operator": p.operator,
                "values": [
                    run_ir_args(p.expression, tuple(point), expected_arity=2)
                    for point in fixture["public_probes"]
                ],
            }
            for p in proposals
        ]
        assert observed == corpus["proposals"]
        assert asdict(stats) == corpus["logical_counters"]


def test_frozen_normalized_journal_and_inheritance_replay(tmp_path):
    from cin.archive import Archive
    from cin.contracts import load_genome, load_world
    from cin.evolution import Experiment, replay_experiment
    from cin.ir import canonical_hash

    root = Path(__file__).resolve().parents[1]
    archive = Archive(tmp_path)
    report = Experiment(
        load_genome(root / "examples/seed-genome.v0.1.yaml"),
        load_world(root / "examples/world-max2.v0.1.yaml"),
        archive,
        seed=0,
        max_evals=250,
    ).run()
    _, trace = Archive.read_normalized_trace(tmp_path)
    assert len(trace) == 75
    assert (
        canonical_hash(trace) == "308b862be9c8c6c87888109c4d0e522da50cb25bcc50e0b6a133ab23ec91a345"
    )
    assert report["candidate_evaluations"] == 63
    assert (
        report["offspring_inherited_skill_hashes"]
        == report["parent_skill_hashes"]
        == ["2a4a39647279cef199e96ec1c6c11bbdd90c3d50547067c4afed83cc883b2f43"]
    )
    assert replay_experiment(tmp_path)["archive_chain_valid"]


def test_negative_ir_and_unknown_verdict_contracts():
    from cin.contracts import load_genome, load_world
    from cin.ir import IRViolation, Limits, check_tree, run_ir
    from cin.worlds import verify_program

    root = Path(__file__).resolve().parents[1]
    base = load_genome(root / "examples/seed-genome.v0.1.yaml")["genome"]["base"]
    world = load_world(root / "examples/world-max2.v0.1.yaml")
    arg = {"op": "Arg", "index": 0}
    for expression in [
        {"op": "Arg", "index": True},
        {"op": "Arg", "index": 2},
        {"op": "ConstInt", "value": True},
    ]:
        with pytest.raises(IRViolation):
            check_tree(expression, base)
    assert run_ir(arg, -(2**63), 0) == -(2**63)
    assert run_ir(arg, 2**63, 0) == 2**63
    with pytest.raises(IRViolation):
        run_ir(arg, 2**64, 0)
    with pytest.raises(IRViolation):
        run_ir(arg, 0, 0, Limits(max_ops=0))
    assert verify_program(arg, world, base, max_cases=1).status == "INVALID"
    assert verify_program(arg, world, base, limits=Limits(max_ops=0)).status == "UNKNOWN"


def test_smoke_report_records_limits_and_no_native_decision():
    from experiments.native_baseline import run_baseline

    protocol = load_protocol(DEFAULT_MANIFEST)
    protocol.update(seeds=[0], repetitions=1, guided_proposals=1, composition_iterations=1)
    protocol["workloads"] = [protocol["workloads"][1]]
    protocol["workloads"][0]["max_proposals"] = 1
    report = run_baseline(protocol)
    assert report["decision"] == "ITERATE_R0_NO_NATIVE_GO"
    assert report["native_speedup"] == "NOT_MEASURED"
    assert len(report["guided_baselines"]) == 3
    assert report["provenance"]["source_sha256"]["uv.lock"]
    json.dumps(report, allow_nan=False)


def test_provenance_prefers_host_cpu_model_over_architecture_label(monkeypatch):
    original_exists = Path.exists
    original_read_text = Path.read_text

    def exists(path):
        return True if path == Path("/proc/cpuinfo") else original_exists(path)

    def read_text(path, *args, **kwargs):
        if path == Path("/proc/cpuinfo"):
            return "processor\t: 0\nmodel name\t: Example CPU 123\n"
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "exists", exists)
    monkeypatch.setattr(Path, "read_text", read_text)
    monkeypatch.setattr(native_baseline.platform, "processor", lambda: "x86_64")

    assert native_baseline._provenance()["processor"] == "Example CPU 123"


def test_provenance_falls_back_when_cpuinfo_cannot_be_read(monkeypatch):
    original_exists = Path.exists
    original_read_text = Path.read_text

    def exists(path):
        return True if path == Path("/proc/cpuinfo") else original_exists(path)

    def read_text(path, *args, **kwargs):
        if path == Path("/proc/cpuinfo"):
            raise PermissionError("cpuinfo is not readable")
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "exists", exists)
    monkeypatch.setattr(Path, "read_text", read_text)
    monkeypatch.setattr(native_baseline.platform, "processor", lambda: "fallback-architecture")

    assert native_baseline._provenance()["processor"] == "fallback-architecture"


def test_provenance_keeps_unknown_cpu_sentinel_when_both_sources_absent(monkeypatch):
    original_exists = Path.exists

    def exists(path):
        return False if path == Path("/proc/cpuinfo") else original_exists(path)

    monkeypatch.setattr(Path, "exists", exists)
    monkeypatch.setattr(native_baseline.platform, "processor", lambda: "")

    assert native_baseline._provenance()["processor"] == "UNKNOWN"


def test_baseline_captures_provenance_before_measured_work(monkeypatch):
    protocol = load_protocol(DEFAULT_MANIFEST)
    protocol.update(seeds=[0], repetitions=1, guided_proposals=1, composition_iterations=1)
    protocol["workloads"] = [protocol["workloads"][1]]
    protocol["workloads"][0]["max_proposals"] = 1
    events = []
    original_load_genome = native_baseline.load_genome

    def load_genome(path):
        events.append("work")
        return original_load_genome(path)

    def provenance():
        events.append("provenance")
        return {"captured": "before"}

    monkeypatch.setattr(native_baseline, "_provenance", provenance)
    monkeypatch.setattr(native_baseline, "load_genome", load_genome)

    report = native_baseline.run_baseline(protocol)
    assert events[0] == "provenance"
    assert report["provenance"] == {"captured": "before"}


def test_cli_checks_output_parent_before_measuring(tmp_path, monkeypatch, capsys):
    def unexpected_baseline(protocol):
        pytest.fail("the baseline must not run for an invalid output path")

    monkeypatch.setattr(native_baseline, "run_baseline", unexpected_baseline)
    with pytest.raises(SystemExit) as exit_info:
        native_baseline.main(["--output", str(tmp_path / "missing" / "r0.json")])

    assert exit_info.value.code == 2
    assert "existing directory" in capsys.readouterr().err


def test_cli_handles_git_failure_as_invalid_baseline(tmp_path, monkeypatch, capsys):
    def git_failure(protocol):
        raise subprocess.CalledProcessError(128, ["git", "rev-parse", "HEAD"])

    monkeypatch.setattr(native_baseline, "run_baseline", git_failure)
    with pytest.raises(SystemExit) as exit_info:
        native_baseline.main(["--output", str(tmp_path / "r0.json")])

    assert exit_info.value.code == 2
    assert "INVALID R0 baseline" in capsys.readouterr().err
