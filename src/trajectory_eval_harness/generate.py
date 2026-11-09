"""Deterministic generator for 120 golden trajectories across 6 task families."""
from __future__ import annotations

from .schema import Hop, Trajectory

_FAMILIES: list[tuple[str, list[str], str]] = [
    ("search-book", ["search", "book"], "Booked: {n}"),
    ("lookup-summarise", ["search", "summarise"], "Summary: {n}"),
    ("read-write", ["read_file", "write_file"], "Wrote: {n}"),
    ("query-filter", ["query", "filter"], "Results: {n}"),
    ("fetch-parse-store", ["fetch", "parse", "store"], "Stored: {n}"),
    ("plan-execute-verify", ["plan", "execute", "verify"], "Verified: {n}"),
]


def generate(count_per_family: int = 20) -> list[Trajectory]:
    """Generate ``count_per_family`` perfect trajectories per family."""
    trajs: list[Trajectory] = []
    for fam, tools, template in _FAMILIES:
        for i in range(count_per_family):
            name = f"{fam}-{i}"
            hops: list[Hop] = []
            state: dict[str, object] = {"step": 0}
            exp_args: list[dict[str, object]] = []
            for j, tool in enumerate(tools):
                before = dict(state)
                state = {"step": j + 1, "last_tool": tool}
                args: dict[str, object] = {"target": name, "index": j}
                exp_args.append(dict(args))
                hops.append(Hop(tool=tool, args=args, state_before=before,
                                state_after=dict(state)))
            answer = template.format(n=name)
            trajs.append(Trajectory(
                id=f"golden-{fam}-{i:03d}", task=f"Do {fam} for {name}", hops=hops,
                final_answer=answer, expected_answer=answer,
                expected_tools=list(tools), expected_args=exp_args,
                expected_final_state=dict(state)))
    return trajs
