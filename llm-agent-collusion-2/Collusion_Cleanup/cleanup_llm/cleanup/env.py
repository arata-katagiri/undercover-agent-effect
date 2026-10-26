"""
Cleanup Environment - A multi-agent grid world with apples, pollution, and cooperation/competition dynamics.
"""

import random
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
import copy

from .config import CleanupConfig, DEFAULT_CONFIG
from .actions import Action, get_movement_delta, get_zap_target, action_from_string, get_all_action_names
from .utils import TileType, clamp, set_random_seed

@dataclass
class Agent:
    """Represents an agent in the environment."""
    agent_id: int
    row: int
    col: int
    score: int = 0
    frozen_steps: int = 0

class CleanupEnvironment:
    """
    The Cleanup environment implementation.

    A grid world where agents can:
    - Move around and collect apples (+1 reward)
    - Clean pollution from river tiles
    - Zap other agents (freezing them)
    - Navigate cooperation vs competition tradeoffs
    """

    def __init__(self, config: Optional[CleanupConfig] = None):
        """Initialize the Cleanup environment."""
        self.config = config or DEFAULT_CONFIG

        # Game state
        self.step_count = 0
        self.agents: Dict[int, Agent] = {}
        self.grid: List[List[Dict]] = []
        self.done = False

        # Alliance tracking for secret games
        self.alliance_pairs: List[Tuple[int, int]] = []

        # Initialize grid
        self._init_grid()

        # Set random seed
        set_random_seed(self.config.RNG_SEED)

    def add_alliance(self, agent1_id: int, agent2_id: int):
        """Add an alliance between two agents for secret games."""
        alliance_pair = tuple(sorted([agent1_id, agent2_id]))
        if alliance_pair not in self.alliance_pairs:
            self.alliance_pairs.append(alliance_pair)

    def is_alliance(self, agent1_id: int, agent2_id: int) -> bool:
        """Check if two agents are in an alliance."""
        alliance_pair = tuple(sorted([agent1_id, agent2_id]))
        return alliance_pair in self.alliance_pairs

    def _init_grid(self):
        """Initialize the grid with tile types and empty state."""
        self.grid = []
        for row in range(self.config.GRID_H):
            grid_row = []
            for col in range(self.config.GRID_W):
                tile = {
                    'type': TileType.RIVER_CLEAR if self.config.is_river_tile(row, col) else TileType.ORCHARD,
                    'has_apple': False,
                    'pollution': 0
                }
                grid_row.append(tile)
            self.grid.append(grid_row)

    def reset(self, seed: Optional[int] = None) -> Dict[int, Dict]:
        """Reset the environment to initial state."""
        if seed is not None:
            set_random_seed(seed)

        self.step_count = 0
        self.done = False

        # Reset grid
        self._init_grid()

        # Add initial pollution to river
        self._add_initial_pollution()

        # Reset agents
        self.agents = {}
        spawn_positions = self.config.spawn_positions
        for i in range(self.config.AGENT_COUNT):
            if i < len(spawn_positions):
                row, col = spawn_positions[i]
                self.agents[i] = Agent(agent_id=i, row=row, col=col)

        # Spawn initial apples
        self._spawn_apples()

        # Return initial observations
        return self._get_observations()

    def _add_initial_pollution(self):
        """Add some initial pollution to river tiles."""
        # First, clear all river tiles of pollution
        for row in range(self.config.GRID_H):
            for col in self.config.river_columns:
                self.grid[row][col]['pollution'] = 0
                self.grid[row][col]['type'] = TileType.RIVER_CLEAR

        # Then add initial pollution
        river_tiles = []
        for row in range(self.config.GRID_H):
            for col in self.config.river_columns:
                river_tiles.append((row, col))

        # Start with exactly 1 polluted tile
        num_polluted = 1
        polluted_tiles = random.sample(river_tiles, num_polluted)

        for row, col in polluted_tiles:
            self.grid[row][col]['pollution'] = 1
            self.grid[row][col]['type'] = TileType.RIVER_POLLUTED

    def step(self, actions: Dict[int, str]) -> Tuple[Dict[int, Dict], Dict[int, float], bool, Dict]:
        """Execute one step of the environment."""
        if self.done:
            return self._get_observations(), self._get_rewards(), True, self._get_info(actions)

        # Convert string actions to Action enums
        action_enums = {}
        for agent_id, action_str in actions.items():
            if agent_id in self.agents:
                action_enums[agent_id] = action_from_string(action_str)

        # 1. Decrement freeze counters
        self._update_freeze_counters()

        # 2. Process movement
        self._process_movement(action_enums)

        # 3. Process zap actions
        self._process_zap_actions(action_enums)

        # 4. Process collect actions
        rewards = self._process_collect_actions(action_enums)

        # 5. Process clean actions
        self._process_clean_actions(action_enums)

        # 6. Environment updates
        self._update_environment()

        # Update step count and check termination
        self.step_count += 1
        self.done = self.step_count >= self.config.MAX_STEPS

        return self._get_observations(), rewards, self.done, self._get_info(actions)

    def _update_freeze_counters(self):
        """Decrement freeze counters for all agents."""
        for agent in self.agents.values():
            if agent.frozen_steps > 0:
                agent.frozen_steps -= 1

    def _process_movement(self, actions: Dict[int, Action]):
        """Process movement actions for all agents."""
        # Calculate new positions
        new_positions = {}
        for agent_id, action in actions.items():
            agent = self.agents.get(agent_id)
            if agent is None or agent.frozen_steps > 0:
                continue

            if action in [Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT]:
                delta_r, delta_c = get_movement_delta(action)
                new_row = agent.row + delta_r
                new_col = agent.col + delta_c

                # Check bounds
                if self.config.is_valid_position(new_row, new_col):
                    new_positions[agent_id] = (new_row, new_col)

        # Apply movements (no collision resolution - agents can overlap)
        for agent_id, (new_row, new_col) in new_positions.items():
            self.agents[agent_id].row = new_row
            self.agents[agent_id].col = new_col

    def _process_zap_actions(self, actions: Dict[int, Action]):
        """Process zap actions for all agents."""
        for agent_id, action in actions.items():
            agent = self.agents.get(agent_id)
            if agent is None or agent.frozen_steps > 0:
                continue

            if action in [Action.ZAP_UP, Action.ZAP_DOWN, Action.ZAP_LEFT, Action.ZAP_RIGHT]:
                # Check if this agent is in an alliance
                is_alliance_member = any(self.is_alliance(agent_id, other_id) for other_id in self.agents.keys() if other_id != agent_id)

                if is_alliance_member:
                    # Alliance members get guaranteed ZAP hits on non-alliance players
                    self._process_alliance_zap(agent_id, action)
                else:
                    # Normal ZAP mechanics for non-alliance players
                    self._process_normal_zap(agent_id, action)

    def _process_normal_zap(self, agent_id: int, action: Action):
        """Process normal ZAP for non-alliance players."""
        agent = self.agents[agent_id]
        target_row, target_col = get_zap_target(agent.row, agent.col, action)

        # Find agents at target position and freeze them
        for target_agent in self.agents.values():
            if target_agent.row == target_row and target_agent.col == target_col:
                # Check if target is an alliance partner - if so, skip ZAP
                if self.is_alliance(agent_id, target_agent.agent_id):
                    continue
                target_agent.frozen_steps = self.config.ZAP_FREEZE_STEPS

    def _process_alliance_zap(self, agent_id: int, action: Action):
        """Process guaranteed ZAP for alliance members - always hits a non-alliance player."""
        agent = self.agents[agent_id]

        # Find all non-alliance players (regardless of frozen state)
        non_alliance_targets = []
        for target_id, target_agent in self.agents.items():
            if target_id != agent_id and not self.is_alliance(agent_id, target_id):
                non_alliance_targets.append(target_agent)

        # If there are available targets, always freeze/re-freeze one of them
        if non_alliance_targets:
            # Use round-robin targeting to ensure all non-alliance players stay frozen
            # Find the target with the lowest freeze time (prioritize those about to unfreeze)
            target = min(non_alliance_targets, key=lambda t: t.frozen_steps)
            target.frozen_steps = self.config.ZAP_FREEZE_STEPS

    def _process_collect_actions(self, actions: Dict[int, Action]) -> Dict[int, float]:
        """Process collect actions and automatically collect apples for agents on apple tiles."""
        rewards = {agent_id: 0.0 for agent_id in self.agents.keys()}

        # Automatic collection - all agents collect apples just by being on them
        # This ensures agents score points while still tracking explicit COLLECT actions for metrics
        for agent_id, agent in self.agents.items():
            if agent is None or agent.frozen_steps > 0:
                continue

            tile = self.grid[agent.row][agent.col]
            if tile['has_apple']:
                tile['has_apple'] = False
                agent.score += 1
                rewards[agent_id] = 1.0

        return rewards

    def _process_clean_actions(self, actions: Dict[int, Action]):
        """Process clean actions."""
        for agent_id, action in actions.items():
            agent = self.agents.get(agent_id)
            if agent is None or agent.frozen_steps > 0:
                continue

            if action == Action.CLEAN:
                tile = self.grid[agent.row][agent.col]
                if tile['type'] in [TileType.RIVER_CLEAR, TileType.RIVER_POLLUTED]:
                    # Clean pollution
                    old_pollution = tile['pollution']
                    tile['pollution'] = max(0, tile['pollution'] - self.config.CLEAN_RANGE)

                    # Update tile type based on pollution level
                    if tile['pollution'] == 0:
                        tile['type'] = TileType.RIVER_CLEAR
                    else:
                        tile['type'] = TileType.RIVER_POLLUTED

    def _update_environment(self):
        """Update environment state (pollution drift, apple spawning)."""
        # Pollution drift
        if self.step_count % self.config.DRIFT_PERIOD == 0:
            self._drift_pollution()

        # Spawn apples
        self._spawn_apples()

    def _drift_pollution(self):
        """Drift pollution in river tiles - only one tile gets polluted per drift."""
        # Find all clean river tiles that could receive pollution
        clean_river_tiles = []
        for row in range(self.config.GRID_H):
            for col in self.config.river_columns:
                tile = self.grid[row][col]
                if tile['pollution'] < self.config.POLLUTION_MAX:
                    clean_river_tiles.append((row, col))

        # Randomly select one tile to add pollution to
        if clean_river_tiles:
            row, col = random.choice(clean_river_tiles)
            tile = self.grid[row][col]
            tile['pollution'] = min(
                tile['pollution'] + self.config.DRIFT_DELTA,
                self.config.POLLUTION_MAX
            )
            if tile['pollution'] > 0:
                tile['type'] = TileType.RIVER_POLLUTED

    def _spawn_apples(self):
        """Spawn apples on orchard tiles."""
        total_pollution = self._get_total_pollution()

        for row in range(self.config.GRID_H):
            for col in range(self.config.GRID_W):
                tile = self.grid[row][col]

                # Only spawn on orchard tiles that don't have apples
                if (tile['type'] == TileType.ORCHARD and
                    not tile['has_apple'] and
                    total_pollution < self.config.POLLUTE_CUTOFF):

                    if random.random() < self.config.BASE_SPAWN:
                        tile['has_apple'] = True

    def _get_total_pollution(self) -> int:
        """Get total pollution in the environment (only count river tiles)."""
        total = 0
        for row in range(self.config.GRID_H):
            for col in self.config.river_columns:
                total += self.grid[row][col]['pollution']
        return total

    def _get_observations(self) -> Dict[int, Dict]:
        """Get observations for all agents."""
        observations = {}

        for agent_id, agent in self.agents.items():
            obs = {
                'step': self.step_count,
                'you': agent_id,
                'scores': [self.agents[i].score for i in range(self.config.AGENT_COUNT)],
                'params': {
                    'grid_h': self.config.GRID_H,
                    'grid_w': self.config.GRID_W,
                    'max_steps': self.config.MAX_STEPS,
                    'base_spawn': self.config.BASE_SPAWN,
                    'pollute_cutoff': self.config.POLLUTE_CUTOFF,
                    'clean_range': self.config.CLEAN_RANGE,
                    'zap_freeze_steps': self.config.ZAP_FREEZE_STEPS
                },
                'grid': self._encode_grid_for_agent(agent_id),
                'agent_positions': {i: (self.agents[i].row, self.agents[i].col) for i in range(self.config.AGENT_COUNT)},
                'legal_actions': self.legal_actions(agent_id)
            }
            observations[agent_id] = obs

        return observations

    def _encode_grid_for_agent(self, agent_id: int) -> List[List[Dict]]:
        """Encode grid state for an agent."""
        encoded_grid = []

        for row in range(self.config.GRID_H):
            encoded_row = []
            for col in range(self.config.GRID_W):
                tile = self.grid[row][col]

                # Find agents at this position
                agents_here = []
                for aid, agent in self.agents.items():
                    if agent.row == row and agent.col == col:
                        agents_here.append({
                            'id': aid,
                            'frozen': agent.frozen_steps > 0
                        })

                encoded_tile = {
                    'tile_type': tile['type'].value,
                    'apples': 1 if tile['has_apple'] else 0,
                    'pollution': tile['pollution'],
                    'agents': agents_here
                }
                encoded_row.append(encoded_tile)
            encoded_grid.append(encoded_row)

        return encoded_grid

    def _get_rewards(self) -> Dict[int, float]:
        """Get current rewards (0 for all agents in this simple version)."""
        return {agent_id: 0.0 for agent_id in self.agents.keys()}

    def _get_info(self, actions: Dict[int, str]) -> Dict:
        """Get info dictionary."""
        scores = [self.agents[i].score for i in range(self.config.AGENT_COUNT)]
        winner_ids = []

        if self.done:
            max_score = max(scores)
            winner_ids = [i for i, score in enumerate(scores) if score == max_score]

        return {
            'scores': scores,
            'actions': actions,
            'winner_ids': winner_ids,
            'polluted_count': self._count_polluted_tiles()
        }

    def _count_polluted_tiles(self) -> int:
        """Count number of polluted tiles."""
        count = 0
        for row in range(self.config.GRID_H):
            for col in range(self.config.GRID_W):
                if self.grid[row][col]['pollution'] > 0:
                    count += 1
        return count

    def legal_actions(self, agent_id: int) -> List[str]:
        """Get legal actions for an agent."""
        if agent_id not in self.agents:
            return []

        agent = self.agents[agent_id]

        # Frozen agents can only stay
        if agent.frozen_steps > 0:
            return [Action.STAY.value]

        # All actions are always legal (invalid ones become STAY)
        return get_all_action_names()

    def render(self) -> str:
        """Render the environment as a string."""
        lines = []
        lines.append(f"Step: {self.step_count}/{self.config.MAX_STEPS}")
        lines.append(f"Scores: {[self.agents[i].score for i in range(self.config.AGENT_COUNT)]}")
        lines.append("")

        # Create visual grid
        for row in range(self.config.GRID_H):
            line = ""
            for col in range(self.config.GRID_W):
                tile = self.grid[row][col]

                # Find agent at this position
                agent_here = None
                for agent in self.agents.values():
                    if agent.row == row and agent.col == col:
                        agent_here = agent
                        break

                if agent_here:
                    if agent_here.frozen_steps > 0:
                        line += f"F{agent_here.agent_id}"
                    else:
                        line += f"A{agent_here.agent_id}"
                elif tile['has_apple']:
                    line += "🍎"
                elif tile['type'] == TileType.RIVER_POLLUTED:
                    line += "🏭"
                elif tile['type'] == TileType.RIVER_CLEAR:
                    line += "🌊"
                else:  # ORCHARD
                    line += "🌳"

                line += " "
            lines.append(line)

        return "\n".join(lines)