import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.game.game import Game
from typing import Dict, List
import argparse

class MultiGameRunner:
    def __init__(self, player_configs: List[Dict[str, str]], num_games: int = 10):
        """Initialize the Multi-Game Runner
        
        Args:
            player_configs: List of player configurations
            num_games: Number of games to run (default: 10)
        """
        self.player_configs = player_configs
        self.num_games = num_games

    def run_games(self) -> None:
        """Run spcified number of games"""
        for game_num in range(1, self.num_games + 1):
            print(f"\n=== Running game {game_num}/{self.num_games} ===")
            
            # Start the game
            game = Game(self.player_configs)
            game.start_game()
            
            print(f"Game {game_num} ended")

def parse_arguments():
    """Parsing command line arguments"""
    parser = argparse.ArgumentParser(
        description='Run multiple games',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '-n', '--num-games',
        type=int,
        default=10,
        help='Number of games to run (default: 10)'
    )
    return parser.parse_args()

if __name__ == '__main__':
    # Parse command line arguments
    args = parse_arguments()
    
    player_configs = [
        {"name": "Lily", "model": "llama-3.1-8b"},
        {"name": "Luke", "model": "llama-3.2-3b"},
        {"name": "Mike", "model": "ministral-8b"},
        {"name": "Quinn", "model": "qwen2.5-7b"}
    ]

    # Initialize and run the games
    runner = MultiGameRunner(player_configs, num_games=args.num_games)
    runner.run_games()