"""Aggregate metrics for the Cleanup baseline tournament.

RECONSTRUCTION. The published repository imports `metrics.tracker.MetricsTracker` from
`games/tournament.py` but never shipped this module, so the baseline tournament could
not run. This file restores the interface the runner uses:

    tracker = MetricsTracker()
    tracker.update_episode(actions, final_scores)   # once per game
    summary = tracker.get_summary()                 # one flat dict -> summary.csv

What it reports is deliberately descriptive and free of interpretation: per-agent score
totals/means across games and a count of every action label the environment emits.
It is not the authors' original implementation. Nothing else in the project reads
`summary.csv`; the experiment's raw data (`episodes.csv`, `cumulative_scores.csv`,
the per-game JSON records) is written by the runner itself and is unaffected.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List


def _label(action: Any) -> str:
    """Action labels arrive as strings from LLM agents and as enum members from
    scripted ones; normalise both to the enum's name."""
    return getattr(action, "name", str(action))


def _known_action_labels() -> List[str]:
    """Every action the environment defines, so summary.csv has a stable column set."""
    try:
        from cleanup.actions import ALL_ACTIONS  # resolved via the runner's sys.path
        return [_label(a) for a in ALL_ACTIONS]
    except Exception:  # pragma: no cover - fall back to whatever was observed
        return []


class MetricsTracker:
    """Accumulates per-agent scores and action counts across games."""

    def __init__(self) -> None:
        self.games = 0
        self.total_scores: Dict[int, float] = defaultdict(float)
        self.action_counts: Dict[int, Counter] = defaultdict(Counter)

    def update_episode(self, actions: Dict[int, Iterable[Any]], final_scores: Dict[int, float]) -> None:
        """Record one finished game.

        Args:
            actions:      {agent_id: [action per step]} as collected by the runner
            final_scores: {agent_id: final score}
        """
        self.games += 1
        for agent_id, score in final_scores.items():
            self.total_scores[agent_id] += float(score)
        for agent_id, seq in actions.items():
            self.action_counts[agent_id].update(_label(a) for a in seq)

    def get_summary(self) -> Dict[str, Any]:
        """One flat row: games, then per agent total/mean score and per-action counts."""
        agent_ids = sorted(set(self.total_scores) | set(self.action_counts))
        labels = _known_action_labels()
        seen = {lbl for c in self.action_counts.values() for lbl in c}
        labels += sorted(seen - set(labels))

        summary: Dict[str, Any] = {"games": self.games}
        for agent_id in agent_ids:
            total = self.total_scores.get(agent_id, 0.0)
            counts = self.action_counts.get(agent_id, Counter())
            summary[f"agent_{agent_id}_total_score"] = round(total, 4)
            summary[f"agent_{agent_id}_mean_score"] = round(total / self.games, 4) if self.games else 0.0
            summary[f"agent_{agent_id}_actions"] = sum(counts.values())
            for lbl in labels:
                summary[f"agent_{agent_id}_action_{lbl}"] = counts.get(lbl, 0)
        return summary
