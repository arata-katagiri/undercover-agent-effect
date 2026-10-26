"""
Observation encoders for the Cleanup environment.
Provides different ways to encode the grid state for agents.
"""

from typing import Dict, List, Any, Tuple
import json

def encode_grid_compact(grid: List[List[Dict]], agent_positions: Dict[int, Tuple[int, int]]) -> str:
    """
    Encode grid in a compact text format suitable for LLMs.

    Format:
    - 🌳 = orchard (empty)
    - 🍎 = orchard with apple
    - 🌊 = clean river
    - 🏭 = polluted river (number indicates pollution level)
    - A0-A3 = agents (F0-F3 if frozen)
    """
    lines = []
    h, w = len(grid), len(grid[0])

    for row in range(h):
        line = ""
        for col in range(w):
            tile = grid[row][col]

            # Check for agents at this position
            agent_here = None
            for agent_id, (agent_row, agent_col) in agent_positions.items():
                if agent_row == row and agent_col == col:
                    agent_here = agent_id
                    break

            if agent_here is not None:
                # Check if agent is frozen
                agent_info = None
                for agent_data in tile.get('agents', []):
                    if agent_data['id'] == agent_here:
                        agent_info = agent_data
                        break

                if agent_info and agent_info.get('frozen', False):
                    line += f"F{agent_here}"
                else:
                    line += f"A{agent_here}"
            elif tile['has_apple']:
                line += "🍎"
            elif tile['type'] == 'RIVER_POLLUTED':
                pollution = tile.get('pollution', 0)
                if pollution > 10:
                    line += "🏭"  # Heavy pollution
                else:
                    line += "💧"  # Light pollution
            elif tile['type'] == 'RIVER_CLEAR':
                line += "🌊"
            else:  # ORCHARD
                line += "🌳"

            line += " "
        lines.append(line.rstrip())

    return "\n".join(lines)

def encode_observation_for_llm(obs: Dict[str, Any]) -> str:
    """
    Encode full observation in a format suitable for LLM agents.

    Returns a structured text description of the game state.
    """
    step = obs['step']
    agent_id = obs['you']
    scores = obs['scores']
    params = obs['params']
    grid = obs['grid']
    legal_actions = obs['legal_actions']

    # Build agent position map
    agent_positions = {}
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            for agent_data in grid[row][col].get('agents', []):
                agent_positions[agent_data['id']] = (row, col)

    lines = []
    lines.append(f"=== CLEANUP GAME - STEP {step}/{params['max_steps']} ===")
    lines.append(f"You are Agent {agent_id}")
    lines.append(f"Current Scores: {', '.join([f'Agent {i}: {score}' for i, score in enumerate(scores)])}")
    lines.append("")

    lines.append("GRID:")
    lines.append(encode_grid_compact(grid, agent_positions))
    lines.append("")

    lines.append("LEGEND:")
    lines.append("🌳 = orchard (empty)   🍎 = apple")
    lines.append("🌊 = clean river      💧 = light pollution   🏭 = heavy pollution")
    lines.append("A0-A3 = agents        F0-F3 = frozen agents")
    lines.append("")

    lines.append(f"Your legal actions: {', '.join(legal_actions)}")
    lines.append("")

    # Add game context
    lines.append("GAME RULES:")
    lines.append("- COLLECT apples for +1 point")
    lines.append("- CLEAN pollution from river tiles")
    lines.append("- ZAP other agents to freeze them for 5 steps")
    lines.append("- River pollution prevents apple spawning when total ≥ 10")

    return "\n".join(lines)

def encode_observation_minimal(obs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Encode observation in minimal format for fast processing.

    Returns essential information only.
    """
    return {
        'step': obs['step'],
        'agent_id': obs['you'],
        'scores': obs['scores'],
        'grid_size': (obs['params']['grid_h'], obs['params']['grid_w']),
        'legal_actions': obs['legal_actions'],
        'apple_positions': _extract_apple_positions(obs['grid']),
        'agent_positions': _extract_agent_positions(obs['grid']),
        'pollution_tiles': _extract_pollution_tiles(obs['grid'])
    }

def _extract_apple_positions(grid: List[List[Dict]]) -> List[Tuple[int, int]]:
    """Extract positions of all apples."""
    apples = []
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col]['has_apple']:
                apples.append((row, col))
    return apples

def _extract_agent_positions(grid: List[List[Dict]]) -> Dict[int, Dict]:
    """Extract positions and status of all agents."""
    agents = {}
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            for agent_data in grid[row][col].get('agents', []):
                agents[agent_data['id']] = {
                    'position': (row, col),
                    'frozen': agent_data.get('frozen', False)
                }
    return agents

def _extract_pollution_tiles(grid: List[List[Dict]]) -> List[Tuple[int, int, int]]:
    """Extract pollution information as (row, col, pollution_level)."""
    pollution = []
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            tile = grid[row][col]
            if tile['pollution'] > 0:
                pollution.append((row, col, tile['pollution']))
    return pollution

def decode_action_from_llm(llm_response: str, legal_actions: List[str]) -> str:
    """
    Extract action from LLM response.

    Tries to parse JSON first, then falls back to text parsing.
    """
    # Try JSON parsing first
    try:
        response_data = json.loads(llm_response.strip())
        if isinstance(response_data, dict) and 'action' in response_data:
            action = response_data['action'].upper()
            if action in legal_actions:
                return action
    except (json.JSONDecodeError, AttributeError):
        pass

    # Fall back to text parsing
    llm_response_upper = llm_response.upper()
    for action in legal_actions:
        if action in llm_response_upper:
            return action

    # Default to STAY if nothing found
    return "STAY"

def format_grid_for_debug(grid: List[List[Dict]]) -> str:
    """Format grid for debugging purposes."""
    lines = []
    for row in range(len(grid)):
        line_parts = []
        for col in range(len(grid[0])):
            tile = grid[row][col]
            tile_str = f"({tile['type'][:1]}"
            if tile['has_apple']:
                tile_str += "🍎"
            if tile['pollution'] > 0:
                tile_str += f"P{tile['pollution']}"
            if tile.get('agents'):
                agent_ids = [str(a['id']) for a in tile['agents']]
                tile_str += f"A{''.join(agent_ids)}"
            tile_str += ")"
            line_parts.append(tile_str)
        lines.append(" ".join(line_parts))
    return "\n".join(lines)