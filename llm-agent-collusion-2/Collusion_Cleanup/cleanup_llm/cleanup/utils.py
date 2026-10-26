"""Utility functions for the Cleanup environment."""

from enum import Enum
from typing import Dict, Any, List
import random

class TileType(Enum):
    """Types of tiles in the grid."""
    ORCHARD = "ORCHARD"
    RIVER_CLEAR = "RIVER_CLEAR"
    RIVER_POLLUTED = "RIVER_POLLUTED"

def set_random_seed(seed: int) -> None:
    """Set the random seed for reproducibility."""
    random.seed(seed)

def clamp(value: int, min_val: int, max_val: int) -> int:
    """Clamp a value between min and max."""
    return max(min_val, min(value, max_val))

def manhattan_distance(pos1: tuple, pos2: tuple) -> int:
    """Calculate Manhattan distance between two positions."""
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

def get_neighbors(row: int, col: int, grid_h: int, grid_w: int) -> List[tuple]:
    """Get valid neighboring positions (4-connected)."""
    neighbors = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        new_row, new_col = row + dr, col + dc
        if 0 <= new_row < grid_h and 0 <= new_col < grid_w:
            neighbors.append((new_row, new_col))
    return neighbors

def format_observation(obs: Dict[str, Any]) -> str:
    """Format observation for debugging/logging."""
    step = obs.get('step', 0)
    you = obs.get('you', -1)
    scores = obs.get('scores', [])
    return f"Step {step}, Agent {you}, Scores: {scores}"

def safe_get(dictionary: Dict, key: str, default: Any = None) -> Any:
    """Safely get a value from a dictionary."""
    return dictionary.get(key, default)

def validate_agent_id(agent_id: int, max_agents: int) -> bool:
    """Validate that agent_id is in valid range."""
    return 0 <= agent_id < max_agents