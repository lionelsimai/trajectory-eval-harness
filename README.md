# Trajectory Eval Harness

![CI](https://github.com/lionelsimai/trajectory-eval-harness/actions/workflows/ci.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)

**Grade every hop of an agent run — not just the final answer — and block bad PRs in CI.**

**Target:** 100+ golden trajectories, CI gate live.
**Shows:** You measure what actually breaks.

## Problem → Solution

Final-answer evals say *that* a run failed, never *where*. This harness grades
each hop (tool choice, argument correctness, state transition) plus the final
answer and final state, ships 120 golden trajectories, and provides a `gate`
command that exits 1 on regression — wired into GitHub Actions so a bad agent
change cannot merge.

## Architecture

```mermaid
flowchart LR
  A[Agent run JSONL] --> B[Schema] --> C[Per-hop graders] --> D[Report]
  D --> F{Gate >= 0.99?} -->|yes| G[Pass] 
  F -->|no| H[exit 1 — blocked]
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Quickstart (<2 min)

```bash
git clone https://github.com/lionelsimai/trajectory-eval-harness && cd trajectory-eval-harness
pip install -e .
python -m trajectory_eval_harness.cli eval --data data/golden.jsonl
python -m trajectory_eval_harness.cli gate --data data/golden.jsonl --min-score 0.99
python -m pytest -q   # 11 passed
python scripts/generate_golden.py   # regenerate the 120-trajectory golden set
```

## Real demo output

```json
{ "count": 120, "mean_score": 1.0, "pass_rate": 1.0,
  "worst": [{ "id": "golden-search-book-000", "score": 1.0 }] }
```
```text
GATE PASSED: mean 1.0000 >= 0.99
```
Sample narrative report: [examples/sample-report.md](examples/sample-report.md).

## Benchmarks

```bash
python benchmarks/bench_gate.py
```
Measured in this build: golden set mean 1.0000 (gate passes); a deliberately
regressed copy (half the trajectories given a wrong tool + wrong answer)
drops well below 0.99 and the gate blocks it with exit 1. That catch — not
the perfect score — is the benchmark.

## Limitations (honest)

- Golden trajectories are synthetic and deterministic; they prove the grading
  and gating machinery, not your agent's real-world quality. Point the harness
  at recorded real runs for that.
- Final-answer grading is exact/word-overlap; semantic grading (LLM judge) is
  a roadmap item and must itself be calibrated.
- State grading checks chaining consistency, not domain invariants.

## Roadmap

- [x] Schema, 5 graders, 120 goldens, eval + gate CLI, Actions gate workflow
- [ ] Adapters to import runs from popular agent frameworks
- [ ] Optional LLM-judge grader with calibration set; HTML report

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Licence: MIT — see [LICENSE](LICENSE).
