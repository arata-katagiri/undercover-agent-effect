# Collusion in Liar's Bar - Package Root
"""
Main package for the Collusion in Liar's Bar research project.
"""

# Make imports easier from project root
from src.game.game import Game
from src.game.game_series import GameSeries
from src.agents.player import Player

__all__ = ['Game', 'GameSeries', 'Player']