"""Rules and payoff engine for the four-player discrete coalition game."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


ACTION_NAMES = ("KEEP", "PUBLIC", "TRANSFER", "SABOTAGE")


@dataclass(frozen=True)
class Choice:
    action: str
    target: Optional[int] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "action", self.action.upper())

    def as_dict(self) -> Dict[str, object]:
        return {"action": self.action, "target": self.target}


class DiscreteCoalitionGame:
    """Apply simultaneous choices and expose only public actions, deltas, and scores."""

    def __init__(self, agent_count: int = 4) -> None:
        if agent_count < 3:
            raise ValueError("the coalition game requires at least three agents")
        self.agent_count = agent_count
        self.scores = {agent_id: 0.0 for agent_id in range(agent_count)}
        self.history = []

    def validate_choice(self, actor: int, choice: Choice) -> None:
        if actor not in self.scores:
            raise ValueError(f"unknown actor {actor}")
        if choice.action not in ACTION_NAMES:
            raise ValueError(f"unknown action {choice.action!r}")
        targeted = choice.action in {"TRANSFER", "SABOTAGE"}
        if targeted:
            if choice.target not in self.scores:
                raise ValueError(f"{choice.action} requires a valid target")
            if choice.target == actor:
                raise ValueError("agents may not target themselves")
        elif choice.target is not None:
            raise ValueError(f"{choice.action} must not include a target")

    def step(self, choices: Dict[int, Choice]) -> Dict[str, object]:
        if set(choices) != set(self.scores):
            raise ValueError("every agent must submit exactly one choice")
        for actor, choice in choices.items():
            self.validate_choice(actor, choice)

        deltas = {agent_id: 0.0 for agent_id in self.scores}
        for actor, choice in choices.items():
            if choice.action == "KEEP":
                deltas[actor] += 2.0
            elif choice.action == "PUBLIC":
                for recipient in deltas:
                    deltas[recipient] += 1.0
            elif choice.action == "TRANSFER":
                deltas[choice.target] += 3.0
            elif choice.action == "SABOTAGE":
                deltas[actor] += 1.0
                deltas[choice.target] -= 2.0

        for agent_id, delta in deltas.items():
            self.scores[agent_id] += delta
        record = {
            "round": len(self.history) + 1,
            "choices": {str(actor): choice.as_dict() for actor, choice in choices.items()},
            "deltas": {str(agent_id): delta for agent_id, delta in deltas.items()},
            "scores": {str(agent_id): score for agent_id, score in self.scores.items()},
            "social_welfare": sum(self.scores.values()),
        }
        self.history.append(record)
        return record
