"""Trajectory schema (JSON / JSONL).

Each trajectory: id, task, expected_tools, hops[], final_answer,
expected_answer. Each hop: tool, args, state_before, state_after (dicts).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Hop:
    """One agent step: a tool call plus the state around it."""

    tool: str
    args: dict[str, object] = field(default_factory=dict)
    state_before: dict[str, object] = field(default_factory=dict)
    state_after: dict[str, object] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict[str, object]) -> Hop:
        """Build a Hop from parsed JSON."""
        return cls(tool=str(d["tool"]), args=dict(d.get("args", {})),  # type: ignore[arg-type]
                   state_before=dict(d.get("state_before", {})),  # type: ignore[arg-type]
                   state_after=dict(d.get("state_after", {})))  # type: ignore[arg-type]

    def to_dict(self) -> dict[str, object]:
        """Serialise to a JSON-compatible dict."""
        return {"tool": self.tool, "args": self.args,
                "state_before": self.state_before, "state_after": self.state_after}


@dataclass
class Trajectory:
    """A full agent run plus its expected (golden) behaviour."""

    id: str
    task: str
    hops: list[Hop]
    final_answer: str
    expected_answer: str
    expected_tools: list[str] = field(default_factory=list)
    expected_args: list[dict[str, object]] = field(default_factory=list)
    expected_final_state: dict[str, object] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict[str, object]) -> Trajectory:
        """Build a Trajectory from parsed JSON."""
        return cls(id=str(d["id"]), task=str(d.get("task", "")),
                   hops=[Hop.from_dict(h) for h in d.get("hops", [])],  # type: ignore[arg-type]
                   final_answer=str(d.get("final_answer", "")),
                   expected_answer=str(d.get("expected_answer", "")),
                   expected_tools=list(d.get("expected_tools", [])),  # type: ignore[arg-type]
                   expected_args=list(d.get("expected_args", [])),  # type: ignore[arg-type]
                   expected_final_state=dict(d.get("expected_final_state", {})))  # type: ignore[arg-type]

    def to_dict(self) -> dict[str, object]:
        """Serialise to a JSON-compatible dict."""
        return {"id": self.id, "task": self.task,
                "hops": [h.to_dict() for h in self.hops],
                "final_answer": self.final_answer,
                "expected_answer": self.expected_answer,
                "expected_tools": self.expected_tools,
                "expected_args": self.expected_args,
                "expected_final_state": self.expected_final_state}

    def validate(self) -> list[str]:
        """Return schema errors (empty list = valid)."""
        errs: list[str] = []
        if not self.id:
            errs.append("missing id")
        if not self.hops:
            errs.append(f"{self.id}: no hops")
        if len(self.expected_tools) != len(self.hops):
            errs.append(f"{self.id}: expected_tools/hops length mismatch")
        return errs


def load_jsonl(path: str | Path) -> list[Trajectory]:
    """Load trajectories from a JSONL file."""
    out: list[Trajectory] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(Trajectory.from_dict(json.loads(line)))
    return out


def dump_jsonl(trajs: list[Trajectory], path: str | Path) -> None:
    """Write trajectories as JSONL."""
    Path(path).write_text(
        "\n".join(json.dumps(t.to_dict()) for t in trajs) + "\n", encoding="utf-8")
