"""Base agent class for the Cleanup environment."""
from abc import ABC, abstractmethod
from typing import Dict, List, Any

class BaseAgent(ABC):
    """Abstract base class for all Cleanup agents."""

    def __init__(self, agent_id: int, name: str = None):
        """
        Initialize the agent.

        Args:
            agent_id: Unique identifier for this agent (0-3)
            name: Optional name for the agent
        """
        self.agent_id = agent_id
        self.name = name or f"Agent_{agent_id}"

    @abstractmethod
    def act(self, obs: Dict[str, Any], legal_actions: List[str]) -> str:
        """
        Choose an action based on the current observation.

        Args:
            obs: Dictionary containing the current game state
            legal_actions: List of legal action strings

        Returns:
            Selected action as a string
        """
        pass

    def reset(self):
        """Reset agent state between episodes (if needed)."""
        pass

    def __str__(self):
        return f"{self.__class__.__name__}(id={self.agent_id}, name='{self.name}')"