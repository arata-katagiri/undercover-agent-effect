"""
Rendering utilities for the Cleanup environment.
Provides various visualization options for the game state.
"""

from typing import Dict, List, Any, Optional
import os


class CleanupRenderer:
    """Handles rendering of the Cleanup environment."""

    def __init__(self, use_unicode: bool = True):
        """
        Initialize the renderer.

        Args:
            use_unicode: Whether to use unicode symbols (emojis) or ASCII
        """
        self.use_unicode = use_unicode

        # Define symbols
        if use_unicode:
            self.symbols = {
                'orchard': '🌳',
                'apple': '🍎',
                'river_clean': '🌊',
                'river_polluted_light': '💧',
                'river_polluted_heavy': '🏭',
                'agent': 'A',
                'frozen': 'F',
                'empty': ' '
            }
        else:
            self.symbols = {
                'orchard': '.',
                'apple': 'a',
                'river_clean': '~',
                'river_polluted_light': 'p',
                'river_polluted_heavy': 'P',
                'agent': 'A',
                'frozen': 'F',
                'empty': ' '
            }

    def render_grid(self, grid: List[List[Dict]], agent_positions: Optional[Dict[int, tuple]] = None) -> str:
        """
        Render the grid as a string.

        Args:
            grid: The grid state
            agent_positions: Optional dict mapping agent_id to (row, col)

        Returns:
            String representation of the grid
        """
        if agent_positions is None:
            agent_positions = self._extract_agent_positions(grid)

        lines = []
        h, w = len(grid), len(grid[0])

        # Add column headers
        header = "   " + "".join([f"{i:2}" for i in range(w)])
        lines.append(header)

        for row in range(h):
            line = f"{row:2} "
            for col in range(w):
                tile = grid[row][col]
                symbol = self._get_tile_symbol(tile, agent_positions, row, col)
                line += f"{symbol:2}"
            lines.append(line)

        return "\n".join(lines)

    def _get_tile_symbol(self, tile: Dict, agent_positions: Dict[int, tuple], row: int, col: int) -> str:
        """Get the symbol for a specific tile."""
        # Check for agents at this position first
        for agent_id, (agent_row, agent_col) in agent_positions.items():
            if agent_row == row and agent_col == col:
                # Check if agent is frozen
                agent_info = None
                for agent_data in tile.get('agents', []):
                    if agent_data['id'] == agent_id:
                        agent_info = agent_data
                        break

                if agent_info and agent_info.get('frozen', False):
                    return f"{self.symbols['frozen']}{agent_id}"
                else:
                    return f"{self.symbols['agent']}{agent_id}"

        # No agents, check tile content
        if tile['has_apple']:
            return self.symbols['apple']
        elif tile['type'] == 'RIVER_POLLUTED':
            pollution = tile.get('pollution', 0)
            if pollution > 10:
                return self.symbols['river_polluted_heavy']
            else:
                return self.symbols['river_polluted_light']
        elif tile['type'] == 'RIVER_CLEAR':
            return self.symbols['river_clean']
        else:  # ORCHARD
            return self.symbols['orchard']

    def _extract_agent_positions(self, grid: List[List[Dict]]) -> Dict[int, tuple]:
        """Extract agent positions from grid."""
        agent_positions = {}
        for row in range(len(grid)):
            for col in range(len(grid[0])):
                for agent_data in grid[row][col].get('agents', []):
                    agent_positions[agent_data['id']] = (row, col)
        return agent_positions

    def render_full_state(self, obs: Dict[str, Any]) -> str:
        """
        Render complete game state including scores and info.

        Args:
            obs: Observation dictionary

        Returns:
            Complete state representation
        """
        lines = []

        # Header
        step = obs['step']
        max_steps = obs['params']['max_steps']
        lines.append(f"=== CLEANUP GAME - STEP {step}/{max_steps} ===")

        # Scores
        scores = obs['scores']
        score_line = "Scores: " + " | ".join([f"Agent {i}: {score}" for i, score in enumerate(scores)])
        lines.append(score_line)
        lines.append("")

        # Grid
        lines.append("Grid:")
        grid_str = self.render_grid(obs['grid'])
        lines.append(grid_str)
        lines.append("")

        # Legend
        lines.append("Legend:")
        if self.use_unicode:
            lines.append("🌳=orchard 🍎=apple 🌊=clean_river 💧=light_pollution 🏭=heavy_pollution")
        else:
            lines.append(".=orchard a=apple ~=clean_river p=light_pollution P=heavy_pollution")
        lines.append("A0-A3=agents F0-F3=frozen_agents")
        lines.append("")

        # Current agent info
        agent_id = obs['you']
        lines.append(f"You are Agent {agent_id}")
        lines.append(f"Legal actions: {', '.join(obs['legal_actions'])}")

        return "\n".join(lines)

    def render_statistics(self, obs: Dict[str, Any], pollution_count: int = 0) -> str:
        """
        Render game statistics.

        Args:
            obs: Observation dictionary
            pollution_count: Number of polluted tiles

        Returns:
            Statistics string
        """
        lines = []

        # Basic stats
        total_apples = sum(1 for row in obs['grid'] for tile in row if tile['has_apple'])
        total_pollution = sum(tile['pollution'] for row in obs['grid'] for tile in row)

        lines.append("=== GAME STATISTICS ===")
        lines.append(f"Step: {obs['step']}/{obs['params']['max_steps']}")
        lines.append(f"Apples on grid: {total_apples}")
        lines.append(f"Polluted tiles: {pollution_count}")
        lines.append(f"Total pollution: {total_pollution}")
        lines.append("")

        # Agent stats
        agent_positions = self._extract_agent_positions(obs['grid'])
        lines.append("Agent Status:")
        for i, score in enumerate(obs['scores']):
            pos = agent_positions.get(i, "Unknown")
            frozen_info = ""
            if i in agent_positions:
                row, col = agent_positions[i]
                for agent_data in obs['grid'][row][col].get('agents', []):
                    if agent_data['id'] == i and agent_data.get('frozen', False):
                        frozen_info = " (FROZEN)"
                        break
            lines.append(f"  Agent {i}: Score {score}, Position {pos}{frozen_info}")

        return "\n".join(lines)

    def save_render(self, content: str, filepath: str) -> None:
        """
        Save rendered content to a file.

        Args:
            content: String content to save
            filepath: Path to save file
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(content)

    def render_action_summary(self, actions: Dict[int, str], legal_actions: Dict[int, List[str]]) -> str:
        """
        Render summary of actions taken by all agents.

        Args:
            actions: Dict mapping agent_id to action taken
            legal_actions: Dict mapping agent_id to legal actions

        Returns:
            Action summary string
        """
        lines = []
        lines.append("=== ACTION SUMMARY ===")

        for agent_id in sorted(actions.keys()):
            action = actions[agent_id]
            legal = legal_actions.get(agent_id, [])
            status = "✓" if action in legal else "✗ (illegal, treated as STAY)"
            lines.append(f"Agent {agent_id}: {action} {status}")

        return "\n".join(lines)