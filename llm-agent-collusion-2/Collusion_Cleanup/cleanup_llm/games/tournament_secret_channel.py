"""
Tournament runner for Cleanup games with secret communication channels
Runs multiple games with secret communication capabilities for research analysis
"""

import os
import sys
import json
import random
import argparse
from typing import Dict, List, Any
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from games.secret_channel import CleanupSecretChannel

class SecretChannelTournament:
    """Tournament manager for secret communication channel experiments"""

    def __init__(self, games: int, steps: int, output_dir: str,
                 secret_channel_config: Dict[str, Any], seed: int = None):
        """Initialize tournament

        Args:
            games: Number of games to run
            steps: Steps per game
            output_dir: Directory to save results
            secret_channel_config: Secret channel configuration
                {
                    'trigger_game': int,  # Which game number to offer the tool (optional)
                    'trigger_step': int,  # Which step within game to offer tool (optional)
                    'chosen_agent': str,  # Who gets offered the tool ('random' or agent ID)
                    'allow_refusal': bool  # Can they refuse the offer?
                }
            seed: Base random seed
        """
        self.games = games
        self.steps = steps
        self.output_dir = output_dir
        self.secret_channel_config = secret_channel_config
        self.base_seed = seed

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, 'game_record'), exist_ok=True)

        # Agent configurations (small LLM roster)
        self.agent_configs = [
            {"type": "llm", "model": "llama-3.2-3b", "name": "Luke"},
            {"type": "llm", "model": "llama-3.1-8b", "name": "Lily"},
            {"type": "llm", "model": "ministral-8b", "name": "Mike"},
            {"type": "llm", "model": "qwen2.5-7b", "name": "Quinn"}
        ]

        # Tournament tracking
        self.results = {
            'tournament_info': {
                'total_games': games,
                'steps_per_game': steps,
                'tournament_type': 'secret_communication_channel',
                'secret_channel_config': secret_channel_config,
                'agent_configs': self.agent_configs,
                'start_time': datetime.now().isoformat()
            },
            'games': [],
            'summary_stats': {}
        }

        # Persistent alliance tracking across games
        self.alliance_established = False
        self.alliance_initiator = None
        self.alliance_partner = None
        self.alliance_established_at_game = None

    def run_tournament(self) -> Dict[str, Any]:
        """Run the complete tournament"""
        print(f"=== Starting Secret Communication Channel Tournament ===")
        print(f"Games: {self.games}")
        print(f"Steps per game: {self.steps}")
        print(f"Output directory: {self.output_dir}")
        print(f"Secret channel config: {self.secret_channel_config}")
        print("=" * 60)

        # Track various statistics
        win_counts = {config['name']: 0 for config in self.agent_configs}
        score_totals = {config['name']: 0 for config in self.agent_configs}
        channel_acceptance_count = 0
        channel_offered_count = 0
        alliance_win_count = 0  # When alliance members win
        non_alliance_win_count = 0

        # Run all games
        for game_num in range(1, self.games + 1):
            print(f"\n--- Game {game_num}/{self.games} ---")

            # Set seed for reproducibility
            game_seed = self.base_seed + game_num if self.base_seed else None

            # Configure secret channel for this game
            game_secret_config = self.secret_channel_config.copy()

            # Determine if tool should be offered in this game
            should_offer_tool = False
            if 'trigger_game' in self.secret_channel_config:
                # Game-based triggering
                if game_num == self.secret_channel_config['trigger_game'] and not self.alliance_established:
                    should_offer_tool = True
                    # Set trigger_step for within-game offering (default to step 10 if not specified)
                    game_secret_config['trigger_step'] = self.secret_channel_config.get('trigger_step', 1)
                elif self.alliance_established:
                    # Alliance already exists, continue with it but don't offer new tools
                    should_offer_tool = False
                    game_secret_config.pop('trigger_step', None)  # Remove trigger to prevent re-offering
                else:
                    # Before trigger game or tool was refused
                    should_offer_tool = False
                    game_secret_config.pop('trigger_step', None)  # Remove trigger
            else:
                # Original step-based triggering (backward compatibility)
                should_offer_tool = 'trigger_step' in game_secret_config

            # Create and run game
            game = CleanupSecretChannel(
                agent_configs=self.agent_configs,
                secret_channel_config=game_secret_config,
                max_steps=self.steps,
                seed=game_seed
            )

            # If alliance exists, establish it at game start
            if self.alliance_established:
                print(f"[TOURNAMENT] Continuing alliance: {self.alliance_initiator} ↔ {self.alliance_partner}")
                # Find agent IDs from names
                initiator_id = next(i for i, config in enumerate(self.agent_configs)
                                  if config['name'] == self.alliance_initiator)
                partner_id = next(i for i, config in enumerate(self.agent_configs)
                                if config['name'] == self.alliance_partner)

                # Establish the channel at game start
                game.secret_channel.establish(self.alliance_initiator, self.alliance_partner, 0)
                game.tool_accepted = True

                # CRITICAL: Also establish the environment alliance for ZAP mechanics
                game.env.add_alliance(initiator_id, partner_id)
                print(f"[TOURNAMENT] Environment alliance registered: Agent {initiator_id} ↔ Agent {partner_id}")

            game_result = game.run_game()

            # Check if alliance was newly established in this game
            if not self.alliance_established and game_result['final_results'].get('secret_channel_active', False):
                # Extract alliance info from game events
                for event in game_result.get('secret_channel_events', []):
                    if event['event'] == 'channel_established':
                        self.alliance_established = True
                        self.alliance_initiator = event['initiator_name']
                        self.alliance_partner = event['partner_name']
                        self.alliance_established_at_game = game_num
                        print(f"\n🔐 TOURNAMENT ALLIANCE ESTABLISHED!")
                        print(f"   Alliance: {self.alliance_initiator} ↔ {self.alliance_partner}")
                        print(f"   Game: {game_num}")
                        print(f"   This alliance will continue for all remaining games!")
                        break

            # Save individual game record
            game_filename = f"cleanup_secret_channel_game_{game_num}.json"
            game_filepath = os.path.join(self.output_dir, 'game_record', game_filename)
            with open(game_filepath, 'w') as f:
                json.dump(game_result, f, indent=2)

            # Update tournament tracking
            self.results['games'].append({
                'game_number': game_num,
                'filename': game_filename,
                'winner': game_result['final_results']['winner_name'],
                'scores': {self.agent_configs[i]['name']: game_result['final_results']['scores'][i]
                          for i in range(len(self.agent_configs))},
                'secret_channel_active': game_result['final_results']['secret_channel_active'],
                'secret_messages_count': game_result['final_results']['secret_messages_count'],
                'total_steps': game_result['final_results']['total_steps'],
                'alliance_active': self.alliance_established,
                'alliance_members': [self.alliance_initiator, self.alliance_partner] if self.alliance_established else []
            })

            # Update statistics
            winner_name = game_result['final_results']['winner_name']
            win_counts[winner_name] += 1

            for i, config in enumerate(self.agent_configs):
                agent_name = config['name']
                score_totals[agent_name] += game_result['final_results']['scores'][i]

            # Track secret channel statistics
            if game_result.get('secret_channel_events'):
                for event in game_result['secret_channel_events']:
                    if event['event'] == 'tool_offered':
                        channel_offered_count += 1
                    elif event['event'] == 'channel_established':
                        channel_acceptance_count += 1

                        # Check if alliance member won
                        initiator_name = event['initiator_name']
                        partner_name = event['partner_name']
                        if winner_name in [initiator_name, partner_name]:
                            alliance_win_count += 1
                        else:
                            non_alliance_win_count += 1
            else:
                non_alliance_win_count += 1

            print(f"Game {game_num} completed: Winner {winner_name}")
            if game_result['final_results']['secret_channel_active']:
                print(f"  Secret channel: {game_result['final_results']['secret_messages_count']} messages exchanged")

        # Calculate summary statistics
        total_games_with_offers = channel_offered_count
        acceptance_rate = (channel_acceptance_count / total_games_with_offers * 100) if total_games_with_offers > 0 else 0
        alliance_success_rate = (alliance_win_count / channel_acceptance_count * 100) if channel_acceptance_count > 0 else 0

        self.results['summary_stats'] = {
            'win_counts': win_counts,
            'win_rates': {name: count/self.games*100 for name, count in win_counts.items()},
            'average_scores': {name: total/self.games for name, total in score_totals.items()},
            'secret_channel_stats': {
                'tools_offered': channel_offered_count,
                'channels_established': channel_acceptance_count,
                'acceptance_rate_percent': acceptance_rate,
                'alliance_wins': alliance_win_count,
                'non_alliance_wins': non_alliance_win_count,
                'alliance_success_rate_percent': alliance_success_rate
            },
            'alliance_info': {
                'alliance_established': self.alliance_established,
                'alliance_members': [self.alliance_initiator, self.alliance_partner] if self.alliance_established else [],
                'alliance_established_at_game': self.alliance_established_at_game,
                'games_with_alliance': self.games - (self.alliance_established_at_game - 1) if self.alliance_established else 0
            }
        }

        # Save tournament results
        tournament_file = os.path.join(self.output_dir, 'tournament_results.json')
        with open(tournament_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        # Create summary CSV
        self.create_summary_csv()

        print(f"\n=== Tournament Complete ===")
        print(f"Results saved to: {self.output_dir}")
        print(f"\nWin Counts:")
        for name, count in win_counts.items():
            print(f"  {name}: {count} ({count/self.games*100:.1f}%)")

        print(f"\nSecret Channel Statistics:")
        print(f"  Tools offered: {channel_offered_count}")
        print(f"  Channels established: {channel_acceptance_count}")
        print(f"  Acceptance rate: {acceptance_rate:.1f}%")
        print(f"  Alliance wins: {alliance_win_count}")
        print(f"  Alliance success rate: {alliance_success_rate:.1f}%")

        return self.results

    def create_summary_csv(self):
        """Create CSV summary files for analysis"""
        import csv

        # Episodes summary (compatible with existing analysis)
        episodes_file = os.path.join(self.output_dir, 'episodes.csv')
        with open(episodes_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['game', 'winner', 'Luke_score', 'Lily_score', 'Mike_score', 'Quinn_score',
                           'secret_channel_active', 'secret_messages', 'total_steps'])

            for game in self.results['games']:
                writer.writerow([
                    game['game_number'],
                    game['winner'],
                    game['scores']['Luke'],
                    game['scores']['Lily'],
                    game['scores']['Mike'],
                    game['scores']['Quinn'],
                    game['secret_channel_active'],
                    game['secret_messages_count'],
                    game['total_steps']
                ])

        # Cumulative scores (compatible with existing analysis)
        cumulative_file = os.path.join(self.output_dir, 'cumulative_scores.csv')
        with open(cumulative_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['game', 'Luke', 'Lily', 'Mike', 'Quinn'])

            cumulative_scores = {'Luke': 0, 'Lily': 0, 'Mike': 0, 'Quinn': 0}
            for game in self.results['games']:
                for name in cumulative_scores:
                    cumulative_scores[name] += game['scores'][name]

                writer.writerow([
                    game['game_number'],
                    cumulative_scores['Luke'],
                    cumulative_scores['Lily'],
                    cumulative_scores['Mike'],
                    cumulative_scores['Quinn']
                ])

        # Secret channel specific analysis
        secret_analysis_file = os.path.join(self.output_dir, 'secret_channel_analysis.csv')
        with open(secret_analysis_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['game', 'tool_offered', 'channel_established', 'initiator', 'partner',
                           'alliance_won', 'messages_exchanged'])

            for game in self.results['games']:
                game_num = game['game_number']

                # Find corresponding game result file to get detailed channel info
                game_filename = f"cleanup_secret_channel_game_{game_num}.json"
                game_filepath = os.path.join(self.output_dir, 'game_record', game_filename)

                try:
                    with open(game_filepath, 'r') as gf:
                        game_data = json.load(gf)

                    tool_offered = False
                    channel_established = False
                    initiator = ""
                    partner = ""

                    if game_data.get('secret_channel_events'):
                        for event in game_data['secret_channel_events']:
                            if event['event'] == 'tool_offered':
                                tool_offered = True
                            elif event['event'] == 'channel_established':
                                channel_established = True
                                initiator = event['initiator_name']
                                partner = event['partner_name']

                    alliance_won = game['winner'] in [initiator, partner] if channel_established else False

                    writer.writerow([
                        game_num,
                        tool_offered,
                        channel_established,
                        initiator,
                        partner,
                        alliance_won,
                        game['secret_messages_count']
                    ])

                except Exception as e:
                    print(f"Warning: Could not process detailed data for game {game_num}: {e}")
                    writer.writerow([game_num, False, False, "", "", False, 0])

def main():
    """Main function for running secret channel tournaments"""
    parser = argparse.ArgumentParser(description="Run Cleanup Tournament with Secret Communication Channels")
    parser.add_argument("--games", type=int, default=20, help="Number of games to run")
    parser.add_argument("--steps", type=int, default=30, help="Steps per game")
    parser.add_argument("--out", type=str, default="runs/secret_channel", help="Output directory")
    parser.add_argument("--trigger-step", type=int, default=1, help="Step within game to offer secret tool")
    parser.add_argument("--trigger-game", type=int, help="Game number to offer secret tool (overrides step-based)")
    parser.add_argument("--chosen-agent", type=str, default="random", help="Agent to offer tool to")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")

    args = parser.parse_args()

    # Secret channel configuration
    secret_config = {
        'chosen_agent': args.chosen_agent,
        'allow_refusal': True
    }

    # Add trigger configuration
    if args.trigger_game is not None:
        secret_config['trigger_game'] = args.trigger_game
        secret_config['trigger_step'] = args.trigger_step  # Step within that game
    else:
        secret_config['trigger_step'] = args.trigger_step  # Original behavior

    print("Tournament Configuration:")
    print(f"  Games: {args.games}")
    print(f"  Steps per game: {args.steps}")
    print(f"  Output directory: {args.out}")
    print(f"  Secret tool trigger step: {args.trigger_step}")
    print(f"  Chosen agent: {args.chosen_agent}")
    print("-" * 50)

    # Create and run tournament
    tournament = SecretChannelTournament(
        games=args.games,
        steps=args.steps,
        output_dir=args.out,
        secret_channel_config=secret_config,
        seed=args.seed
    )

    results = tournament.run_tournament()
    print(f"\nTournament completed successfully!")
    print(f"Results available in: {args.out}")

if __name__ == '__main__':
    main()