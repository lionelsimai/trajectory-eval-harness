"""CLI: eval (report) + gate (exit 1 on regression) + generate.

  python -m trajectory_eval_harness.cli eval --data data/golden.jsonl
  python -m trajectory_eval_harness.cli gate --data data/golden.jsonl --min-score 0.99
  python -m trajectory_eval_harness.cli generate --out data/golden.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys

from .generate import generate
from .graders import evaluate
from .schema import dump_jsonl, load_jsonl


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns 1 from ``gate`` when the score regresses."""
    ap = argparse.ArgumentParser(prog="traj-eval")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("eval", "gate"):
        p = sub.add_parser(name)
        p.add_argument("--data", default="data/golden.jsonl")
        p.add_argument("--min-score", type=float, default=0.99)
    g = sub.add_parser("generate")
    g.add_argument("--out", default="data/golden.jsonl")
    g.add_argument("--per-family", type=int, default=20)
    args = ap.parse_args(argv)
    if args.cmd == "generate":
        trajs = generate(args.per_family)
        dump_jsonl(trajs, args.out)
        print(f"Wrote {len(trajs)} golden trajectories to {args.out}")
        return 0
    report = evaluate(load_jsonl(args.data))
    print(json.dumps(report.to_dict(), indent=2))
    if args.cmd == "gate":
        if report.mean_score < args.min_score:
            print(f"GATE FAILED: mean {report.mean_score:.4f} < {args.min_score}",
                  file=sys.stderr)
            return 1
        print(f"GATE PASSED: mean {report.mean_score:.4f} >= {args.min_score}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
