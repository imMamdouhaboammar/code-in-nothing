from pathlib import Path

from cin.contracts import load_genome
from cin.ir import canonical_hash, check_tree
from cin.search import candidate_stream

BASE = load_genome(Path(__file__).resolve().parents[1] / "examples/seed-genome.v0.1.yaml")[
    "genome"
]["base"]


def test_search_produces_distinct_valid_typed_candidates():
    stream = list(candidate_stream({"op": "Arg", "index": 0}, BASE, seed=7, max_proposals=100))
    assert len(stream) == 100
    assert len({canonical_hash(x.expression) for x in stream}) == 100
    assert all(check_tree(x.expression, BASE) == "Int" for x in stream)


def test_search_does_not_need_witness_or_task_solution():
    stream = candidate_stream({"op": "Arg", "index": 0}, BASE, seed=1, max_proposals=300)
    assert any(x.expression["op"] == "If" for x in stream)
