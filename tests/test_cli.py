import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def run(*args):
    return subprocess.run(
        [sys.executable, "-m", "cin", *map(str, args)], cwd=ROOT, capture_output=True, text=True
    )


def test_validate_canonical_examples():
    result = run("validate")
    assert result.returncode == 0, result.stderr
    assert "VALID" in result.stdout


def test_validate_bad_genome_fails(tmp_path):
    g = yaml.safe_load((ROOT / "examples/seed-genome.v0.1.yaml").read_text())
    g["genome"]["sixth"] = {}
    bad = tmp_path / "bad.yaml"
    bad.write_text(yaml.safe_dump(g))
    result = run("validate", "--genome", bad)
    assert result.returncode != 0
    assert "INVALID" in result.stderr


def test_demo_generates_verified_report_and_journal(tmp_path):
    result = run("demo", "--seed", "0", "--max-evals", "250", "--output", tmp_path / "run")
    assert result.returncode == 0, result.stderr
    report = json.loads((tmp_path / "run" / "report.json").read_text())
    assert report["verified_capabilities"] == 1
    assert report["offspring_count"] == 1
    assert report["maturity_status"] == "NOT_EVALUATED"
    assert report["archive_chain_valid"] is True
    assert (tmp_path / "run" / "events.jsonl").exists()


def test_cli_refuses_overwrite(tmp_path):
    path = tmp_path / "run"
    assert run("demo", "--seed", "0", "--max-evals", "1", "--output", path).returncode == 0
    assert run("demo", "--seed", "0", "--max-evals", "1", "--output", path).returncode != 0
