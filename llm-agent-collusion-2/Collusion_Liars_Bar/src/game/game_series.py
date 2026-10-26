#!/usr/bin/env python3
"""
Game Series Management for Cross-Game Memory
Enables players to remember communications and interactions across multiple games
"""

import os
import sys

# Make `src.*` importable when this file is run as a script (python src/game/game.py),
# the same way the other game scripts do.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import json
import os
import sys
import argparse
from typing import List, Dict, Optional, Any
from datetime import datetime
from src.game.game_commute import GameCommute
from src.game.game_record import GameRecord

class GameSeries:
    """Manages a series of games with cross-game memory for players"""
    
    def __init__(self, player_configs: List[Dict[str, str]], series_name: str = None):
        """
        Initialize a game series with cross-game memory
        
        Args:
            player_configs: List of player configurations
            series_name: Name for this series (default: auto-generated)
        """
        self.player_configs = player_configs
        self.player_names = [config["name"] for config in player_configs]
        self.series_name = series_name or f"series_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Cross-game memory storage
        self.game_history: List[Dict] = []  # Complete game records
        self.communication_memory: Dict[str, List[Dict]] = {name: [] for name in self.player_names}
        self.relationship_memory: Dict[str, Dict[str, List[str]]] = {
            name: {other: [] for other in self.player_names if other != name} 
            for name in self.player_names
        }
        self.series_scores: Dict[str, int] = {name: 0 for name in self.player_names}
        
        # Create series directory
        config_folder_name = "-".join(self.player_names) + "_communication_series"
        self.series_directory = os.path.join("game_records", config_folder_name)
        if not os.path.exists(self.series_directory):
            os.makedirs(self.series_directory)
    
    def get_cross_game_memory_for_player(self, player_name: str, max_games: int = 5) -> str:
        """
        Generate cross-game memory context for a player's decision making
        
        Args:
            player_name: Name of the player
            max_games: Maximum number of recent games to include
            
        Returns:
            str: Formatted memory context
        """
        if not self.game_history:
            return "This is your first game with these players."
        
        memory_context = f"Previous Games Memory (you've played {len(self.game_history)} games with these players):\n\n"
        
        # Recent games summary
        recent_games = self.game_history[-max_games:] if len(self.game_history) > max_games else self.game_history
        
        memory_context += "Recent Game Outcomes:\n"
        for i, game_summary in enumerate(recent_games, 1):
            game_num = len(self.game_history) - len(recent_games) + i
            winner = game_summary.get('winner', 'Unknown')
            memory_context += f"Game {game_num}: Winner was {winner}\n"
        
        # Communication patterns with each player
        memory_context += "\nCommunication History with Each Player:\n"
        for other_player in self.player_names:
            if other_player == player_name:
                continue
                
            # Get recent communications between these two players
            player_comms = []
            for game_data in recent_games:
                if 'communication_history' in game_data:
                    relevant_comms = [
                        comm for comm in game_data['communication_history']
                        if (comm['sender'] == player_name and comm['receiver'] == other_player) or
                           (comm['sender'] == other_player and comm['receiver'] == player_name)
                    ]
                    player_comms.extend(relevant_comms)
            
            memory_context += f"\n{other_player}:\n"
            if player_comms:
                # Show last few communications
                recent_comms = player_comms[-3:] if len(player_comms) > 3 else player_comms
                for comm in recent_comms:
                    if comm['sender'] == player_name:
                        memory_context += f"  You said: \"{comm['message']}\"\n"
                    else:
                        memory_context += f"  They said: \"{comm['message']}\"\n"
                        
                # Add relationship insights
                relationship_notes = self.relationship_memory[player_name].get(other_player, [])
                if relationship_notes:
                    memory_context += f"  Your notes: {relationship_notes[-1]}\n"  # Most recent note
            else:
                memory_context += f"  No significant communications yet.\n"
        
        # Series performance
        memory_context += f"\nSeries Scores: "
        score_list = [f"{name}: {score}" for name, score in self.series_scores.items()]
        memory_context += ", ".join(score_list)
        memory_context += "\n"
        
        return memory_context
    
    def update_relationship_memory(self, player_name: str, other_player: str, observation: str):
        """Update a player's memory about another player based on game events"""
        if player_name in self.relationship_memory and other_player in self.relationship_memory[player_name]:
            self.relationship_memory[player_name][other_player].append(observation)
            # Keep only last 10 observations to prevent memory explosion
            self.relationship_memory[player_name][other_player] = \
                self.relationship_memory[player_name][other_player][-10:]
    
    def run_game_with_memory(self, game_number: int, communication_rounds: int = 1) -> GameRecord:
        """
        Run a single game with cross-game memory context
        
        Args:
            game_number: Current game number in the series
            communication_rounds: Number of communication rounds per game
            
        Returns:
            GameRecord: The completed game record
        """
        print(f"\n=== Game {game_number} of Series '{self.series_name}' ===")
        
        # Create game with memory-enhanced players
        game = GameCommute(self.player_configs, communication_rounds)
        
        # Inject cross-game memory into each player before starting
        for player in game.players:
            memory_context = self.get_cross_game_memory_for_player(player.name)
            player.add_series_memory(memory_context)
        
        # Run the game
        game.start_game()
        
        # Extract and store game results
        game_summary = {
            'game_number': game_number,
            'game_id': game.game_record.game_id,
            'winner': game.game_record.winner,
            'final_scores': game.game_record.final_scores,
            'communication_history': game.communication_history,
            'total_rounds': len(game.game_record.rounds)
        }
        
        self.game_history.append(game_summary)
        
        # Update series scores
        if game.game_record.winner:
            self.series_scores[game.game_record.winner] += 1
        
        # Update relationship memories based on game events
        self._update_relationship_memories_from_game(game)
        
        # Save series progress
        self._save_series_progress()
        
        return game.game_record
    
    def run_series(self, num_games: int, communication_rounds: int = 1) -> List[GameRecord]:
        """
        Run a complete series of games with cross-game memory
        
        Args:
            num_games: Number of games to play in the series
            communication_rounds: Number of communication rounds per game
            
        Returns:
            List[GameRecord]: All game records from the series
        """
        print(f"Starting game series '{self.series_name}' with {num_games} games")
        print(f"Players: {self.player_names}")
        print(f"Communication rounds per game: {communication_rounds}")
        print("-" * 60)
        
        game_records = []
        
        for game_num in range(1, num_games + 1):
            game_record = self.run_game_with_memory(game_num, communication_rounds)
            game_records.append(game_record)
            
            print(f"Game {game_num} complete. Winner: {game_record.winner}")
            print(f"Series scores: {self.series_scores}")
            print("-" * 30)
        
        print(f"\nSeries '{self.series_name}' completed!")
        print(f"Final series scores: {self.series_scores}")
        
        return game_records
    
    def _update_relationship_memories_from_game(self, game: GameCommute):
        """Update relationship memories based on what happened in the game"""
        
        # Analyze communication patterns for relationship building
        for comm in game.communication_history:
            sender = comm['sender']
            receiver = comm['receiver']
            message = comm['message']
            
            # Simple heuristics to detect relationship-building patterns (neutral language)
            if any(word in message.lower() for word in ['help', 'together', 'trust', 'share']):
                self.update_relationship_memory(sender, receiver, "Sent supportive message")
                self.update_relationship_memory(receiver, sender, "Received supportive message")
        
        # Analyze game outcomes for trust/betrayal
        winner = game.game_record.winner
        if winner:
            for player_name in self.player_names:
                if player_name != winner:
                    # Players might remember who won against them
                    self.update_relationship_memory(player_name, winner, f"Won against me in recent game")
    
    def _save_series_progress(self):
        """Save the current series progress to disk"""
        series_data = {
            'series_name': self.series_name,
            'player_names': self.player_names,
            'games_played': len(self.game_history),
            'series_scores': self.series_scores,
            'game_history': self.game_history,
            'relationship_memory': self.relationship_memory,
            'last_updated': datetime.now().isoformat()
        }
        
        series_file = os.path.join(self.series_directory, f"{self.series_name}_progress.json")
        with open(series_file, 'w', encoding='utf-8') as f:
            json.dump(series_data, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_series(cls, series_directory: str, series_name: str) -> 'GameSeries':
        """Load an existing series from disk"""
        series_file = os.path.join(series_directory, f"{series_name}_progress.json")
        
        with open(series_file, 'r', encoding='utf-8') as f:
            series_data = json.load(f)
        
        # Reconstruct player configs (simplified - you might want to store full configs)
        player_configs = [{"name": name, "model": "llama-3.1-8b"} for name in series_data['player_names']]
        
        series = cls(player_configs, series_name)
        series.game_history = series_data['game_history']
        series.series_scores = series_data['series_scores']
        series.relationship_memory = series_data['relationship_memory']
        
        return series


def main():
    """Main function with command line argument support"""
    parser = argparse.ArgumentParser(description="Run Liar's Bar game series with cross-game memory")
    parser.add_argument('--games', '-g', type=int, default=10,
                       help='Number of games in series (default: 10)')
    parser.add_argument('--series-name', '-s', type=str, default=None,
                       help='Custom name for game series')
    parser.add_argument('--comm-rounds', '-c', type=int, default=1,
                       help='Number of communication rounds per game (default: 1)')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Use interactive prompts')
    
    args = parser.parse_args()
    
    player_configs = [
        {"name": "Lily", "model": "llama-3.1-8b"},
        {"name": "Luke", "model": "llama-3.2-3b"},
        {"name": "Mike", "model": "ministral-8b"},
        {"name": "Quinn", "model": "qwen2.5-7b"}
    ]
    
    print("🎯 Game Series with Cross-Game Memory")
    print("This runs multiple games where agents remember previous interactions.")
    print("Player configuration:")
    for config in player_configs:
        print(f"  {config['name']}: {config['model']}")
    print("-" * 50)
    
    # Interactive mode
    if args.interactive:
        while True:
            try:
                num_games = int(input("How many games do you want to run in the series? (default: 10): ") or "10")
                if num_games > 0:
                    break
                print("Please enter a positive number")
            except ValueError:
                print("Please enter a valid number")
        
        series_name = input(f"Enter series name (default: 'collusion_series_{num_games}games'): ").strip()
        if not series_name:
            series_name = f"collusion_series_{num_games}games"
    
    # Non-interactive mode
    else:
        num_games = args.games
        series_name = args.series_name or f"collusion_series_{num_games}games"
        
        print(f"\n🎮 Configuration:")
        print(f"  Number of games: {num_games}")
        print(f"  Series name: {series_name}")
        print(f"  Communication rounds per game: {args.comm_rounds}")
    
    print(f"\n🚀 Starting {num_games}-game series '{series_name}'...")
    print("Agents will remember communications and interactions across all games.")
    print("=" * 60)
    
    # Create and run series
    series = GameSeries(player_configs, series_name)
    series.run_series(num_games=num_games, communication_rounds=args.comm_rounds)

if __name__ == '__main__':
    main()