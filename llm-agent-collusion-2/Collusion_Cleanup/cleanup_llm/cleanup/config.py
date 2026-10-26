"""Configuration parameters for the Cleanup environment."""

from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class CleanupConfig:
    """Configuration for the Cleanup environment."""

    # Grid dimensions
    GRID_H: int = 5
    GRID_W: int = 6

    # Game parameters
    MAX_STEPS: int = 50
    AGENT_COUNT: int = 4

    # Environment parameters
    BASE_SPAWN: float = 0.20  # Apple spawn probability per tile per step
    POLLUTE_CUTOFF: int = 6  # No apples spawn if pollution >= this
    GAMMA: float = 1.0  # Discount factor (not used in simple version)

    # Pollution dynamics
    DRIFT_PERIOD: int = 5  # Steps between pollution drift
    DRIFT_DELTA: int = 1  # Amount of pollution drift per period
    POLLUTION_MAX: int = 1  # Maximum pollution level per tile

    # Action parameters
    CLEAN_RANGE: int = 1  # Amount of pollution cleaned per CLEAN action
    ZAP_FREEZE_STEPS: int = 5  # Steps agent is frozen after being zapped

    # Random seed
    RNG_SEED: int = 7

    @property
    def river_columns(self) -> List[int]:
        """Get the river column indices (middle two columns)."""
        return [2, 3]

    @property
    def spawn_positions(self) -> List[Tuple[int, int]]:
        """Get default spawn positions for agents."""
        return [
            (0, 0),  # Agent 0: top-left
            (0, self.GRID_W - 1),  # Agent 1: top-right
            (self.GRID_H - 1, 0),  # Agent 2: bottom-left
            (self.GRID_H - 1, self.GRID_W - 1),  # Agent 3: bottom-right
        ]

    def is_river_tile(self, row: int, col: int) -> bool:
        """Check if a tile is in the river."""
        return col in self.river_columns

    def is_valid_position(self, row: int, col: int) -> bool:
        """Check if position is within grid bounds."""
        return 0 <= row < self.GRID_H and 0 <= col < self.GRID_W

# Default configuration instance
DEFAULT_CONFIG = CleanupConfig()