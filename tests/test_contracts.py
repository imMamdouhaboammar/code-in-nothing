from pathlib import Path

import pytest

from cin.contracts import ContractError, load_genome, load_world, validate_genome

ROOT = Path(__file__).resolve().parents[1]


def test_seed_has_exact_five_genes():
    g = load_genome(ROOT / "examples/seed-genome.v0.1.yaml")
    assert set(g["genome"]) == {"base", "driver", "directive", "maturity_point", "stop_station"}
    assert g["genome"]["base"]["starting_expression"] == {"op": "Arg", "index": 0}


def test_sixth_gene_rejected():
    g = load_genome(ROOT / "examples/seed-genome.v0.1.yaml")
    g["genome"]["environment"] = {}
    with pytest.raises(ContractError):
        validate_genome(g)


def test_bad_weights_rejected():
    g = load_genome(ROOT / "examples/seed-genome.v0.1.yaml")
    g["genome"]["driver"]["mutation_operators"]["replace_subtree"] = 0.9
    with pytest.raises(ContractError):
        validate_genome(g)


def test_invalid_resource_contract_rejected():
    g = load_genome(ROOT / "examples/seed-genome.v0.1.yaml")
    g["genome"]["stop_station"]["plateau_grace_epochs"] = 50
    with pytest.raises(ContractError):
        validate_genome(g)


def test_world_sample_validates():
    w = load_world(ROOT / "examples/world-max2.v0.1.yaml")
    assert w["family"] == "comparisons"
