"""Trajectory eval harness: grade every hop, gate bad PRs."""
from .graders import TrajectoryReport, grade_trajectory
from .schema import Hop, Trajectory, load_jsonl

__all__ = ["Trajectory", "Hop", "load_jsonl", "grade_trajectory", "TrajectoryReport"]
__version__ = "0.1.0"
