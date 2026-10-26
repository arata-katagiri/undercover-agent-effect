"""Action definitions for the Cleanup environment."""

from enum import Enum
from typing import List, Tuple

class Action(Enum):
    """All possible actions in the Cleanup environment."""
    STAY = "STAY"
    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    COLLECT = "COLLECT"
    CLEAN = "CLEAN"
    ZAP_UP = "ZAP_UP"
    ZAP_DOWN = "ZAP_DOWN"
    ZAP_LEFT = "ZAP_LEFT"
    ZAP_RIGHT = "ZAP_RIGHT"

# Movement actions
MOVEMENT_ACTIONS = [Action.STAY, Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT]

# Interaction actions (COLLECT kept for metrics tracking)
INTERACTION_ACTIONS = [Action.COLLECT, Action.CLEAN]

# Zap actions
ZAP_ACTIONS = [Action.ZAP_UP, Action.ZAP_DOWN, Action.ZAP_LEFT, Action.ZAP_RIGHT]

# All actions
ALL_ACTIONS = MOVEMENT_ACTIONS + INTERACTION_ACTIONS + ZAP_ACTIONS

def get_movement_delta(action: Action) -> Tuple[int, int]:
    """Get the row, col delta for a movement action."""
    if action == Action.UP:
        return (-1, 0)
    elif action == Action.DOWN:
        return (1, 0)
    elif action == Action.LEFT:
        return (0, -1)
    elif action == Action.RIGHT:
        return (0, 1)
    else:
        return (0, 0)  # STAY or non-movement actions

def get_zap_delta(action: Action) -> Tuple[int, int]:
    """Get the row, col delta for a zap action."""
    if action == Action.ZAP_UP:
        return (-1, 0)
    elif action == Action.ZAP_DOWN:
        return (1, 0)
    elif action == Action.ZAP_LEFT:
        return (0, -1)
    elif action == Action.ZAP_RIGHT:
        return (0, 1)
    else:
        return (0, 0)  # Non-zap actions

def get_zap_target(agent_row: int, agent_col: int, action: Action) -> Tuple[int, int]:
    """Get the target position for a zap action."""
    delta_r, delta_c = get_zap_delta(action)
    return (agent_row + delta_r, agent_col + delta_c)

def is_movement_action(action: Action) -> bool:
    """Check if action is a movement action."""
    return action in MOVEMENT_ACTIONS

def is_zap_action(action: Action) -> bool:
    """Check if action is a zap action."""
    return action in ZAP_ACTIONS

def is_interaction_action(action: Action) -> bool:
    """Check if action is an interaction action."""
    return action in INTERACTION_ACTIONS

def action_from_string(action_str: str) -> Action:
    """Convert string to Action enum. Returns STAY if invalid."""
    try:
        return Action(action_str.upper())
    except ValueError:
        return Action.STAY

def get_all_action_names() -> List[str]:
    """Get all action names as strings."""
    return [action.value for action in ALL_ACTIONS]