"""Random agent for the Cleanup environment."""
import random
from typing import Dict, List, Any
from .base import BaseAgent

class RandomAgent(BaseAgent):
    """Agent that takes random legal actions."""

    def __init__(self, agent_id: int, seed: int = None):
        """
        Initialize random agent.

        Args:
            agent_id: Unique identifier for this agent
            seed: Random seed for reproducibility
        """
        super().__init__(agent_id, f"Random_{agent_id}")
        self.rng = random.Random(seed)

    def act(self, obs: Dict[str, Any], legal_actions: List[str]) -> str:
        """Choose a random legal action."""
        if not legal_actions:
            return "STAY"
        return self.rng.choice(legal_actions)

    def reset(self):
        """Reset is not needed for random agent."""
        pass