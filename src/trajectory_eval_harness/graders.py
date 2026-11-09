"""Per-hop graders: tool choice, arguments, state transition, final answer.

Each grader returns 0.0-1.0. A hop score is the mean of its graders, and a
trajectory score also folds in the final answer and final state.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .schema import Trajectory


def grade_tool_choice(traj: Trajectory, i: int) -> float:
    """1.0 if hop ``i`` used the expected tool, else 0.0.

    Missing expected data scores 0.0, not 1.0: an expectation that was never
    recorded cannot be passed by default.
    """
    if i >= len(traj.expected_tools):
        return 0.0
    return 1.0 if traj.hops[i].tool == traj.expected_tools[i] else 0.0


def grade_args(traj: Trajectory, i: int) -> float:
    """Fraction of expected argument key/values matched exactly.

    Missing expected args score 0.0 when the hop passed arguments anyway;
    an expectation of no arguments matched by no arguments scores 1.0.
    """
    if i >= len(traj.expected_args):
        return 0.0
    exp, got = traj.expected_args[i], traj.hops[i].args
    if not exp:
        return 1.0 if not got else 0.0
    matched = sum(1 for k, v in exp.items() if got.get(k) == v)
    return matched / len(exp)


def grade_state_transition(traj: Trajectory, i: int) -> float:
    """Check hop ``i``'s state_after chains into hop ``i+1``'s state_before.

    Key-disjoint consecutive states score 0.0 (no chaining evidence). The
    last hop has no transition to check and scores 1.0.
    """
    hop = traj.hops[i]
    if i + 1 < len(traj.hops):
        nxt = traj.hops[i + 1].state_before
        shared = set(hop.state_after) & set(nxt)
        if not shared:
            return 0.0
        ok = sum(1 for k in shared if hop.state_after[k] == nxt[k])
        return ok / len(shared)
    return 1.0


def grade_final_answer(traj: Trajectory) -> float:
    """Exact match = 1.0, otherwise word-overlap with the expected answer.

    A missing expected answer scores 0.0: there is nothing to grade against.
    """
    exp = traj.expected_answer.strip().lower()
    got = traj.final_answer.strip().lower()
    if not exp:
        return 0.0
    if got == exp:
        return 1.0
    exp_words, got_words = set(exp.split()), set(got.split())
    return len(exp_words & got_words) / len(exp_words)


def grade_final_state(traj: Trajectory) -> float:
    """Fraction of expected final-state keys matched.

    Missing expected final state (or no hops to take a final state from)
    scores 0.0.
    """
    if not traj.expected_final_state or not traj.hops:
        return 0.0
    final = traj.hops[-1].state_after
    matched = sum(1 for k, v in traj.expected_final_state.items() if final.get(k) == v)
    return matched / len(traj.expected_final_state)


@dataclass
class HopReport:
    """Grades for a single hop."""

    index: int
    tool: str
    tool_choice: float
    args: float
    state: float

    @property
    def score(self) -> float:
        """Mean of the three hop graders."""
        return (self.tool_choice + self.args + self.state) / 3


@dataclass
class TrajectoryReport:
    """Grades for a whole trajectory."""

    id: str
    hops: list[HopReport] = field(default_factory=list)
    final_answer: float = 0.0
    final_state: float = 0.0

    @property
    def score(self) -> float:
        """Mean of hop scores plus final answer/state scores."""
        parts = [h.score for h in self.hops] + [self.final_answer, self.final_state]
        return sum(parts) / len(parts) if parts else 0.0

    @property
    def passed(self) -> bool:
        """A trajectory passes at >= 0.8."""
        return self.score >= 0.8


def grade_trajectory(traj: Trajectory) -> TrajectoryReport:
    """Grade every hop plus the final answer and state.

    A trajectory with no hops scores 0.0 overall: an empty run demonstrates
    nothing, even if its final-answer string happens to match.
    """
    if not traj.hops:
        return TrajectoryReport(id=traj.id, hops=[], final_answer=0.0, final_state=0.0)
    hops = [HopReport(index=i, tool=h.tool, tool_choice=grade_tool_choice(traj, i),
                      args=grade_args(traj, i), state=grade_state_transition(traj, i))
            for i, h in enumerate(traj.hops)]
    return TrajectoryReport(id=traj.id, hops=hops,
                            final_answer=grade_final_answer(traj),
                            final_state=grade_final_state(traj))


@dataclass
class EvalReport:
    """Aggregate report over a trajectory set."""

    reports: list[TrajectoryReport]

    @property
    def mean_score(self) -> float:
        """Mean trajectory score (0.0 for an empty set)."""
        if not self.reports:
            return 0.0
        return sum(r.score for r in self.reports) / len(self.reports)

    @property
    def pass_rate(self) -> float:
        """Fraction of trajectories at >= 0.8."""
        if not self.reports:
            return 0.0
        return sum(1 for r in self.reports if r.passed) / len(self.reports)

    def worst(self, n: int = 5) -> list[TrajectoryReport]:
        """The ``n`` lowest-scoring trajectories."""
        return sorted(self.reports, key=lambda r: r.score)[:n]

    def to_dict(self) -> dict[str, object]:
        """JSON-serialisable summary."""
        return {"count": len(self.reports), "mean_score": round(self.mean_score, 4),
                "pass_rate": round(self.pass_rate, 4),
                "worst": [{"id": r.id, "score": round(r.score, 4)} for r in self.worst()]}


def evaluate(trajs: list[Trajectory]) -> EvalReport:
    """Grade a list of trajectories."""
    return EvalReport(reports=[grade_trajectory(t) for t in trajs])
