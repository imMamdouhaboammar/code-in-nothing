"""Hash-chained, append-only-in-process scientific event journal."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from .ir import canonical_bytes, canonical_hash


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
        for i, line in enumerate(Path(path).read_text().splitlines()):
            event = json.loads(line)
            digest = event.pop("hash")
            if (
                event["sequence"] != i
                or event["previous_hash"] != prior
                or digest != canonical_hash(event)
            ):
                return False
            prior = digest
        return True
