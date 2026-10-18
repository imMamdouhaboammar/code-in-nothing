"""Hash-chained scientific event journal and versioned completed-run traces."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from .contracts import validate_genome, validate_world
from .ir import canonical_bytes, canonical_hash

COHORT_VERSION = "cin.cohort/v0.1"
_MAX_MANIFEST_BYTES = 1_048_576
_MAX_JOURNAL_BYTES = 67_108_864


class Archive:
    def __init__(self, directory: str | Path):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.journal = self.directory / "events.jsonl"
        if self.journal.exists() and self.journal.stat().st_size:
            raise ValueError("archive directory must be empty for a new experiment")
        self.events = []
        self._terminal = set()

    def append(self, kind: str, payload: dict) -> str:
        prior = self.events[-1]["hash"] if self.events else "GENESIS"
        event = {
            "sequence": len(self.events),
            "kind": kind,
            "payload": deepcopy(payload),
            "previous_hash": prior,
        }
        event["hash"] = canonical_hash(event)
        with self.journal.open("ab") as f:
            f.write(canonical_bytes(event) + b"\n")
        self.events.append(event)
        return event["hash"]

    def write_manifest(self, configuration: dict) -> str:
        """Persist the exact inputs before emitting the first scientific event.

        Exclusive creation refuses accidental reuse. Atomic crash recovery remains
        a separate P1-03 obligation; partial files are rejected by replay.
        """
        if self.events or self.journal.exists():
            raise ValueError("manifest must precede the first event")
        manifest = {
            "schema_version": COHORT_VERSION,
            "configuration": deepcopy(configuration),
        }
        with (self.directory / "manifest.json").open("xb") as f:
            f.write(canonical_bytes(manifest) + b"\n")
        digest = canonical_hash(manifest)
        self.append("COHORT_MANIFEST", {"manifest_hash": digest})
        return digest

    def terminal_archive(self, organism_id: str, summary: dict) -> str | None:
        if organism_id in self._terminal:
            return None
        self.append("STOP_TRIGGERED", {"organism_id": organism_id, **summary})
        final_hash = self.append(
            "ARCHIVED", {"organism_id": organism_id, "summary_hash": canonical_hash(summary)}
        )
        self._terminal.add(organism_id)
        return final_hash

    @staticmethod
    def verify_chain(path: str | Path) -> bool:
        prior = "GENESIS"
        try:
            journal = Path(path)
            if journal.stat().st_size > _MAX_JOURNAL_BYTES:
                return False
            raw = journal.read_bytes()
            if not raw or not raw.endswith(b"\n"):
                return False
            for i, line in enumerate(raw.splitlines()):
                event = json.loads(line)
                if not isinstance(event, dict) or set(event) != {
                    "sequence",
                    "kind",
                    "payload",
                    "previous_hash",
                    "hash",
                }:
                    return False
                digest = event.pop("hash")
                if (
                    type(event["sequence"]) is not int
                    or event["sequence"] != i
                    or event["previous_hash"] != prior
                    or type(event["kind"]) is not str
                    or not isinstance(event["payload"], dict)
                    or digest != canonical_hash(event)
                ):
                    return False
                prior = digest
        except (OSError, ValueError, TypeError, KeyError, UnicodeDecodeError):
            return False
        return True

    @staticmethod
    def read_normalized_trace(directory: str | Path) -> tuple[dict, list[dict]]:
        """Read a *completed* trace, excluding measurement-only CPU timing.

        A hash chain detects accidental changes, not an attacker with write
        access who can rehash the journal. Scientific replay separately reruns
        the unchanged independent verifier.
        """
        root = Path(directory)
        path = root / "manifest.json"
        try:
            if path.stat().st_size > _MAX_MANIFEST_BYTES:
                raise ValueError("manifest size limit")
            raw = path.read_bytes()
            if not raw.endswith(b"\n"):
                raise ValueError("partial manifest")
            manifest = json.loads(raw)
            if (
                not isinstance(manifest, dict)
                or set(manifest) != {"schema_version", "configuration"}
                or manifest["schema_version"] != COHORT_VERSION
            ):
                raise ValueError("unknown cohort manifest version or shape")
            config = manifest["configuration"]
            if not isinstance(config, dict) or set(config) != {
                "genome",
                "world",
                "seed",
                "resource_policy",
                "runtime_version",
                "verifier_version",
            }:
                raise ValueError("invalid cohort configuration")
            validate_genome(config["genome"])
            validate_world(config["world"])
            policy = config["resource_policy"]
            if not isinstance(policy, dict) or set(policy) != {
                "max_evals",
                "epoch_proposals",
                "world_evolution",
                "inheritance",
            }:
                raise ValueError("invalid resource policy")
            if (
                type(config["seed"]) is not int
                or config["seed"] < 0
                or type(policy["max_evals"]) is not int
                or policy["max_evals"] < 1
                or type(policy["epoch_proposals"]) is not int
                or policy["epoch_proposals"] < 1
                or type(policy["world_evolution"]) is not bool
                or type(policy["inheritance"]) is not bool
                or type(config["runtime_version"]) is not str
                or type(config["verifier_version"]) is not str
            ):
                raise ValueError("invalid cohort policy types")
            journal = root / "events.jsonl"
            if not Archive.verify_chain(journal):
                raise ValueError("journal integrity failure")
            events = [json.loads(line) for line in journal.read_text().splitlines()]
            if (
                not events
                or events[0]["kind"] != "COHORT_MANIFEST"
                or events[0]["payload"] != {"manifest_hash": canonical_hash(manifest)}
                or events[-1]["kind"] != "ARCHIVED"
            ):
                raise ValueError("incomplete or mismatched completed trace")
            terminated = set()
            for i, event in enumerate(events):
                kind = event["kind"]
                payload = event["payload"]
                if kind == "STOP_TRIGGERED":
                    organism_id = payload.get("organism_id")
                    if not isinstance(organism_id, str) or organism_id in terminated:
                        raise ValueError("duplicate or malformed terminal event")
                    summary = {k: v for k, v in payload.items() if k != "organism_id"}
                    if i + 1 == len(events) or events[i + 1]["kind"] != "ARCHIVED":
                        raise ValueError("orphan terminal event")
                    if events[i + 1]["payload"] != {
                        "organism_id": organism_id,
                        "summary_hash": canonical_hash(summary),
                    }:
                        raise ValueError("terminal summary mismatch")
                    terminated.add(organism_id)
                if kind == "ARCHIVED" and (i == 0 or events[i - 1]["kind"] != "STOP_TRIGGERED"):
                    raise ValueError("orphan archive event")
            if not terminated:
                raise ValueError("no completed organism")
            trace = []
            for event in events:
                payload = deepcopy(event["payload"])
                if event["kind"] == "GROWTH_EVIDENCE":
                    payload["resources"].pop("cpu_ms", None)
                trace.append({"kind": event["kind"], "payload": payload})
            return manifest, trace
        except (OSError, KeyError, TypeError, UnicodeDecodeError) as exc:
            raise ValueError("missing or malformed replay evidence") from exc
