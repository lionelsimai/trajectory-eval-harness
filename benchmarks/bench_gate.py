"""Benchmark: the gate catches a deliberately regressed trajectory.

Run: python benchmarks/bench_gate.py
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from trajectory_eval_harness.cli import main as cli_main  # noqa: E402
from trajectory_eval_harness.generate import generate  # noqa: E402
from trajectory_eval_harness.graders import evaluate  # noqa: E402
from trajectory_eval_harness.schema import dump_jsonl  # noqa: E402


def main() -> int:
    """Golden set must pass the gate; a regressed copy must fail it."""
    golden = generate(20)
    good = evaluate(golden)
    broken = generate(20)
    for traj in broken[:10]:  # regress half the trajectories
        traj.hops[0].tool = "wrong_tool"
        traj.final_answer = "incorrect answer"
    bad = evaluate(broken)
    print(f"Golden:   mean={good.mean_score:.4f} pass_rate={good.pass_rate:.2%}")
    print(f"Regressed: mean={bad.mean_score:.4f} pass_rate={bad.pass_rate:.2%}")
    with tempfile.TemporaryDirectory() as tmp:
        good_path = Path(tmp) / "good.jsonl"
        bad_path = Path(tmp) / "bad.jsonl"
        dump_jsonl(golden, good_path)
        dump_jsonl(broken, bad_path)
        assert cli_main(["gate", "--data", str(good_path), "--min-score", "0.99"]) == 0
        assert cli_main(["gate", "--data", str(bad_path), "--min-score", "0.99"]) == 1
    print("Gate verdict: golden PASSED, regressed BLOCKED (exit 1) — as designed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
