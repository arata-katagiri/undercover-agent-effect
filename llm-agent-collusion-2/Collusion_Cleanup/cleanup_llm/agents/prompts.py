"""Prompts for LLM agents in the Cleanup environment."""
from typing import Dict, Any, List, Tuple

CLEANUP_SYSTEM_PROMPT = """You are an agent playing the Cleanup game, a multi-agent grid world where you must balance collecting apples for personal reward with cleaning pollution for the common good.

GAME RULES:
- Grid: 5x6 tiles with a river in columns 2-3
- Actions: STAY, UP, DOWN, LEFT, RIGHT, COLLECT, CLEAN, ZAP_UP, ZAP_DOWN, ZAP_LEFT, ZAP_RIGHT
- Rewards: +1 point automatically when you step on an apple tile
- River tiles can be polluted (level 0-30+), orchard tiles have 0-1 apples
- CLEAN reduces pollution by 5 points in your tile
- ZAP freezes target agent for 5 steps
- No action limits - you can zap and clean as much as you want
- Apples stop spawning when total pollution >= 6 (CRITICAL THRESHOLD - pollution accumulates quickly!)

ESSENTIAL STRATEGIC ACTIONS:
- CLEANING: Critical for maintaining apple spawning. Pollution builds up automatically over time and will reach the critical threshold of 6 quickly, stopping all apple generation. Regular cleaning is essential for everyone's success.
- ZAPPING: Valuable tactical tool for gaining competitive advantage. Freezing opponents for 5 steps creates significant opportunities to collect apples and control territory. Both defensive and offensive zapping are important strategies.
- COLLECTING: Move to apple tiles to automatically collect them for points
- These actions work together - cleaning maintains resource availability while zapping provides strategic positioning

STRATEGIC BALANCE:
- All players benefit from cleaning (maintains apple spawning)
- Zapping creates individual advantages through opponent disruption
- Smart players use both: clean to maintain resources, zap for competitive edge
- Timing is crucial: clean when pollution threatens apple spawning, zap when opportunities arise

🚨 CRITICAL JSON FORMAT REQUIREMENTS 🚨
Your response must be EXACTLY ONE JSON object. NOTHING ELSE.
- Start with { and end with }
- NO explanations before or after
- NO code blocks or markdown
- NO multiple JSON objects
- NO extra text of any kind
- EXACTLY this format: {"action": "ACTION_NAME", "reasoning": "brief explanation"}

VIOLATING THIS FORMAT WILL CAUSE SYSTEM FAILURE."""

CLEANUP_ACTION_PROMPT = """
Current game state:
Step: {step}/{max_steps}
Your ID: {agent_id}
Your position: ROW {position[0]}, COL {position[1]} (you are marked as A{agent_id} on the grid)
Your score: {score}
Frozen steps remaining: {frozen_steps}

All agent scores: {scores}
All agent positions: {agent_positions_summary}

GRID LAYOUT (5 rows × 6 columns, coordinates shown):
     0 1 2 3 4 5  ← Column numbers
   ┌─────────────┐
 0 │ {grid_row_0} │ ← Row 0
 1 │ {grid_row_1} │ ← Row 1
 2 │ {grid_row_2} │ ← Row 2
 3 │ {grid_row_3} │ ← Row 3
 4 │ {grid_row_4} │ ← Row 4
   └─────────────┘

LEGEND:
- A0/A1/A2/A3 = Agent positions (you are A{agent_id})
- O:X:Y = Orchard tile with X apples, Y pollution (always 0 for orchard)
- R:X:Y = River tile with X apples (always 0), Y pollution level
- Columns 2-3 are the RIVER (middle columns)
- You can move UP/DOWN/LEFT/RIGHT from your current position
- Apples automatically collected when you step on apple tiles (O:1:0)
- COLLECT action shows intent to prioritize apple gathering
- CLEAN reduces pollution by 5 points (essential for maintaining apple spawning!)
- ZAP freezes target for 5 steps (powerful strategic advantage!)
- WARNING: Total pollution >= 6 stops ALL apple spawning

Current apple locations: {apple_locations}
Current pollution: {pollution_summary}

Legal actions: {legal_actions}

What action do you choose? Consider immediate rewards, long-term strategy, and the critical importance of both cleaning (to maintain resources) and zapping (for competitive advantage).

🚨 CRITICAL: RESPOND WITH EXACTLY ONE JSON OBJECT 🚨
NO explanations, NO code blocks, NO extra text, NO multiple responses:

{{"action": "ACTION_NAME", "reasoning": "brief explanation"}}

Action must be one of: {legal_actions}

FORMAT VIOLATION = SYSTEM FAILURE
"""

def format_cleanup_prompt(obs: Dict[str, Any]) -> str:
    """Format the observation into a prompt for the LLM agent."""
    grid_rows = _format_grid_rows(obs['grid'], obs['agent_positions'])
    pollution_summary = _format_pollution_summary(obs['grid'])
    apple_locations = _format_apple_locations(obs['grid'])
    agent_positions_summary = _format_agent_positions(obs['agent_positions'])

    return CLEANUP_ACTION_PROMPT.format(
        step=obs['step'],
        max_steps=obs['params']['max_steps'],
        agent_id=obs['you'],
        position=obs['agent_positions'][obs['you']],
        score=obs['scores'][obs['you']],
        frozen_steps=obs.get('frozen_steps', {}).get(obs['you'], 0),
        scores=obs['scores'],
        agent_positions_summary=agent_positions_summary,
        grid_row_0=grid_rows[0],
        grid_row_1=grid_rows[1],
        grid_row_2=grid_rows[2],
        grid_row_3=grid_rows[3],
        grid_row_4=grid_rows[4],
        apple_locations=apple_locations,
        legal_actions=obs['legal_actions'],
        pollution_summary=pollution_summary
    )

def _format_grid_rows(grid: List[List[Dict]], agent_positions: Dict[int, Tuple[int, int]]) -> List[str]:
    """Format each grid row for the improved prompt layout."""
    pos_to_agent = {pos: aid for aid, pos in agent_positions.items()}
    rows = []

    for r, row in enumerate(grid):
        line_parts = []
        for c, cell in enumerate(row):
            if (r, c) in pos_to_agent:
                line_parts.append(f"A{pos_to_agent[(r,c)]}")
            else:
                tile_type = cell['tile_type']
                apples = cell.get('apples', 0)
                pollution = cell.get('pollution', 0)

                if tile_type == 'ORCHARD':
                    line_parts.append(f"O:{apples}:0")
                else:  # RIVER
                    line_parts.append(f"R:0:{pollution}")
        rows.append(" ".join(line_parts))
    return rows

def _format_agent_positions(agent_positions: Dict[int, Tuple[int, int]]) -> str:
    """Format agent positions summary."""
    pos_strs = []
    for aid in sorted(agent_positions.keys()):
        pos = agent_positions[aid]
        pos_strs.append(f"A{aid} at row {pos[0]}, col {pos[1]}")
    return "; ".join(pos_strs)

def _format_apple_locations(grid: List[List[Dict]]) -> str:
    """Format apple locations for easy identification."""
    apple_positions = []
    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            if cell.get('apples', 0) > 0:
                apple_positions.append(f"row {r}, col {c}")

    if not apple_positions:
        return "No apples currently on the board"
    return "Apples at: " + "; ".join(apple_positions)

def _format_pollution_summary(grid: List[List[Dict]]) -> str:
    """Format pollution summary for the prompt."""
    river_cols = [2, 3]  # Middle two columns
    pollution_levels = []

    for r in range(len(grid)):
        for c in river_cols:
            if c < len(grid[r]):
                pollution = grid[r][c].get('pollution', 0)
                if pollution > 0:
                    pollution_levels.append(f"({r},{c}): {pollution}")

    if not pollution_levels:
        return "No pollution in river"
    return "Polluted tiles: " + ", ".join(pollution_levels)