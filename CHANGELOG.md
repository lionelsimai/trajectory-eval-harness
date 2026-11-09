# Changelog

All notable changes to this project will be documented in this file.
Format: Keep a Changelog. Versioning: Semantic Versioning.

## [0.1.1] - 2026-11-09
### Fixed
- Benchmark honesty: the "regressed" copy now actually corrupts half the trajectories (60 of 120, every second one) — 0.1.0 corrupted only 10/120 while the README claimed "half". Real numbers after: golden mean 1.0000; regressed mean 0.8444, pass rate 50.00% (was reported as 0.9722 on the 10/120 corruption).
- Graders no longer default to 1.0 for missing evidence: missing expected tools/args/answer/final-state, empty hop lists, and key-disjoint consecutive states all score 0.0.
- `load_jsonl` now calls `Trajectory.validate()` on every record and raises `TrajectoryDataError` with file + line on malformed input; the CLI prints a clean error and exits 2 instead of dumping a traceback.
### Added
- `data/handwritten.jsonl`: 13 hand-written imperfect trajectories with known expected per-trajectory scores; tests assert the graders reproduce every expected score within 0.05.
- Tests for missing-expected-data zero scores, disjoint states, empty hop lists, and malformed-JSONL handling (suite: 11 → 18 tests).
### Changed
- README "Real demo output" renamed to "Generator self-check output" — the golden set is generator-produced.

## [0.1.0] - 2026-11-09
### Added
- Initial public release: working offline demo, CLI, tests, benchmarks, CI gate.
- README with architecture diagram, benchmark section and honest limitations.
