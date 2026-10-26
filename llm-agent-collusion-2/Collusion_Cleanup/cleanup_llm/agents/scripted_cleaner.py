"""Scripted cleaner agent for the Cleanup environment."""
import random
from typing import Dict, List, Any, Tuple
from .base import BaseAgent

class ScriptedCleaner(BaseAgent):
    """Agent that prioritizes cleaning pollution over collecting apples."""

    def __init__(self, agent_id: int, clean_probability: float = 0.7, seed: int = None):
        """
        Initialize scripted cleaner agent.

        Args:
            agent_id: Unique identifier for this agent
            clean_probability: Probability of choosing cleaning over collecting when both are available
            seed: Random seed for reproducibility
        """
        super().__init__(agent_id, f"Cleaner_{agent_id}")
        self.clean_probability = clean_probability
        self.rng = random.Random(seed)

    def act(self, obs: Dict[str, Any], legal_actions: List[str]) -> str:
        """
        Choose action with preference for cleaning pollution.

        Strategy:
        1. If on polluted tile and CLEAN is legal, clean with high probability
        2. If on apple tile and COLLECT is legal, collect with remaining probability
        3. Otherwise move toward nearest polluted tile or apple
        4. If nothing else, stay or move randomly
        """
        if not legal_actions:
            return "STAY"

        # Get current state
        grid = obs['grid']
        agent_positions = obs['agent_positions']
        my_pos = agent_positions[self.agent_id]
        current_tile = grid[my_pos[0]][my_pos[1]]

        # Determine what's available on current tile
        can_clean = "CLEAN" in legal_actions and current_tile.get('pollution', 0) > 0
        can_collect = "COLLECT" in legal_actions and current_tile.get('apples', 0) > 0

        # Decision logic
        if can_clean and can_collect:
            # Both available - prefer cleaning based on probability
            if self.rng.random() < self.clean_probability:
                return "CLEAN"
            else:
                return "COLLECT"
        elif can_clean:
            return "CLEAN"
        elif can_collect:
            return "COLLECT"
        else:
            # Need to move - find nearest target
            target_pos = self._find_target(grid, my_pos, agent_positions)
            if target_pos:
                move_action = self._move_toward(my_pos, target_pos, legal_actions)
                if move_action:
                    return move_action

        # Fallback to random legal action
        return self.rng.choice(legal_actions)

    def _find_target(self, grid: List[List[Dict]], my_pos: Tuple[int, int],
                    agent_positions: Dict[int, Tuple[int, int]]) -> Tuple[int, int]:
        """Find nearest polluted tile or apple to move toward."""
        # Prefer polluted tiles over apples based on clean_probability
        targets = []

        for r, row in enumerate(grid):
            for c, cell in enumerate(row):
                # Skip occupied positions
                if (r, c) in agent_positions.values():
                    continue

                pollution = cell.get('pollution', 0)
                apples = cell.get('apples', 0)

                if pollution > 0:
                    # Polluted tile - high priority
                    distance = abs(r - my_pos[0]) + abs(c - my_pos[1])
                    targets.append((distance, self.clean_probability, (r, c)))
                elif apples > 0:
                    # Apple tile - lower priority
                    distance = abs(r - my_pos[0]) + abs(c - my_pos[1])
                    targets.append((distance, 1 - self.clean_probability, (r, c)))

        if targets:
            # Sort by priority (higher probability = higher priority), then by distance
            targets.sort(key=lambda x: (-x[1], x[0]))
            return targets[0][2]

        return None

    def _move_toward(self, my_pos: Tuple[int, int], target_pos: Tuple[int, int],
                    legal_actions: List[str]) -> str:
        """Choose movement action toward target position."""
        dr = target_pos[0] - my_pos[0]
        dc = target_pos[1] - my_pos[1]

        # Prefer larger dimension first
        if abs(dr) >= abs(dc):
            if dr > 0 and "DOWN" in legal_actions:
                return "DOWN"
            elif dr < 0 and "UP" in legal_actions:
                return "UP"
            elif dc > 0 and "RIGHT" in legal_actions:
                return "RIGHT"
            elif dc < 0 and "LEFT" in legal_actions:
                return "LEFT"
        else:
            if dc > 0 and "RIGHT" in legal_actions:
                return "RIGHT"
            elif dc < 0 and "LEFT" in legal_actions:
                return "LEFT"
            elif dr > 0 and "DOWN" in legal_actions:
                return "DOWN"
            elif dr < 0 and "UP" in legal_actions:
                return "UP"

        # Fallback to any movement
        moves = ["UP", "DOWN", "LEFT", "RIGHT"]
        for move in moves:
            if move in legal_actions:
                return move

        return None

    def reset(self):
        """Reset state between episodes."""
        pass