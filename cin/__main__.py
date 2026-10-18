"""CLI: validate the five-gene seed or run a bounded model-free experiment."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .archive import Archive
from .contracts import ContractError, load_genome, load_world
from .evolution import Experiment
from .ir import render_python

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = (
    ROOT / "examples"
    if (ROOT / "examples").is_dir()
    else Path(__file__).resolve().parent / "examples"
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cin", description="Code in Nothing: bounded synthesis and evolutionary research lab"
    )
    cmds = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "demo"):
        p = cmds.add_parser(name)
        p.add_argument("--genome", type=Path, default=EXAMPLES / "seed-genome.v0.1.yaml")
        p.add_argument("--world", type=Path, default=EXAMPLES / "world-max2.v0.1.yaml")
        if name == "demo":
            p.add_argument("--seed", type=int, default=0)
            p.add_argument("--max-evals", type=int, default=250)
            p.add_argument("--output", type=Path, required=True)
            p.add_argument("--no-world-evolution", action="store_true")
            p.add_argument("--no-inheritance", action="store_true")
    args = parser.parse_args(argv)
    try:
        genome = load_genome(args.genome)
        world = load_world(args.world)
        if args.command == "validate":
            print("VALID: five-gene genome and formal world schemas")
            return 0
        output = args.output
        if output.exists():
            print(f"INVALID: output already exists: {output}", file=sys.stderr)
            return 2
        archive = Archive(output)
        experiment = Experiment(
            genome,
            world,
            archive,
            seed=args.seed,
            max_evals=args.max_evals,
            world_evolution=not args.no_world_evolution,
            inheritance=not args.no_inheritance,
        )
        report = experiment.run()
        (output / "report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        if report["learned_program_ir"] is not None:
            (output / "generated_program.py").write_text(
                render_python(report["learned_program_ir"], genome["genome"]["base"]),
                encoding="utf-8",
            )
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    except (ValueError, ContractError, OSError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
