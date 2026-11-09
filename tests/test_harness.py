"""Unit + end-to-end tests for the trajectory eval harness."""
import json
from pathlib import Path

import pytest

from trajectory_eval_harness.cli import main
from trajectory_eval_harness.generate import generate
from trajectory_eval_harness.graders import (
    evaluate,
    grade_args,
    grade_final_answer,
    grade_final_state,
    grade_state_transition,
    grade_tool_choice,
    grade_trajectory,
)
from trajectory_eval_harness.schema import (
    Hop,
    Trajectory,
    TrajectoryDataError,
    dump_jsonl,
    load_jsonl,
)

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


def test_handwritten_trajectories_match_expected_scores() -> None:
    rows = [json.loads(line) for line in
            (ROOT / "data" / "handwritten.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()]
    assert len(rows) >= 12
    for row in rows:
        expected = row.pop("expected_score")
        traj = Trajectory.from_dict(row)
        assert traj.validate() == []
        got = grade_trajectory(traj).score
        assert abs(got - expected) <= 0.05, f"{traj.id}: got {got}, expected {expected}"


def test_handwritten_loads_via_validating_loader() -> None:
    trajs = load_jsonl(ROOT / "data" / "handwritten.jsonl")
    assert len(trajs) >= 12


def test_graders_score_zero_on_missing_expected_data() -> None:
    traj = Trajectory(id="m", task="t", hops=[Hop(tool="search", args={"a": 1})],
                      final_answer="x", expected_answer="",
                      expected_tools=[], expected_args=[])
    assert grade_tool_choice(traj, 0) == 0.0
    assert grade_args(traj, 0) == 0.0
    assert grade_final_answer(traj) == 0.0
    assert grade_final_state(traj) == 0.0


def test_empty_hop_list_scores_zero() -> None:
    traj = Trajectory(id="e", task="t", hops=[], final_answer="a", expected_answer="a")
    assert grade_trajectory(traj).score == 0.0


def test_disjoint_states_score_zero() -> None:
    traj = Trajectory(
        id="d", task="t",
        hops=[Hop(tool="a", state_after={"x": 1}), Hop(tool="b", state_before={"y": 2})],
        final_answer="a", expected_answer="a", expected_tools=["a", "b"])
    assert grade_state_transition(traj, 0) == 0.0


def test_malformed_jsonl_raises_data_error(tmp_path: Path) -> None:
    bad = tmp_path / "bad.jsonl"
    bad.write_text("{not json\n", encoding="utf-8")
    with pytest.raises(TrajectoryDataError):
        load_jsonl(bad)
    invalid = tmp_path / "invalid.jsonl"
    invalid.write_text('{"id": "x", "hops": [{"args": {}}]}\n', encoding="utf-8")
    with pytest.raises(TrajectoryDataError):
        load_jsonl(invalid)


def test_cli_malformed_jsonl_clean_error_exit_2(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    bad = tmp_path / "bad.jsonl"
    bad.write_text("{not json\n", encoding="utf-8")
    assert main(["eval", "--data", str(bad)]) == 2
    err = capsys.readouterr().err
    assert "error" in err and "Traceback" not in err
    missing = tmp_path / "nope.jsonl"
    assert main(["gate", "--data", str(missing)]) == 2


def test_config_from_env(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from trajectory_eval_harness.config import Settings
    monkeypatch.setenv("TRAJ_EVAL_LOG_LEVEL", "DEBUG")
    assert Settings.from_env().log_level == "DEBUG"
