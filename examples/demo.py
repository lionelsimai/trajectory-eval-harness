"""End-to-end demo: grade the golden set and show the worst trajectories.

Run: python examples/demo.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from trajectory_eval_harness.graders import evaluate  # noqa: E402
from trajectory_eval_harness.schema import load_jsonl  # noqa: E402

if __name__ == "__main__":
    data = Path(__file__).parent.parent / "data" / "golden.jsonl"
    report = evaluate(load_jsonl(data))
    print(f"Trajectories: {len(report.reports)}")
    print(f"Mean score: {report.mean_score:.4f}  Pass rate: {report.pass_rate:.2%}")
    print("Worst:", [(r.id, round(r.score, 3)) for r in report.worst(3)])
