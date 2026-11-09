"""Generate data/golden.jsonl with 120 golden trajectories.

Run: python scripts/generate_golden.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from trajectory_eval_harness.generate import generate  # noqa: E402
from trajectory_eval_harness.schema import dump_jsonl  # noqa: E402

if __name__ == "__main__":
    out = Path(__file__).parent.parent / "data" / "golden.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    trajs = generate(20)
    dump_jsonl(trajs, out)
    print(f"Wrote {len(trajs)} trajectories to {out}")
