"""One reproducible hybrid-evolution pilot, not a general autonomous coding system."""

from __future__ import annotations

import time
from copy import deepcopy

from .archive import Archive
from .contracts import validate_genome
from .ir import canonical_hash
from .search import candidate_stream
from .worlds import admit_world, expand_domain, verify_program

VERIFIER_VERSION = "cin.verifier/finite-domain-v0.1"


def spawn_verified(
    parent: dict,
    artifact: dict,
    certificates: list[dict],
    child_id: str,
    worlds: list[dict] | None = None,
) -> dict:
    """Reproduce only a replayed skill verified in >=2 distinct formal specs.

    A new child has a frozen, independent five-gene genome; its root phenotype
    starts with the heritable accepted IR. It receives no privileged evaluator.
    """
    if not artifact or "expression" not in artifact or "hash" not in artifact:
        raise ValueError("heritable artifact missing")
    if canonical_hash(artifact["expression"]) != artifact["hash"]:
        raise ValueError("artifact integrity mismatch")
    qualified = {
        c["world_hash"]
        for c in certificates
        if c.get("status") == "PASS" and c.get("program_hash") == artifact["hash"]
    }
    if len(qualified) < 2 or artifact["hash"] not in {
        canonical_hash(s) for s in parent["skills"].values()
    }:
        raise ValueError("replay-confirmed reuse over two distinct specifications required")
    if not worlds or {canonical_hash(w) for w in worlds} != qualified:
        raise ValueError("approved world specifications are required for independent replay")
    base = parent["genome"]["genome"]["base"]
    for world in worlds:
        admission = admit_world(world, base, max_proposals=250, max_cases=512)
        if (
            admission.status != "ADMITTED"
            or verify_program(artifact["expression"], world, base, max_cases=512).status != "PASS"
        ):
            raise ValueError("inherited skill failed independent world admission or replay")
    genome = deepcopy(parent["genome"])
    genome["seed_id"] = child_id
    genome["genome"]["base"]["starting_expression"] = deepcopy(artifact["expression"])
    validate_genome(genome)
    assert genome["genome"]["maturity_point"] == parent["genome"]["genome"]["maturity_point"]
    assert genome["genome"]["stop_station"] == parent["genome"]["genome"]["stop_station"]
    return {
        "id": child_id,
        "parent_ids": [parent["id"]],
        "genome": genome,
        # Only transfer the program whose certificates and worlds were replayed.
        # Other parent skills have not been independently verified for this birth.
        "skills": {
            world_hash: deepcopy(skill)
            for world_hash, skill in parent["skills"].items()
            if world_hash in qualified and canonical_hash(skill) == artifact["hash"]
        },
        "inherited_from": artifact["hash"],
    }


class Experiment:
    def __init__(
        self,
        genome: dict,
        world: dict,
        archive: Archive,
        seed: int = 0,
        max_evals: int | None = None,
        world_evolution: bool = True,
        inheritance: bool = True,
    ):
        self.genome = validate_genome(genome)
        self.world = deepcopy(world)
        self.archive = archive
        if type(seed) is not int or seed < 0:
            raise ValueError("rng seed must be a nonnegative integer")
        self.seed = seed
        self.world_evolution = world_evolution
        self.inheritance = inheritance
        self.base = self.genome["genome"]["base"]
        self.max_evals = min(
            max_evals if max_evals is not None else 2000,
            self.genome["genome"]["stop_station"]["max_candidate_evaluations"],
        )
        if self.max_evals < 1:
            raise ValueError("positive evaluation budget required")
        self.epoch_proposals = min(
            self.max_evals, self.genome["genome"]["directive"]["proposals_per_epoch"]
        )

    def run(self) -> dict:
        # World witnesses are checked inside verifier admission and not exposed to proposal generator.
        initial = admit_world(self.world, self.base, max_proposals=250, max_cases=512)
        self.archive.append(
            "WORLD_ADMISSION",
            {
                "world_id": self.world["id"],
                "world_hash": initial.spec_hash,
                "status": initial.status,
                "witness_digest": initial.witness_hash,
                "witness_search_candidates": initial.candidates_checked,
            },
        )
        if initial.status != "ADMITTED":
            raise ValueError(f"initial world not admissible: {initial.reason}")
        parent = {"id": "organism-0", "genome": deepcopy(self.genome), "skills": {}}
        self.archive.append(
            "BIRTH",
            {
                "organism_id": parent["id"],
                "genome_hash": canonical_hash(parent["genome"]),
                "five_genes": sorted(parent["genome"]["genome"]),
                "rng_seed": self.seed,
            },
        )
        start = self.base["starting_expression"]
        budget_used = 0
        learned = None
        accepted_worlds = []
        # Seed tested first; seed success is not claimed as acquired growth.
        if verify_program(start, self.world, self.base).status == "PASS":
            parent["skills"][initial.spec_hash] = deepcopy(start)
            learned = {"expression": deepcopy(start), "hash": canonical_hash(start)}
        else:
            for proposal in candidate_stream(
                start, self.base, seed=self.seed, max_proposals=self.epoch_proposals
            ):
                budget_used += 1
                t0 = time.process_time()
                verdict = verify_program(proposal.expression, self.world, self.base, max_cases=512)
                cpu_ms = max(0, int((time.process_time() - t0) * 1000))
                # Retained capabilities are versioned, not overwritten, so a newly
                # accepted candidate cannot silently replace a prior solved task.
                current_regression = all(
                    verify_program(saved, self.world, self.base).status == "PASS"
                    for saved in parent["skills"].values()
                )
                success = verdict.status == "PASS" and current_regression
                outcome = (
                    "ACCEPTED"
                    if success
                    else "REJECTED"
                    if verdict.status == "FAIL"
                    else "INVALID"
                    if verdict.status == "INVALID"
                    else "UNKNOWN"
                )
                evidence = {
                    "schema_version": "cin.evidence/v0.1",
                    "proposal_hash": canonical_hash(
                        {
                            "parent": proposal.parent_hash,
                            "expr": proposal.expression,
                            "operator": proposal.operator,
                        }
                    ),
                    "parent_hash": proposal.parent_hash,
                    "candidate_ir_hash": canonical_hash(proposal.expression),
                    "task_spec_hash": initial.spec_hash,
                    "evaluator_version": VERIFIER_VERSION,
                    "outcome": outcome,
                    "gate_outcomes": [
                        {
                            "gate": "validity",
                            "outcome": "PASS" if verdict.status != "INVALID" else "FAIL",
                        },
                        {
                            "gate": "behavioral",
                            "outcome": "PASS"
                            if verdict.status == "PASS"
                            else "FAIL"
                            if verdict.status == "FAIL"
                            else "UNKNOWN",
                        },
                        {"gate": "regression", "outcome": "PASS" if current_regression else "FAIL"},
                        {"gate": "contribution", "outcome": "PASS" if success else "FAIL"},
                    ],
                    "resources": {
                        "candidate_evaluations": 1,
                        "interpreter_operations": verdict.operations,
                        "cpu_ms": cpu_ms,
                    },
                    "replay": {
                        "rng_seed": self.seed,
                        "runtime_version": "cin/0.1.0",
                        "artifact_manifest_hash": canonical_hash(self.genome),
                    },
                    # This is an integrity digest, NOT a cryptographic signature.
                    "evaluator_signature": canonical_hash(
                        {
                            "version": VERIFIER_VERSION,
                            "candidate": canonical_hash(proposal.expression),
                            "outcome": outcome,
                        }
                    ),
                }
                self.archive.append("GROWTH_EVIDENCE", evidence)
                if success:
                    parent["skills"][initial.spec_hash] = deepcopy(proposal.expression)
                    learned = {
                        "expression": deepcopy(proposal.expression),
                        "hash": canonical_hash(proposal.expression),
                    }
                    self.archive.append(
                        "GROWTH_ACCEPTED",
                        {
                            "organism_id": parent["id"],
                            "world_hash": initial.spec_hash,
                            "program_hash": learned["hash"],
                            "search_attempt": budget_used,
                            "operator": proposal.operator,
                        },
                    )
                    break
        if learned:
            replay = verify_program(learned["expression"], self.world, self.base, max_cases=512)
            if replay.status == "PASS":
                accepted_worlds.append(
                    {
                        "world_hash": initial.spec_hash,
                        "program_hash": learned["hash"],
                        "status": "PASS",
                    }
                )
        world_admitted = False
        if learned and self.world_evolution:
            child_world = expand_domain(self.world, 1)
            updated = admit_world(child_world, self.base, max_proposals=250, max_cases=512)
            world_admitted = updated.status == "ADMITTED"
            self.archive.append(
                "WORLD_ADMISSION",
                {
                    "world_id": child_world["id"],
                    "world_hash": updated.spec_hash,
                    "parent_world_hash": initial.spec_hash,
                    "status": updated.status,
                    "witness_digest": updated.witness_hash,
                },
            )
            if world_admitted:
                independent = verify_program(
                    learned["expression"], child_world, self.base, max_cases=512
                )
                if independent.status == "PASS":
                    parent["skills"][updated.spec_hash] = deepcopy(learned["expression"])
                    accepted_worlds.append(
                        {
                            "world_hash": updated.spec_hash,
                            "program_hash": learned["hash"],
                            "status": "PASS",
                        }
                    )
                    self.archive.append(
                        "TRANSFER_VERIFIED",
                        {
                            "organism_id": parent["id"],
                            "world_hash": updated.spec_hash,
                            "program_hash": learned["hash"],
                        },
                    )
        child = None
        if learned and self.inheritance and len(accepted_worlds) >= 2:
            child = spawn_verified(
                parent,
                learned,
                accepted_worlds,
                "organism-0.child-1",
                worlds=[self.world, child_world],
            )
            self.archive.append(
                "INHERITANCE_APPROVED",
                {
                    "parent_id": parent["id"],
                    "program_hash": learned["hash"],
                    "supporting_world_hashes": [c["world_hash"] for c in accepted_worlds],
                },
            )
            self.archive.append(
                "OFFSPRING_BORN",
                {
                    "organism_id": child["id"],
                    "parent_ids": child["parent_ids"],
                    "genome_hash": canonical_hash(child["genome"]),
                    "inherited_skill_hashes": sorted(
                        {canonical_hash(p) for p in child["skills"].values()}
                    ),
                },
            )
        stop_reason = (
            "EXPERIMENT_COMPLETE"
            if learned
            else "BUDGET_EXHAUSTED"
            if budget_used >= self.max_evals
            else "EPOCH_COMPLETE"
            if budget_used >= self.epoch_proposals
            else "SEARCH_EXHAUSTED"
        )
        self.archive.terminal_archive(
            parent["id"],
            {
                "stop_reason": stop_reason,
                "evaluations": budget_used,
                "skills": len(parent["skills"]),
            },
        )
        if child:
            self.archive.terminal_archive(
                child["id"],
                {
                    "stop_reason": "EXPERIMENT_COMPLETE",
                    "evaluations": 0,
                    "skills": len(child["skills"]),
                },
            )
        return {
            "experiment_version": "cin-lab/0.1",
            "seed": self.seed,
            "finite_domain_only": True,
            "language_model_calls": 0,
            "initial_world_status": initial.status,
            "world_mutation_admitted": world_admitted,
            "verified_capabilities": 1 if learned else 0,
            "verified_world_specs": len(parent["skills"]),
            "candidate_evaluations": budget_used,
            "max_evaluations": self.max_evals,
            "max_epoch_proposals": self.epoch_proposals,
            "parent_skill_hashes": sorted({canonical_hash(p) for p in parent["skills"].values()}),
            "learned_program_ir": deepcopy(learned["expression"]) if learned else None,
            "offspring_count": 1 if child else 0,
            "offspring_inherited_skill_hashes": sorted(
                {canonical_hash(p) for p in child["skills"].values()}
            )
            if child
            else [],
            "parents_contracts_equal": (
                child is not None
                and parent["genome"]["genome"]["maturity_point"]
                == child["genome"]["genome"]["maturity_point"]
                and parent["genome"]["genome"]["stop_station"]
                == child["genome"]["genome"]["stop_station"]
            ),
            "maturity_status": "NOT_EVALUATED",
            "sealed_transfer_evaluation": "NOT_RUN",
            "scientific_self_improvement": "NOT_ESTABLISHED",
            "stop_reason": stop_reason,
            "archive_chain_valid": Archive.verify_chain(self.archive.journal),
        }
