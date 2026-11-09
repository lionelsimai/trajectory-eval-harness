"""Unit + end-to-end tests for the trajectory eval harness."""
import json
from pathlib import Path

from trajectory_eval_harness.cli import main
from trajectory_eval_harness.generate import generate
from trajectory_eval_harness.graders import (
    evaluate,
    grade_args,
    grade_final_answer,
    grade_tool_choice,
    grade_trajectory,
)
from trajectory_eval_harness.schema import Hop, Trajectory, dump_jsonl, load_jsonl

ROOT = Path(__file__).parent.parent


def _perfect() -> Trajectory:
    return generate(1)[0]


def test_golden_dataset_has_100_plus() -> None:
    trajs = load_jsonl(ROOT / "data" / "golden.jsonl")
    assert len(trajs) >= 100
    assert all(t.validate() == [] for t in trajs)


def test_perfect_trajectory_scores_one() -> None:
    report = grade_trajectory(_perfect())
    assert report.score == 1.0 and report.passed


def test_wrong_tool_scores_zero_on_choice() -> None:
    traj = _perfect()
    traj.hops[0].tool = "wrong_tool"
    assert grade_tool_choice(traj, 0) == 0.0
    assert grade_trajectory(traj).score < 1.0


def test_wrong_args_partial_credit() -> None:
    traj = _perfect()
    traj.hops[0].args = {"target": "wrong", "index": 999}
    assert grade_args(traj, 0) == 0.0
    traj.hops[0].args = {"target": traj.expected_args[0]["target"], "index": 999}
    assert grade_args(traj, 0) == 0.5


def test_final_answer_word_overlap() -> None:
    traj = _perfect()
    traj.final_answer = "completely unrelated words here"
    assert grade_final_answer(traj) < 0.5


def test_state_break_detected() -> None:
    traj = _perfect()
    if len(traj.hops) > 1:
        traj.hops[1].state_before = {"step": 999}
        report = grade_trajectory(traj)
        assert report.hops[0].state < 1.0


def test_evaluate_and_gate_e2e(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    path = tmp_path / "g.jsonl"
    dump_jsonl(generate(2), path)
    assert main(["eval", "--data", str(path)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["count"] == 12 and out["mean_score"] == 1.0
    assert main(["gate", "--data", str(path), "--min-score", "0.99"]) == 0


def test_gate_fails_on_regression(tmp_path: Path) -> None:
    trajs = generate(1)
    trajs[0].hops[0].tool = "broken"
    trajs[0].final_answer = "wrong"
    path = tmp_path / "bad.jsonl"
    dump_jsonl(trajs, path)
    assert main(["gate", "--data", str(path), "--min-score", "0.99"]) == 1


def test_schema_roundtrip(tmp_path: Path) -> None:
    traj = Trajectory(id="x", task="t", hops=[Hop(tool="search")],
                        final_answer="a", expected_answer="a", expected_tools=["search"])
    path = tmp_path / "x.jsonl"
    dump_jsonl([traj], path)
    loaded = load_jsonl(path)
    assert loaded[0].id == "x" and loaded[0].hops[0].tool == "search"


def test_empty_evaluate() -> None:
    report = evaluate([])
    assert report.mean_score == 0.0 and report.pass_rate == 0.0


def test_config_from_env(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from trajectory_eval_harness.config import Settings
    monkeypatch.setenv("TRAJ_EVAL_LOG_LEVEL", "DEBUG")
    assert Settings.from_env().log_level == "DEBUG"
