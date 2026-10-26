"""
Create barplot comparison of player statistics across three communication conditions
"""

import matplotlib.pyplot as plt
import numpy as np
import json
import os
from typing import Dict, List, Tuple
from scipy import stats
from datetime import datetime

class GameStatsBarplotCreator:
    """Create comparative barplots for player statistics across communication conditions"""
    
    def __init__(self):
        # Color scheme from comparative_pattern_analyzer.py
        self.base_colors = {
            'Lily': '#e41a1c',     # red
            'Luke': '#984ea3',     # purple  
            'Mike': '#ff7f00',     # orange
            'Quinn': '#4daf4a'     # green
        }
        
        # Model mapping for labels
        self.name_to_model = {
            'Lily': 'llama-3.1-8b',
            'Mike': 'ministral-8b', 
            'Luke': 'llama-3.2-3b',
            'Quinn': 'qwen2.5-7b'
        }
        
        # Available conditions and their default paths
        self.default_paths = {
            'baseline': '../../experiments/game_records/Lily-Luke-Mike-Quinn',
            '1_comm': '../../experiments/game_records/Lily-Luke-Mike-Quinn_communication',
            '3_comm': '../../experiments/game_records/Lily-Luke-Mike-Quinn_communication_3',
            'secret': '../../experiments/game_records/Lily-Luke-Mike-Quinn_secret_comm',
            'secret_hint': '../../experiments/game_records/Lily-Luke-Mike-Quinn_secret_hint'
        }
        
        # Initialize record_dirs (will be populated based on user selection)
        self.record_dirs = {}
        
        # This will store extracted individual game data
        self.individual_data = {}
        
        # This will store behavioral data
        self.behavioral_data = {}
        
        # This will store calculated statistics with errors
        self.data = {}
        
        # This will store calculated behavioral statistics
        self.behavioral_stats = {}
        
        self.players = ['Lily', 'Luke', 'Mike', 'Quinn']
        self.conditions = []  # Will be populated based on user selection
        self.condition_labels = {
            'baseline': 'Baseline',
            '1_comm': '1-comm',
            '3_comm': '3-comm',
            'secret': 'Secret Comm',
            'secret_hint': 'Secret Hint'
        }
    
    def get_bar_color_variations(self, base_color: str, condition: str) -> str:
        """Get color variation for bar chart based on condition"""
        rgb = [int(base_color[i:i+2], 16) for i in (1, 3, 5)]
        
        if condition == 'baseline':
            # Light version - increase brightness by 60%
            light_rgb = [min(255, int(c + (255 - c) * 0.6)) for c in rgb]
            return f"#{light_rgb[0]:02x}{light_rgb[1]:02x}{light_rgb[2]:02x}"
        elif condition == '1_comm':
            # Normal base color
            return base_color
        elif condition == '3_comm':
            # Darker version - decrease brightness by 40%
            dark_rgb = [max(0, int(c * 0.6)) for c in rgb]
            return f"#{dark_rgb[0]:02x}{dark_rgb[1]:02x}{dark_rgb[2]:02x}"
        elif condition == 'secret':
            # For secret communication, use a distinctive variation
            # Apply a distinctive blue-shift to make it clearly different
            # secret_rgb = [
            #     max(0, int(rgb[0] * 0.7)),  # Reduce red
            #     max(0, int(rgb[1] * 0.8)),  # Slightly reduce green
            #     min(255, int(rgb[2] + (255 - rgb[2]) * 0.5))  # Boost blue
            # ]
            # return f"#{secret_rgb[0]:02x}{secret_rgb[1]:02x}{secret_rgb[2]:02x}"
            return base_color
        elif condition == 'secret_hint':
            # For secret hint, use same as base color
            dark_rgb = [max(0, int(c * 0.6)) for c in rgb]
            return f"#{dark_rgb[0]:02x}{dark_rgb[1]:02x}{dark_rgb[2]:02x}"
        else:
            return base_color
    
    def extract_individual_game_data(self, directory_path: str) -> Dict[str, Dict]:
        """Extract individual game data for each player from JSON files"""
        player_data = {player: {'final_scores': [], 'rounds_survived': [], 'wins': 0} 
                      for player in self.players}
        
        try:
            if not os.path.exists(directory_path):
                print(f"Warning: Directory {directory_path} not found")
                return player_data
                
            # Get all JSON files in the directory
            json_files = [f for f in os.listdir(directory_path) if f.endswith('.json')]
            json_files.sort()
            
            for json_file in json_files:
                file_path = os.path.join(directory_path, json_file)
                try:
                    with open(file_path, 'r') as file:
                        game_data = json.load(file)
                    
                    # Extract final scores
                    if 'final_scores' in game_data:
                        final_scores = game_data['final_scores']
                        for player in self.players:
                            if player in final_scores:
                                player_data[player]['final_scores'].append(int(final_scores[player]))
                    
                    # Extract rounds survived from rounds array
                    if 'rounds' in game_data:
                        rounds = game_data['rounds']
                        
                        # Find the last round each player participated in
                        for player in self.players:
                            rounds_survived = 0
                            for round_data in rounds:
                                if 'round_players' in round_data:
                                    if player in round_data['round_players']:
                                        rounds_survived = round_data.get('round_id', rounds_survived)
                            player_data[player]['rounds_survived'].append(rounds_survived)
                    
                    # Extract winner information
                    if 'winner' in game_data:
                        winner = game_data['winner']
                        if winner in self.players:
                            player_data[winner]['wins'] += 1
                                
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    print(f"Warning: Error reading {json_file}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Warning: Error accessing directory {directory_path}: {e}")
            
        return player_data
    
    def extract_behavioral_data_from_directory(self, directory_path: str) -> Dict[str, Dict]:
        """Extract behavioral data (bluff/challenge rates and success rates) from game records"""
        player_data = {player: {
            'bluff_attempts': [],
            'bluff_successes': [],
            'challenge_attempts': [],
            'challenge_successes': [],
            'total_plays': [],
            'total_actions': []
        } for player in self.players}
        
        try:
            if not os.path.exists(directory_path):
                print(f"Warning: Directory {directory_path} not found")
                return player_data
            
            # Get all JSON files in the directory
            json_files = [f for f in os.listdir(directory_path) if f.endswith('.json')]
            json_files.sort()
            
            for json_file in json_files:
                file_path = os.path.join(directory_path, json_file)
                try:
                    with open(file_path, 'r') as file:
                        game_data = json.load(file)
                    
                    # Initialize counters for this game
                    game_stats = {player: {
                        'bluff_attempts': 0,
                        'bluff_successes': 0,
                        'challenge_attempts': 0,
                        'challenge_successes': 0,
                        'total_plays': 0,
                        'total_actions': 0
                    } for player in self.players}
                    
                    # Extract from rounds data
                    if 'rounds' in game_data:
                        for round_data in game_data['rounds']:
                            if 'play_history' in round_data:
                                for play in round_data['play_history']:
                                    player = play.get('player_name')
                                    
                                    if player in self.players:
                                        # Count bluff attempts based on whether played cards match target
                                        played_cards = play.get('played_cards', [])
                                        target_card = round_data.get('target_card', '')
                                        
                                        if played_cards:
                                            # Count this as an action for the player (they chose to play cards)
                                            game_stats[player]['total_actions'] += 1
                                            game_stats[player]['total_plays'] += 1
                                            
                                            # Check if this is a bluff (played cards don't match target)
                                            is_bluff = any(card != target_card and card != 'Joker' for card in played_cards)
                                            
                                            if is_bluff:
                                                game_stats[player]['bluff_attempts'] += 1
                                                # Check if bluff was successful (not challenged or challenge failed)
                                                was_challenged = play.get('was_challenged', False)
                                                if not was_challenged:
                                                    game_stats[player]['bluff_successes'] += 1
                                                else:
                                                    challenge_result = play.get('challenge_result', True)
                                                    if not challenge_result:  # Challenge failed, bluff succeeded
                                                        game_stats[player]['bluff_successes'] += 1
                                        
                                        # Count challenges made by next player against this player
                                        next_player = play.get('next_player')
                                        was_challenged = play.get('was_challenged', False)
                                        if was_challenged and next_player and next_player in self.players:
                                            # The next player chose to challenge instead of playing cards - count as action
                                            game_stats[next_player]['total_actions'] += 1
                                            game_stats[next_player]['challenge_attempts'] += 1
                                            challenge_result = play.get('challenge_result', False)
                                            if challenge_result:  # Challenge was successful
                                                game_stats[next_player]['challenge_successes'] += 1
                    
                    # Store the stats for this game
                    for player in self.players:
                        player_data[player]['bluff_attempts'].append(game_stats[player]['bluff_attempts'])
                        player_data[player]['bluff_successes'].append(game_stats[player]['bluff_successes'])
                        player_data[player]['challenge_attempts'].append(game_stats[player]['challenge_attempts'])
                        player_data[player]['challenge_successes'].append(game_stats[player]['challenge_successes'])
                        player_data[player]['total_plays'].append(game_stats[player]['total_plays'])
                        player_data[player]['total_actions'].append(game_stats[player]['total_actions'])
                        
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    print(f"Warning: Error reading {json_file}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Warning: Error accessing directory {directory_path}: {e}")
            
        return player_data
    
    def select_conditions_and_paths(self):
        """Interactive selection of conditions and their paths"""
        print("\n=== Condition Selection ===")
        print("Available conditions:")
        print("  1. baseline - Baseline condition (no communication)")
        print("  2. 1_comm - Single communication round")
        print("  3. 3_comm - Three communication rounds")
        print("  4. secret - Secret communication channel")
        print("  5. secret_hint - Secret strategic hint system")
        print("\nEnter the numbers of conditions you want to compare (comma-separated):")
        print("Example: 1,5 for baseline and secret hint, or 1,2,3,4,5 for all")
        
        while True:
            selection = input("Your selection: ").strip()
            try:
                # Parse selection
                indices = [int(x.strip()) for x in selection.split(',')]
                condition_map = {1: 'baseline', 2: '1_comm', 3: '3_comm', 4: 'secret', 5: 'secret_hint'}
                
                selected_conditions = []
                for idx in indices:
                    if idx in condition_map:
                        selected_conditions.append(condition_map[idx])
                    else:
                        print(f"Invalid selection: {idx}. Please use numbers 1-5.")
                        continue
                
                if selected_conditions:
                    self.conditions = selected_conditions
                    break
                else:
                    print("No valid conditions selected. Please try again.")
            except ValueError:
                print("Invalid input. Please enter comma-separated numbers (e.g., 1,5)")
        
        # Now ask for paths for each selected condition
        print("\n=== Path Configuration ===")
        for condition in self.conditions:
            default_path = self.default_paths[condition]
            print(f"\nPath for {self.condition_labels[condition]} condition:")
            print(f"  Default: {default_path}")
            print("  Press Enter to use default, or enter a custom path:")
            
            custom_path = input("  Path: ").strip()
            if custom_path:
                self.record_dirs[condition] = custom_path
            else:
                self.record_dirs[condition] = default_path
        
        print("\n✓ Configuration complete!")
        print(f"Selected conditions: {', '.join([self.condition_labels[c] for c in self.conditions])}")
        return self.conditions
    
    def load_all_individual_data(self):
        """Load individual game data from all conditions"""
        print("\nLoading individual game data for error calculation...")
        
        for condition, directory in self.record_dirs.items():
            data = self.extract_individual_game_data(directory)
            self.individual_data[condition] = data
            
            # Print summary
            total_games = len(data['Lily']['final_scores']) if data['Lily']['final_scores'] else 0
            print(f"✓ {self.condition_labels[condition]}: Extracted {total_games} games from {directory}")
    
    def load_all_behavioral_data(self):
        """Load behavioral data from all conditions"""
        print("\nLoading behavioral data for analysis...")
        
        for condition, directory in self.record_dirs.items():
            data = self.extract_behavioral_data_from_directory(directory)
            self.behavioral_data[condition] = data
            
            # Print summary
            total_games = len(data['Lily']['bluff_attempts']) if data['Lily']['bluff_attempts'] else 0
            print(f"✓ {self.condition_labels[condition]}: Extracted behavioral data from {total_games} games")
    
    def calculate_statistics_with_errors(self):
        """Calculate means and standard errors from individual game data"""
        self.data = {}
        
        for condition in self.conditions:
            if condition not in self.individual_data:
                continue
                
            condition_stats = {
                'wins': {},
                'win_percent': {},
                'final_scores': {},
                'final_scores_error': {},
                'rounds_survived': {},
                'rounds_survived_error': {}
            }
            
            condition_data = self.individual_data[condition]
            
            for player in self.players:
                player_data = condition_data[player]
                
                # Win statistics
                wins = player_data['wins']
                total_games = len(player_data['final_scores'])
                win_percent = (wins / total_games * 100) if total_games > 0 else 0
                
                condition_stats['wins'][player] = wins
                condition_stats['win_percent'][player] = win_percent
                
                # Final scores with standard error
                if player_data['final_scores']:
                    scores = np.array(player_data['final_scores'])
                    mean_score = np.mean(scores)
                    std_error = np.std(scores) / np.sqrt(len(scores))
                    
                    condition_stats['final_scores'][player] = mean_score
                    condition_stats['final_scores_error'][player] = std_error
                else:
                    condition_stats['final_scores'][player] = 0
                    condition_stats['final_scores_error'][player] = 0
                
                # Rounds survived with standard error
                if player_data['rounds_survived']:
                    rounds = np.array(player_data['rounds_survived'])
                    mean_rounds = np.mean(rounds)
                    std_error = np.std(rounds) / np.sqrt(len(rounds))
                    
                    condition_stats['rounds_survived'][player] = mean_rounds
                    condition_stats['rounds_survived_error'][player] = std_error
                else:
                    condition_stats['rounds_survived'][player] = 0
                    condition_stats['rounds_survived_error'][player] = 0
            
            self.data[condition] = condition_stats
    
    def calculate_behavioral_statistics_with_errors(self):
        """Calculate behavioral statistics with standard errors"""
        self.behavioral_stats = {}
        
        for condition in self.conditions:
            if condition not in self.behavioral_data:
                continue
                
            condition_stats = {
                'mean_bluff_rate': {},
                'mean_bluff_rate_error': {},
                'mean_challenge_rate': {},
                'mean_challenge_rate_error': {},
                'successful_bluff_rate': {},
                'successful_bluff_rate_error': {},
                'successful_challenge_rate': {},
                'successful_challenge_rate_error': {}
            }
            
            condition_data = self.behavioral_data[condition]
            
            for player in self.players:
                player_data = condition_data[player]
                
                # Calculate bluff rate as percentage (bluffs/total_plays * 100)
                bluff_attempts = np.array(player_data['bluff_attempts'])
                total_plays = np.array(player_data['total_plays'])
                bluff_rates = []
                
                for i in range(len(bluff_attempts)):
                    if total_plays[i] > 0:
                        bluff_rates.append((bluff_attempts[i] / total_plays[i]) * 100)
                    else:
                        bluff_rates.append(0)
                
                if bluff_rates:
                    mean_bluff_rate = np.mean(bluff_rates)
                    std_error = np.std(bluff_rates) / np.sqrt(len(bluff_rates))
                    condition_stats['mean_bluff_rate'][player] = mean_bluff_rate
                    condition_stats['mean_bluff_rate_error'][player] = std_error
                else:
                    condition_stats['mean_bluff_rate'][player] = 0
                    condition_stats['mean_bluff_rate_error'][player] = 0
                
                # Calculate challenge rate as percentage (challenges/total_actions * 100)
                challenge_attempts = np.array(player_data['challenge_attempts'])
                total_actions = np.array(player_data['total_actions'])
                challenge_rates = []
                
                for i in range(len(challenge_attempts)):
                    if total_actions[i] > 0:
                        challenge_rates.append((challenge_attempts[i] / total_actions[i]) * 100)
                    else:
                        challenge_rates.append(0)
                
                if challenge_rates:
                    mean_challenge_rate = np.mean(challenge_rates)
                    std_error = np.std(challenge_rates) / np.sqrt(len(challenge_rates))
                    condition_stats['mean_challenge_rate'][player] = mean_challenge_rate
                    condition_stats['mean_challenge_rate_error'][player] = std_error
                else:
                    condition_stats['mean_challenge_rate'][player] = 0
                    condition_stats['mean_challenge_rate_error'][player] = 0
                
                # Calculate successful bluff rate (success rate when bluffing)
                bluff_successes = np.array(player_data['bluff_successes'])
                total_bluffs = np.sum(bluff_attempts)
                total_successes = np.sum(bluff_successes)
                
                if total_bluffs > 0:
                    successful_bluff_rate = total_successes / total_bluffs
                    # Calculate standard error for proportion
                    std_error = np.sqrt(successful_bluff_rate * (1 - successful_bluff_rate) / total_bluffs)
                    condition_stats['successful_bluff_rate'][player] = successful_bluff_rate
                    condition_stats['successful_bluff_rate_error'][player] = std_error
                else:
                    condition_stats['successful_bluff_rate'][player] = 0
                    condition_stats['successful_bluff_rate_error'][player] = 0
                
                # Calculate successful challenge rate (success rate when challenging)
                challenge_successes = np.array(player_data['challenge_successes'])
                total_challenges = np.sum(challenge_attempts)
                total_challenge_successes = np.sum(challenge_successes)
                
                if total_challenges > 0:
                    successful_challenge_rate = total_challenge_successes / total_challenges
                    # Calculate standard error for proportion
                    std_error = np.sqrt(successful_challenge_rate * (1 - successful_challenge_rate) / total_challenges)
                    condition_stats['successful_challenge_rate'][player] = successful_challenge_rate
                    condition_stats['successful_challenge_rate_error'][player] = std_error
                else:
                    condition_stats['successful_challenge_rate'][player] = 0
                    condition_stats['successful_challenge_rate_error'][player] = 0
            
            self.behavioral_stats[condition] = condition_stats
    
    def proportions_test(self, count1: int, n1: int, count2: int, n2: int) -> Tuple[float, float]:
        """Perform two-proportion z-test"""
        if n1 == 0 or n2 == 0:
            return 0.0, 1.0
        
        p1 = count1 / n1
        p2 = count2 / n2
        
        if p1 == p2:
            return 0.0, 1.0
        
        p_pooled = (count1 + count2) / (n1 + n2)
        se = np.sqrt(p_pooled * (1 - p_pooled) * (1/n1 + 1/n2))
        
        if se == 0:
            return 0.0, 1.0
            
        z = (p1 - p2) / se
        p_value = 2 * (1 - stats.norm.cdf(abs(z)))
        
        return z, p_value
    
    def t_test_independent(self, group1: List[float], group2: List[float]) -> Tuple[float, float]:
        """Perform independent samples t-test"""
        if len(group1) == 0 or len(group2) == 0:
            return 0.0, 1.0
        
        t_stat, p_value = stats.ttest_ind(group1, group2)
        return t_stat, p_value
    
    def run_statistical_tests(self) -> Dict:
        """Run all statistical tests and return results"""
        results = {
            'proportions_tests': {},
            't_tests': {},
            'timestamp': datetime.now().strftime("%Y%m%d_%H%M%S")
        }
        
        total_games = 50  # Based on the expected number of games per condition
        
        # 1. Proportions tests for Mike and Quinn games won across conditions
        mike_stats = {}
        quinn_stats = {}
        
        for condition in self.conditions:
            mike_wins = self.data[condition]['wins']['Mike']
            quinn_wins = self.data[condition]['wins']['Quinn']
            mike_stats[condition] = mike_wins
            quinn_stats[condition] = quinn_wins
        
        # Mike: all pairwise comparisons between selected conditions
        mike_tests = {}
        for i, cond1 in enumerate(self.conditions):
            for j, cond2 in enumerate(self.conditions):
                if i < j:  # Only do each comparison once
                    if cond1 in mike_stats and cond2 in mike_stats:
                        z, p = self.proportions_test(mike_stats[cond1], total_games, mike_stats[cond2], total_games)
                        mike_tests[f"{cond1}_vs_{cond2}"] = {'z': z, 'p': p}
        
        # Quinn: all pairwise comparisons between selected conditions
        quinn_tests = {}
        for i, cond1 in enumerate(self.conditions):
            for j, cond2 in enumerate(self.conditions):
                if i < j:  # Only do each comparison once
                    if cond1 in quinn_stats and cond2 in quinn_stats:
                        z, p = self.proportions_test(quinn_stats[cond1], total_games, quinn_stats[cond2], total_games)
                        quinn_tests[f"{cond1}_vs_{cond2}"] = {'z': z, 'p': p}
        
        results['proportions_tests']['Mike_conditions'] = mike_tests
        results['proportions_tests']['Quinn_conditions'] = quinn_tests
        
        # 2. T-tests for final scores between mistral-7b (Mike) and qwen2.5-7b (Quinn)
        mike_vs_quinn_ttests = {}
        for condition in self.conditions:
            mike_scores = self.individual_data[condition]['Mike']['final_scores']
            quinn_scores = self.individual_data[condition]['Quinn']['final_scores']
            t, p = self.t_test_independent(mike_scores, quinn_scores)
            mike_vs_quinn_ttests[condition] = {'t': t, 'p': p, 
                                             'mike_mean': np.mean(mike_scores) if mike_scores else 0,
                                             'quinn_mean': np.mean(quinn_scores) if quinn_scores else 0}
        
        results['t_tests']['Mike_vs_Quinn_scores'] = mike_vs_quinn_ttests
        
        # 2.1. T-tests for final scores within each model across conditions
        # Mike (mistral-7b) across conditions
        mike_condition_tests = {}
        for i, cond1 in enumerate(self.conditions):
            for j, cond2 in enumerate(self.conditions):
                if i < j:  # Only do each comparison once
                    if cond1 in self.individual_data and cond2 in self.individual_data:
                        scores1 = self.individual_data[cond1]['Mike']['final_scores']
                        scores2 = self.individual_data[cond2]['Mike']['final_scores']
                        t, p = self.t_test_independent(scores1, scores2)
                        mike_condition_tests[f"{cond1}_vs_{cond2}"] = {
                            't': t, 'p': p,
                            f'{cond1}_mean': np.mean(scores1) if scores1 else 0,
                            f'{cond2}_mean': np.mean(scores2) if scores2 else 0
                        }
        
        results['t_tests']['Mike_conditions'] = mike_condition_tests
        
        # Quinn (qwen2.5-7b) across conditions
        quinn_condition_tests = {}
        for i, cond1 in enumerate(self.conditions):
            for j, cond2 in enumerate(self.conditions):
                if i < j:  # Only do each comparison once
                    if cond1 in self.individual_data and cond2 in self.individual_data:
                        scores1 = self.individual_data[cond1]['Quinn']['final_scores']
                        scores2 = self.individual_data[cond2]['Quinn']['final_scores']
                        t, p = self.t_test_independent(scores1, scores2)
                        quinn_condition_tests[f"{cond1}_vs_{cond2}"] = {
                            't': t, 'p': p,
                            f'{cond1}_mean': np.mean(scores1) if scores1 else 0,
                            f'{cond2}_mean': np.mean(scores2) if scores2 else 0
                        }
        
        results['t_tests']['Quinn_conditions'] = quinn_condition_tests
        
        # 3. Tests for other models (Lily: llama-3.1-8b, Luke: llama-3-8b)
        # Games won proportions tests
        lily_tests = {}
        luke_tests = {}
        
        lily_stats = {cond: self.data[cond]['wins']['Lily'] for cond in self.conditions}
        luke_stats = {cond: self.data[cond]['wins']['Luke'] for cond in self.conditions}
        
        for i, cond1 in enumerate(self.conditions):
            for j, cond2 in enumerate(self.conditions):
                if i < j:  # Only do each comparison once
                    if cond1 in lily_stats and cond2 in lily_stats:
                        z, p = self.proportions_test(lily_stats[cond1], total_games, lily_stats[cond2], total_games)
                        lily_tests[f"{cond1}_vs_{cond2}"] = {'z': z, 'p': p}
                    
                    if cond1 in luke_stats and cond2 in luke_stats:
                        z, p = self.proportions_test(luke_stats[cond1], total_games, luke_stats[cond2], total_games)
                        luke_tests[f"{cond1}_vs_{cond2}"] = {'z': z, 'p': p}
        
        results['proportions_tests']['Lily_conditions'] = lily_tests
        results['proportions_tests']['Luke_conditions'] = luke_tests
        
        # Final scores t-tests for other models
        lily_vs_luke_ttests = {}
        for condition in self.conditions:
            lily_scores = self.individual_data[condition]['Lily']['final_scores']
            luke_scores = self.individual_data[condition]['Luke']['final_scores']
            t, p = self.t_test_independent(lily_scores, luke_scores)
            lily_vs_luke_ttests[condition] = {'t': t, 'p': p,
                                            'lily_mean': np.mean(lily_scores) if lily_scores else 0,
                                            'luke_mean': np.mean(luke_scores) if luke_scores else 0}
        
        results['t_tests']['Lily_vs_Luke_scores'] = lily_vs_luke_ttests
        
        # Add Luke's score comparisons across conditions
        luke_condition_tests = {}
        for i, cond1 in enumerate(self.conditions):
            for j, cond2 in enumerate(self.conditions):
                if i < j:  # Only do each comparison once
                    if cond1 in self.individual_data and cond2 in self.individual_data:
                        scores1 = self.individual_data[cond1]['Luke']['final_scores']
                        scores2 = self.individual_data[cond2]['Luke']['final_scores']
                        t, p = self.t_test_independent(scores1, scores2)
                        luke_condition_tests[f"{cond1}_vs_{cond2}"] = {
                            't': t, 'p': p,
                            f'{cond1}_mean': np.mean(scores1) if scores1 else 0,
                            f'{cond2}_mean': np.mean(scores2) if scores2 else 0
                        }
        
        results['t_tests']['Luke_conditions'] = luke_condition_tests
        
        # Add Lily's score comparisons across conditions
        lily_condition_tests = {}
        for i, cond1 in enumerate(self.conditions):
            for j, cond2 in enumerate(self.conditions):
                if i < j:  # Only do each comparison once
                    if cond1 in self.individual_data and cond2 in self.individual_data:
                        scores1 = self.individual_data[cond1]['Lily']['final_scores']
                        scores2 = self.individual_data[cond2]['Lily']['final_scores']
                        t, p = self.t_test_independent(scores1, scores2)
                        lily_condition_tests[f"{cond1}_vs_{cond2}"] = {
                            't': t, 'p': p,
                            f'{cond1}_mean': np.mean(scores1) if scores1 else 0,
                            f'{cond2}_mean': np.mean(scores2) if scores2 else 0
                        }
        
        results['t_tests']['Lily_conditions'] = lily_condition_tests
        
        # 4. Between-model comparisons for selected conditions
        between_model_tests = {}
        for condition in self.conditions:
            condition_tests = {}
            
            # All pairwise comparisons for games won
            for player1, model1 in [('Lily', 'llama-3.1-8b'), ('Mike', 'ministral-8b'), ('Luke', 'llama-3.2-3b'), ('Quinn', 'qwen2.5-7b')]:
                for player2, model2 in [('Lily', 'llama-3.1-8b'), ('Mike', 'ministral-8b'), ('Luke', 'llama-3.2-3b'), ('Quinn', 'qwen2.5-7b')]:
                    if player1 >= player2:  # Avoid duplicate comparisons
                        continue
                    
                    wins1 = self.data[condition]['wins'][player1]
                    wins2 = self.data[condition]['wins'][player2]
                    z, p = self.proportions_test(wins1, total_games, wins2, total_games)
                    
                    condition_tests[f"{player1}_{model1}_vs_{player2}_{model2}_wins"] = {'z': z, 'p': p}
                    
                    # Final scores comparison
                    scores1 = self.individual_data[condition][player1]['final_scores']
                    scores2 = self.individual_data[condition][player2]['final_scores']
                    t, p_score = self.t_test_independent(scores1, scores2)
                    
                    condition_tests[f"{player1}_{model1}_vs_{player2}_{model2}_scores"] = {
                        't': t, 'p': p_score,
                        f'{player1}_mean': np.mean(scores1) if scores1 else 0,
                        f'{player2}_mean': np.mean(scores2) if scores2 else 0
                    }
            
            between_model_tests[condition] = condition_tests
        
        results['between_model_tests'] = between_model_tests
        
        # 5. Behavioral statistics t-tests (within models across conditions)
        behavioral_ttests = {}
        for metric in ['mean_bluff_rate', 'mean_challenge_rate', 'successful_bluff_rate', 'successful_challenge_rate']:
            behavioral_ttests[metric] = {}
            
            for player in self.players:
                player_tests = {}
                for i, cond1 in enumerate(self.conditions):
                    for j, cond2 in enumerate(self.conditions):
                        if i >= j:  # Only do each comparison once
                            continue
                            
                        if cond1 not in self.behavioral_data or cond2 not in self.behavioral_data:
                            continue
                            
                        if metric in ['mean_bluff_rate', 'mean_challenge_rate']:
                            # For rate data, calculate rates per game
                            if metric == 'mean_bluff_rate':
                                bluff_attempts1 = np.array(self.behavioral_data[cond1][player]['bluff_attempts'])
                                total_plays1 = np.array(self.behavioral_data[cond1][player]['total_plays'])
                                data1 = [(b/t)*100 if t > 0 else 0 for b, t in zip(bluff_attempts1, total_plays1)]
                                
                                bluff_attempts2 = np.array(self.behavioral_data[cond2][player]['bluff_attempts'])
                                total_plays2 = np.array(self.behavioral_data[cond2][player]['total_plays'])
                                data2 = [(b/t)*100 if t > 0 else 0 for b, t in zip(bluff_attempts2, total_plays2)]
                            else:
                                challenge_attempts1 = np.array(self.behavioral_data[cond1][player]['challenge_attempts'])
                                total_actions1 = np.array(self.behavioral_data[cond1][player]['total_actions'])
                                data1 = [(c/a)*100 if a > 0 else 0 for c, a in zip(challenge_attempts1, total_actions1)]
                                
                                challenge_attempts2 = np.array(self.behavioral_data[cond2][player]['challenge_attempts'])
                                total_actions2 = np.array(self.behavioral_data[cond2][player]['total_actions'])
                                data2 = [(c/a)*100 if a > 0 else 0 for c, a in zip(challenge_attempts2, total_actions2)]
                        else:
                            # For success rates, compute individual success rates per game
                            if metric == 'successful_bluff_rate':
                                attempts1 = np.array(self.behavioral_data[cond1][player]['bluff_attempts'])
                                successes1 = np.array(self.behavioral_data[cond1][player]['bluff_successes'])
                                attempts2 = np.array(self.behavioral_data[cond2][player]['bluff_attempts'])
                                successes2 = np.array(self.behavioral_data[cond2][player]['bluff_successes'])
                            else:
                                attempts1 = np.array(self.behavioral_data[cond1][player]['challenge_attempts'])
                                successes1 = np.array(self.behavioral_data[cond1][player]['challenge_successes'])
                                attempts2 = np.array(self.behavioral_data[cond2][player]['challenge_attempts'])
                                successes2 = np.array(self.behavioral_data[cond2][player]['challenge_successes'])
                            
                            # Calculate success rate per game (handling divide by zero)
                            data1 = np.divide(successes1, attempts1, out=np.zeros_like(successes1, dtype=float), where=attempts1!=0)
                            data2 = np.divide(successes2, attempts2, out=np.zeros_like(successes2, dtype=float), where=attempts2!=0)
                        
                        if metric in ['mean_bluff_rate', 'mean_challenge_rate']:
                            t, p = self.t_test_independent(data1, data2)
                        else:
                            t, p = self.t_test_independent(data1.tolist(), data2.tolist())
                        player_tests[f"{cond1}_vs_{cond2}"] = {
                            't': t, 'p': p,
                            f'{cond1}_mean': np.mean(data1) if len(data1) > 0 else 0,
                            f'{cond2}_mean': np.mean(data2) if len(data2) > 0 else 0
                        }
                
                behavioral_ttests[metric][player] = player_tests
        
        results['behavioral_ttests'] = behavioral_ttests
        
        return results
    
    def save_statistical_results(self, results: Dict, filename: str = None):
        """Save statistical test results to a text file"""
        if filename is None:
            filename = f"statistical_analysis_{results['timestamp']}.txt"
        
        with open(filename, 'w') as f:
            f.write("="*80 + "\n")
            f.write("STATISTICAL SIGNIFICANCE ANALYSIS - PLAYER PERFORMANCE COMPARISON\n")
            f.write("="*80 + "\n")
            f.write(f"Analysis Date: {results['timestamp']}\n")
            f.write(f"Total Games per Condition: 50\n\n")
            
            # 1. Games Won Proportions Tests
            f.write("1. GAMES WON - PROPORTIONS TESTS BETWEEN CONDITIONS\n")
            f.write("-"*60 + "\n")
            
            for player in ['Mike', 'Quinn', 'Lily', 'Luke']:
                model = self.name_to_model[player]
                f.write(f"\n{player} ({model}):\n")
                
                player_tests = results['proportions_tests'][f'{player}_conditions']
                for comparison, test_result in player_tests.items():
                    cond1, cond2 = comparison.split('_vs_')
                    z = test_result['z']
                    p = test_result['p']
                    significance = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns"
                    
                    wins1 = self.data[cond1]['wins'][player]
                    wins2 = self.data[cond2]['wins'][player]
                    
                    f.write(f"  {self.condition_labels[cond1]} vs {self.condition_labels[cond2]}: ")
                    f.write(f"{wins1} vs {wins2} wins, z={z:.3f}, p={p:.3f} {significance}\n")
            
            # 2. Final Scores T-tests
            f.write("\n\n2. FINAL SCORES - T-TESTS BETWEEN MODELS\n")
            f.write("-"*60 + "\n")
            
            f.write("\nMistral-7b (Mike) vs Qwen2.5-7b (Quinn) - Between Models:\n")
            mike_quinn_tests = results['t_tests']['Mike_vs_Quinn_scores']
            for condition, test_result in mike_quinn_tests.items():
                t = test_result['t']
                p = test_result['p']
                significance = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns"
                
                f.write(f"  {self.condition_labels[condition]}: ")
                f.write(f"Mike_mean={test_result['mike_mean']:.2f}, Quinn_mean={test_result['quinn_mean']:.2f}, ")
                f.write(f"t={t:.3f}, p={p:.3f} {significance}\n")
            
            f.write("\nMistral-7b (Mike) - Across Conditions:\n")
            mike_condition_tests = results['t_tests']['Mike_conditions']
            for comparison, test_result in mike_condition_tests.items():
                cond1, cond2 = comparison.split('_vs_')
                t = test_result['t']
                p = test_result['p']
                significance = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns"
                
                f.write(f"  {self.condition_labels[cond1]} vs {self.condition_labels[cond2]}: ")
                f.write(f"{cond1}_mean={test_result[f'{cond1}_mean']:.2f}, {cond2}_mean={test_result[f'{cond2}_mean']:.2f}, ")
                f.write(f"t={t:.3f}, p={p:.3f} {significance}\n")
            
            f.write("\nQwen2.5-7b (Quinn) - Across Conditions:\n")
            quinn_condition_tests = results['t_tests']['Quinn_conditions']
            for comparison, test_result in quinn_condition_tests.items():
                cond1, cond2 = comparison.split('_vs_')
                t = test_result['t']
                p = test_result['p']
                significance = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns"
                
                f.write(f"  {self.condition_labels[cond1]} vs {self.condition_labels[cond2]}: ")
                f.write(f"{cond1}_mean={test_result[f'{cond1}_mean']:.2f}, {cond2}_mean={test_result[f'{cond2}_mean']:.2f}, ")
                f.write(f"t={t:.3f}, p={p:.3f} {significance}\n")
            
            f.write("\nLlama-3.1-8b (Lily) vs Llama-3-8b (Luke) - Between Models:\n")
            lily_luke_tests = results['t_tests']['Lily_vs_Luke_scores']
            for condition, test_result in lily_luke_tests.items():
                t = test_result['t']
                p = test_result['p']
                significance = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns"
                
                f.write(f"  {self.condition_labels[condition]}: ")
                f.write(f"Lily_mean={test_result['lily_mean']:.2f}, Luke_mean={test_result['luke_mean']:.2f}, ")
                f.write(f"t={t:.3f}, p={p:.3f} {significance}\n")
            
            # 2.1. Behavioral Statistics T-tests
            f.write("\n\n2.1. BEHAVIORAL STATISTICS - T-TESTS ACROSS CONDITIONS\n")
            f.write("-"*60 + "\n")
            
            behavioral_metrics = {
                'mean_bluff_rate': 'Mean Bluff Rate (per game)',
                'mean_challenge_rate': 'Mean Challenge Rate (per game)', 
                'successful_bluff_rate': 'Successful Bluff Rate',
                'successful_challenge_rate': 'Successful Challenge Rate'
            }
            
            for metric, metric_name in behavioral_metrics.items():
                f.write(f"\n{metric_name}:\n")
                for player in self.players:
                    model = self.name_to_model[player]
                    f.write(f"  {player} ({model}):\n")
                    
                    player_tests = results['behavioral_ttests'][metric][player]
                    for comparison, test_result in player_tests.items():
                        cond1, cond2 = comparison.split('_vs_')
                        t = test_result['t']
                        p = test_result['p']
                        significance = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns"
                        
                        f.write(f"    {self.condition_labels[cond1]} vs {self.condition_labels[cond2]}: ")
                        f.write(f"{cond1}_mean={test_result[f'{cond1}_mean']:.3f}, {cond2}_mean={test_result[f'{cond2}_mean']:.3f}, ")
                        f.write(f"t={t:.3f}, p={p:.3f} {significance}\n")
            
            # 3. Between-Model Tests
            f.write("\n\n3. BETWEEN-MODEL COMPARISONS (Baseline and 3-Round Communication)\n")
            f.write("-"*80 + "\n")
            
            for condition in self.conditions:
                f.write(f"\n{self.condition_labels[condition]} Condition:\n")
                f.write("-" * 40 + "\n")
                
                condition_tests = results['between_model_tests'][condition]
                
                # Games won comparisons
                f.write("\nGames Won (Proportions Tests):\n")
                for test_name, test_result in condition_tests.items():
                    if '_wins' in test_name:
                        z = test_result['z']
                        p = test_result['p']
                        significance = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns"
                        
                        comparison = test_name.replace('_wins', '').replace('_', ' ')
                        f.write(f"  {comparison}: z={z:.3f}, p={p:.3f} {significance}\n")
                
                # Final scores comparisons
                f.write("\nFinal Scores (T-tests):\n")
                for test_name, test_result in condition_tests.items():
                    if '_scores' in test_name:
                        t = test_result['t']
                        p = test_result['p']
                        significance = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns"
                        
                        comparison = test_name.replace('_scores', '').replace('_', ' ')
                        
                        # Extract means
                        mean_info = ""
                        for key, value in test_result.items():
                            if '_mean' in key:
                                mean_info += f"{key}={value:.2f}, "
                        
                        f.write(f"  {comparison}: {mean_info}t={t:.3f}, p={p:.3f} {significance}\n")
            
            # 4. Summary of Significant Results
            f.write("\n\n4. SUMMARY OF SIGNIFICANT RESULTS (p < 0.05)\n")
            f.write("-"*60 + "\n")
            
            significant_results = []
            
            # Check proportions tests
            for player in ['Mike', 'Quinn', 'Lily', 'Luke']:
                player_tests = results['proportions_tests'][f'{player}_conditions']
                for comparison, test_result in player_tests.items():
                    if test_result['p'] < 0.05:
                        cond1, cond2 = comparison.split('_vs_')
                        wins1 = self.data[cond1]['wins'][player]
                        wins2 = self.data[cond2]['wins'][player]
                        significant_results.append(
                            f"{player} games won: {self.condition_labels[cond1]} ({wins1}) vs {self.condition_labels[cond2]} ({wins2}), p={test_result['p']:.3f}"
                        )
            
            # Check t-tests
            for model_comparison in ['Mike_vs_Quinn_scores', 'Lily_vs_Luke_scores']:
                tests = results['t_tests'][model_comparison]
                for condition, test_result in tests.items():
                    if test_result['p'] < 0.05:
                        significant_results.append(
                            f"{model_comparison.replace('_', ' ')} in {self.condition_labels[condition]}: p={test_result['p']:.3f}"
                        )
            
            # Check within-model condition comparisons
            for model_tests in ['Mike_conditions', 'Quinn_conditions']:
                model_name = model_tests.split('_')[0]
                tests = results['t_tests'][model_tests]
                for comparison, test_result in tests.items():
                    if test_result['p'] < 0.05:
                        cond1, cond2 = comparison.split('_vs_')
                        significant_results.append(
                            f"{model_name} final scores: {self.condition_labels[cond1]} vs {self.condition_labels[cond2]}, p={test_result['p']:.3f}"
                        )
            
            # Check behavioral t-tests
            for metric, metric_name in behavioral_metrics.items():
                for player in self.players:
                    player_tests = results['behavioral_ttests'][metric][player]
                    for comparison, test_result in player_tests.items():
                        if test_result['p'] < 0.05:
                            cond1, cond2 = comparison.split('_vs_')
                            significant_results.append(
                                f"{player} {metric_name}: {self.condition_labels[cond1]} vs {self.condition_labels[cond2]}, p={test_result['p']:.3f}"
                            )
            
            # Check between-model tests
            for condition in self.conditions:
                condition_tests = results['between_model_tests'][condition]
                for test_name, test_result in condition_tests.items():
                    if test_result['p'] < 0.05:
                        significant_results.append(
                            f"{self.condition_labels[condition]} - {test_name.replace('_', ' ')}: p={test_result['p']:.3f}"
                        )
            
            if significant_results:
                for result in significant_results:
                    f.write(f"• {result}\n")
            else:
                f.write("No statistically significant differences found (p < 0.05)\n")
            
            f.write("\n" + "="*80 + "\n")
            f.write("Notes:\n")
            f.write("*** p < 0.001, ** p < 0.01, * p < 0.05, ns = not significant\n")
            f.write("Proportions tests use two-proportion z-test\n")
            f.write("Score comparisons use independent samples t-test\n")
        
        print(f"Statistical analysis results saved to: {filename}")
        return filename
    
    def add_significance_annotations(self, ax, results: Dict, metric_type: str = 'wins'):
        """Add significance annotations to the plot"""
        if metric_type == 'wins':
            # Get the maximum bar height for each player
            max_heights = []
            for player in self.players:
                player_max = max([self.data[condition]['wins'][player] for condition in self.conditions])
                max_heights.append(player_max)
            
            # Add significance annotations for each player
            for player_idx, player in enumerate(self.players):
                player_tests = results['proportions_tests'][f'{player}_conditions']
                base_height = max_heights[player_idx]
                
                # Check all pairwise comparisons and add annotations
                annotation_level = 0
                for comparison, test_result in player_tests.items():
                    cond1, cond2 = comparison.split('_vs_')
                    p_value = test_result['p']
                    
                    if p_value < 0.05:
                        significance = "***" if p_value < 0.001 else "**" if p_value < 0.01 else "*"
                        
                        # Position bars based on condition - use dynamic positioning like main plot
                        num_conds = len(self.conditions)
                        bar_width_dynamic = 0.8 / num_conds  # Same as main plot

                        # Get condition indices
                        cond_list = list(self.conditions)
                        idx1 = cond_list.index(cond1)
                        idx2 = cond_list.index(cond2)

                        # Calculate x positions using same logic as main plot
                        offset1 = (idx1 - (num_conds - 1) / 2) * bar_width_dynamic
                        offset2 = (idx2 - (num_conds - 1) / 2) * bar_width_dynamic
                        x1 = player_idx + offset1
                        x2 = player_idx + offset2
                        
                        # Calculate y position for annotation (moved higher)
                        y = base_height + 2.5 + (annotation_level * 1.5)
                        
                        # Draw horizontal line
                        ax.plot([x1, x2], [y, y], 'k-', linewidth=1, alpha=0.7)
                        # Draw vertical lines at ends
                        ax.plot([x1, x1], [y-0.1, y+0.1], 'k-', linewidth=1, alpha=0.7)
                        ax.plot([x2, x2], [y-0.1, y+0.1], 'k-', linewidth=1, alpha=0.7)
                        
                        # Add significance text (much bigger and higher)
                        ax.text((x1 + x2) / 2, y + 0.5, significance, 
                               ha='center', va='bottom', fontsize=16, fontweight='bold', color='red')
                        
                        annotation_level += 1
                        
        elif metric_type == 'final_scores':
            # Get the maximum bar height (including error bars) for each player
            max_heights = []
            for player in self.players:
                player_maxes = []
                for condition in self.conditions:
                    score = self.data[condition]['final_scores'][player]
                    error = self.data[condition]['final_scores_error'][player]
                    # Use reduced error (30% like in the plot)
                    reduced_error = error * 0.3
                    player_maxes.append(score + reduced_error)
                max_heights.append(max(player_maxes))
            
            # Add significance annotations for all players (t-tests across conditions)
            for player_idx, player in enumerate(self.players):
                if f'{player}_conditions' not in results['t_tests']:
                    continue
                    
                player_tests = results['t_tests'][f'{player}_conditions']
                base_height = max_heights[self.players.index(player)]
                
                # Check all pairwise comparisons and add annotations
                annotation_level = 0
                for comparison, test_result in player_tests.items():
                    cond1, cond2 = comparison.split('_vs_')
                    p_value = test_result['p']
                    
                    if p_value < 0.05:
                        significance = "***" if p_value < 0.001 else "**" if p_value < 0.01 else "*"
                        
                        # Position bars based on condition - use dynamic positioning like main plot
                        num_conds = len(self.conditions)
                        bar_width_dynamic = 0.8 / num_conds  # Same as main plot
                        player_pos = self.players.index(player)

                        # Get condition indices
                        cond_list = list(self.conditions)
                        idx1 = cond_list.index(cond1)
                        idx2 = cond_list.index(cond2)

                        # Calculate x positions using same logic as main plot
                        offset1 = (idx1 - (num_conds - 1) / 2) * bar_width_dynamic
                        offset2 = (idx2 - (num_conds - 1) / 2) * bar_width_dynamic
                        x1 = player_pos + offset1
                        x2 = player_pos + offset2
                        
                        # Calculate y position for annotation (slightly higher for final scores)
                        y = base_height + 1.8 + (annotation_level * 1.2)
                        
                        # Draw horizontal line
                        ax.plot([x1, x2], [y, y], 'k-', linewidth=1, alpha=0.7)
                        # Draw vertical lines at ends
                        ax.plot([x1, x1], [y-0.1, y+0.1], 'k-', linewidth=1, alpha=0.7)
                        ax.plot([x2, x2], [y-0.1, y+0.1], 'k-', linewidth=1, alpha=0.7)
                        
                        # Add significance text
                        ax.text((x1 + x2) / 2, y + 0.3, significance, 
                               ha='center', va='bottom', fontsize=16, fontweight='bold', color='red')
                        
                        annotation_level += 1
    
    def add_behavioral_significance_annotations(self, ax, results: Dict, player: str, metric: str):
        """Add significance annotations to behavioral barplots"""
        if 'behavioral_ttests' not in results or metric not in results['behavioral_ttests']:
            return
        
        player_tests = results['behavioral_ttests'][metric][player]
        player_idx = self.players.index(player)
        
        # Get maximum bar height for positioning
        max_heights = []
        for condition in self.conditions:
            if metric == 'mean_bluff_rate':
                value = self.behavioral_stats[condition][metric][player]
                error = self.behavioral_stats[condition][f'{metric}_error'][player]
            elif metric == 'mean_challenge_rate':
                value = self.behavioral_stats[condition][metric][player]
                error = self.behavioral_stats[condition][f'{metric}_error'][player]
            elif metric == 'successful_bluff_rate':
                value = self.behavioral_stats[condition][metric][player]
                error = self.behavioral_stats[condition][f'{metric}_error'][player]
            else:  # successful_challenge_rate
                value = self.behavioral_stats[condition][metric][player]
                error = self.behavioral_stats[condition][f'{metric}_error'][player]
            max_heights.append(value + error)
        
        base_height = max(max_heights) if max_heights else 0
        bar_width = 0.25
        
        # Check for significant comparisons and add annotations
        annotation_level = 0
        for comparison, test_result in player_tests.items():
            cond1, cond2 = comparison.split('_vs_')
            p_value = test_result['p']
            
            if p_value < 0.05:
                significance = "***" if p_value < 0.001 else "**" if p_value < 0.01 else "*"
                
                # Position bars dynamically based on condition index
                num_conds = len(self.conditions)
                bar_width = 0.8 / num_conds
                
                # Get condition indices
                cond_list = list(self.conditions) if isinstance(self.conditions, list) else list(self.conditions.keys())
                idx1 = cond_list.index(cond1)
                idx2 = cond_list.index(cond2)
                
                # Calculate x positions
                x1 = player_idx + (idx1 - (num_conds - 1) / 2) * bar_width
                x2 = player_idx + (idx2 - (num_conds - 1) / 2) * bar_width
                
                # Calculate y position for annotation (moved higher to avoid overlap with value labels)
                if metric == 'successful_bluff_rate':
                    # For successful bluff rate with 0-1.0 scale, use larger fixed spacing
                    y = base_height + 0.08 + (annotation_level * 0.06)
                elif metric == 'successful_challenge_rate':
                    # For successful challenge rate, use lower positioning
                    y = base_height + 0.09 + (annotation_level * 0.06)
                elif metric == 'mean_bluff_rate':
                    # For mean bluff rate, use larger fixed spacing to avoid overlap
                    y = base_height + 12 + (annotation_level * 8)
                elif metric == 'mean_challenge_rate':
                    # For mean challenge rate, use proportional spacing with more margin
                    y = base_height + (base_height * 0.25) + (annotation_level * (base_height * 0.2))
                else:
                    # For other metrics, use proportional spacing with more margin
                    y = base_height + (base_height * 0.3) + (annotation_level * (base_height * 0.25))
                
                # Draw horizontal line
                ax.plot([x1, x2], [y, y], 'k-', linewidth=1, alpha=0.7)
                # Draw vertical lines at ends
                ax.plot([x1, x1], [y-0.01*(base_height), y+0.01*(base_height)], 'k-', linewidth=1, alpha=0.7)
                ax.plot([x2, x2], [y-0.01*(base_height), y+0.01*(base_height)], 'k-', linewidth=1, alpha=0.7)
                
                # Add significance text (positioned higher, special handling for successful bluff rate)
                if metric == 'successful_bluff_rate':
                    text_y = y + 0.01  # Fixed offset for 0-0.5 scale
                elif metric == 'mean_bluff_rate':
                    text_y = y + 1  # Fixed offset for mean bluff rate
                else:
                    text_y = y + 0.05*(base_height)  # Proportional offset for other scales
                    
                ax.text((x1 + x2) / 2, text_y, significance, 
                       ha='center', va='bottom', fontsize=14, fontweight='bold', color='red')
                
                annotation_level += 1
    
    def create_comparison_barplot(self, save_path: str = "player_stats_comparison.png"):
        """Create comparative barplot with behavioral statistics added"""
        
        # Load individual data and calculate statistics with errors
        self.load_all_individual_data()
        self.calculate_statistics_with_errors()
        
        # Load behavioral data and calculate behavioral statistics
        self.load_all_behavioral_data()
        self.calculate_behavioral_statistics_with_errors()
        
        # Run statistical tests
        print("Running statistical significance tests...")
        statistical_results = self.run_statistical_tests()
        
        # Save statistical results to file
        stats_filename = self.save_statistical_results(statistical_results)
        
        # Create 2x3 subplot layout: reorganized as requested
        fig, axes = plt.subplots(2, 3, figsize=(36, 28))
        
        # Define subplot positions
        ax_bluff_rate = axes[0, 0]      # Top left: Mean Bluff Rate
        ax_success_bluff = axes[0, 1]   # Top center: Successful Bluff Rate  
        ax_wins = axes[0, 2]            # Top right: Winning Statistics
        ax_challenge_rate = axes[1, 0]  # Bottom left: Mean Challenge Rate
        ax_success_challenge = axes[1, 1] # Bottom center: Successful Challenge Rate
        ax_scores = axes[1, 2]          # Bottom right: Final Score Statistics
        
        x_positions = np.arange(len(self.players))
        num_conditions = len(self.conditions)
        bar_width = 0.8 / num_conditions  # Dynamic width based on number of conditions
        
        # Define colors for legend based on selected conditions
        legend_color_map = {
            'baseline': '#cccccc',  # light grey
            '1_comm': '#888888',    # grey
            '3_comm': '#444444',    # dark grey
            'secret': '#888888',    # distinctive blue for secret
            'secret_hint': '#666666'  # distinct grey for secret hint
        }
        grey_colors = [legend_color_map[condition] for condition in self.conditions]
        
        # === TOP RIGHT: Games Won ===
        for i, condition in enumerate(self.conditions):
            wins = [self.data[condition]['wins'][player] for player in self.players]
            colors = [self.get_bar_color_variations(self.base_colors[player], condition) for player in self.players]
            
            # Calculate offset to center bars dynamically
            offset = (i - (num_conditions - 1) / 2) * bar_width
            bars = ax_wins.bar(x_positions + offset, wins, bar_width,
                          color=colors, alpha=0.8, 
                          label=self.condition_labels[condition])
            
            # Add value labels on bars
            for bar, win_count in zip(bars, wins):
                ax_wins.text(bar.get_x() + bar.get_width()/2, 
                        bar.get_height() + 0.5,
                        f'{win_count}', ha='center', va='bottom', 
                        fontsize=17)
        
        ax_wins.set_ylabel('Number of Games Won', fontsize=36, fontweight='bold')
        ax_wins.set_title('Games Won', fontsize=40, fontweight='bold')
        ax_wins.set_xticks(x_positions)
        ax_wins.set_xticklabels([f"{p}\n({self.name_to_model[p]})" for p in self.players], fontsize=28)
        ax_wins.tick_params(axis='y', labelsize=32)
        
        # Create grey legend
        from matplotlib.patches import Rectangle
        legend_elements = [Rectangle((0,0),1,1, facecolor=grey_colors[i], label=self.condition_labels[condition]) 
                          for i, condition in enumerate(self.conditions)]
        ax_wins.legend(handles=legend_elements, fontsize=28, bbox_to_anchor=(0.02, 0.75), loc='upper left')
        ax_wins.grid(True, alpha=0.3, axis='y')
        # Make subplot outline thicker
        for spine in ax_wins.spines.values():
            spine.set_linewidth(3)
        
        # Add significance annotations
        self.add_significance_annotations(ax_wins, statistical_results, 'wins')
        
        # Adjust y-limit to accommodate significance annotations
        max_wins = max([max(self.data[c]['wins'].values()) for c in self.conditions])
        # Calculate maximum annotation height (up to 3 levels per player, adjusted for new spacing)
        max_annotation_height = max_wins + 2.5 + (3 * 1.5) + 2  # base + start + levels + padding
        ax_wins.set_ylim(0, max_annotation_height)
        
        # === BOTTOM RIGHT: Final Scores ===
        for i, condition in enumerate(self.conditions):
            final_scores = [self.data[condition]['final_scores'][player] for player in self.players]
            final_score_errors = [self.data[condition]['final_scores_error'][player] for player in self.players]
            colors = [self.get_bar_color_variations(self.base_colors[player], condition) for player in self.players]
            
            # Calculate offset to center bars dynamically
            offset = (i - (num_conditions - 1) / 2) * bar_width
            # Create asymmetric error bars to prevent negative values
            reduced_errors = [error * 0.3 for error in final_score_errors]  # Further reduce to 30%
            # Calculate lower and upper error bars separately
            lower_errors = [min(reduced_error, score) for reduced_error, score in zip(reduced_errors, final_scores)]
            upper_errors = reduced_errors
            
            bars = ax_scores.bar(x_positions + offset, final_scores, bar_width,
                          color=colors, alpha=0.8, 
                          yerr=[lower_errors, upper_errors], capsize=2,
                          label=self.condition_labels[condition])
            
            # Add value labels on bars (use upper error for positioning)
            for bar, score, upper_error in zip(bars, final_scores, upper_errors):
                y_pos = bar.get_height() + upper_error + 0.1 if bar.get_height() >= 0 else bar.get_height() - upper_error - 0.3
                ax_scores.text(bar.get_x() + bar.get_width()/2, y_pos,
                        f'{score:.1f}', ha='center', va='bottom' if bar.get_height() >= 0 else 'top', 
                        fontsize=17)
        
        ax_scores.set_ylabel('Average Final Score', fontsize=36, fontweight='bold')
        ax_scores.set_title('Final Scores', fontsize=40, fontweight='bold')
        ax_scores.set_xticks(x_positions)
        ax_scores.set_xticklabels([f"{p}\n({self.name_to_model[p]})" for p in self.players], fontsize=28)
        ax_scores.tick_params(axis='y', labelsize=32)
        
        # Create grey legend
        legend_elements = [Rectangle((0,0),1,1, facecolor=grey_colors[i], label=self.condition_labels[condition]) 
                          for i, condition in enumerate(self.conditions)]
        ax_scores.legend(handles=legend_elements, fontsize=28, bbox_to_anchor=(0.02, 0.45), loc='upper left')
        ax_scores.grid(True, alpha=0.3, axis='y')
        ax_scores.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        # Make subplot outline thicker
        for spine in ax_scores.spines.values():
            spine.set_linewidth(3)
        
        # Add significance annotations for final scores
        self.add_significance_annotations(ax_scores, statistical_results, 'final_scores')
        
        # Adjust y-limits to accommodate annotations for final scores
        max_scores = []
        min_scores = []
        for condition in self.conditions:
            for player in self.players:
                score = self.data[condition]['final_scores'][player]
                error = self.data[condition]['final_scores_error'][player] * 0.3 
                max_scores.append(score + error)
                min_scores.append(score - error)
        
        max_score = max(max_scores) if max_scores else 0
        min_score = min(min_scores + [0]) if min_scores else 0
        
        # Add space for annotations (up to 3 levels for Mike and Quinn)
        max_annotation_height = max_score + 1.0 + (3 * 1.2) + 1
        
        # Set y-limits with proper padding, but don't go too far below zero
        y_min = min(min_score - 0.5, -0.5)  # At most 0.5 below the lowest score or -0.5
        ax_scores.set_ylim(y_min, max_annotation_height)
        
        # === SUBPLOT 3: Average Rounds Survived === (COMMENTED OUT)
        # Note: This subplot has been removed from the 2x3 layout
        """
        # COMMENTED OUT - Rounds Survived Subplot
        for i, condition in enumerate(self.conditions):
            rounds_survived = [self.data[condition]['rounds_survived'][player] for player in self.players]
            rounds_survived_errors = [self.data[condition]['rounds_survived_error'][player] for player in self.players]
            colors = [self.get_bar_color_variations(self.base_colors[player], condition) for player in self.players]
            
            # Calculate offset to center bars dynamically
            offset = (i - (num_conditions - 1) / 2) * bar_width
            # Create asymmetric error bars to prevent negative values
            reduced_rounds_errors = [error * 0.6 for error in rounds_survived_errors]  # Increase to 60% for rounds survived
            # Calculate lower and upper error bars separately
            lower_rounds_errors = [min(reduced_error, rounds) for reduced_error, rounds in zip(reduced_rounds_errors, rounds_survived)]
            upper_rounds_errors = reduced_rounds_errors
            
            bars = ax3.bar(x_positions + offset, rounds_survived, bar_width,
                          color=colors, alpha=0.8, 
                          yerr=[lower_rounds_errors, upper_rounds_errors], capsize=2,
                          label=self.condition_labels[condition])
            
            # Add value labels on bars (use upper error for positioning)
            for bar, rounds, upper_error in zip(bars, rounds_survived, upper_rounds_errors):
                ax3.text(bar.get_x() + bar.get_width()/2, 
                        bar.get_height() + upper_error + 0.2,
                        f'{rounds:.1f}', ha='center', va='bottom', 
                        fontsize=10, fontweight='bold')
        
        ax3.set_ylabel('Average Rounds Survived', fontsize=18, fontweight='bold')
        ax3.set_title('Rounds Survived Statistics', fontsize=20, fontweight='bold')
        ax3.set_xticks(x_positions)
        ax3.set_xticklabels([f"{p}\n({self.name_to_model[p]})" for p in self.players], fontsize=14)
        
        # Create grey legend
        legend_elements = [Rectangle((0,0),1,1, facecolor=grey_colors[i], label=self.condition_labels[condition]) 
                          for i, condition in enumerate(self.conditions)]
        ax3.legend(handles=legend_elements, fontsize=16, loc='lower left')
        ax3.grid(True, alpha=0.3, axis='y')
        ax3.set_ylim(0, max([max(self.data[c]['rounds_survived'].values()) for c in self.conditions]) + 2)
        
        # Hide the unused 4th subplot in top row
        ax4.set_visible(False)
        
        # === BEHAVIORAL STATISTICS SUBPLOTS (Bottom Row) ===
        
        """
        
        # === TOP LEFT: Mean Bluff Rate ===
        for i, condition in enumerate(self.conditions):
            bluff_rates = [self.behavioral_stats[condition]['mean_bluff_rate'][player] for player in self.players]
            bluff_rate_errors = [self.behavioral_stats[condition]['mean_bluff_rate_error'][player] for player in self.players]
            colors = [self.get_bar_color_variations(self.base_colors[player], condition) for player in self.players]
            
            # Calculate offset to center bars dynamically
            offset = (i - (num_conditions - 1) / 2) * bar_width
            bars = ax_bluff_rate.bar(x_positions + offset, bluff_rates, bar_width,
                          color=colors, alpha=0.8, yerr=bluff_rate_errors, capsize=2,
                          label=self.condition_labels[condition])
            
            # Add value labels on bars (positioned higher to avoid error bar overlap)
            for bar, rate, error in zip(bars, bluff_rates, bluff_rate_errors):
                label_y = bar.get_height() + error + 1.5  # Fixed small offset above error bar
                ax_bluff_rate.text(bar.get_x() + bar.get_width()/2, 
                        label_y,
                        f'{rate/100:.2f}', ha='center', va='bottom', 
                        fontsize=13)  # Smaller and not bold
        
        ax_bluff_rate.set_ylabel('Mean Bluff Rate', fontsize=36, fontweight='bold')
        ax_bluff_rate.set_title('Mean Bluff Rate', fontsize=40, fontweight='bold')
        ax_bluff_rate.set_xticks(x_positions)
        ax_bluff_rate.set_xticklabels([f"{p}\n({self.name_to_model[p]})" for p in self.players], fontsize=28)
        ax_bluff_rate.tick_params(axis='y', labelsize=32)
        
        legend_elements = [Rectangle((0,0),1,1, facecolor=grey_colors[i], label=self.condition_labels[condition]) 
                          for i, condition in enumerate(self.conditions)]
        ax_bluff_rate.legend(handles=legend_elements, fontsize=28, loc='lower left')
        ax_bluff_rate.grid(True, alpha=0.3, axis='y')
        # Make subplot outline thicker
        for spine in ax_bluff_rate.spines.values():
            spine.set_linewidth(3)
        
        # Add significance annotations for each player
        for player in self.players:
            self.add_behavioral_significance_annotations(ax_bluff_rate, statistical_results, player, 'mean_bluff_rate')
        
        # Set y-axis to [0, 100] but display as [0, 1]
        ax_bluff_rate.set_ylim(0, 100)
        ax_bluff_rate.set_yticks(np.arange(0, 101, 10))
        ax_bluff_rate.set_yticklabels([f'{i/100:.1f}' for i in range(0, 101, 10)])
        
        # === BOTTOM LEFT: Mean Challenge Rate ===
        for i, condition in enumerate(self.conditions):
            challenge_rates = [self.behavioral_stats[condition]['mean_challenge_rate'][player] for player in self.players]
            challenge_rate_errors = [self.behavioral_stats[condition]['mean_challenge_rate_error'][player] for player in self.players]
            colors = [self.get_bar_color_variations(self.base_colors[player], condition) for player in self.players]
            
            # Calculate offset to center bars dynamically
            offset = (i - (num_conditions - 1) / 2) * bar_width
            bars = ax_challenge_rate.bar(x_positions + offset, challenge_rates, bar_width,
                          color=colors, alpha=0.8, yerr=challenge_rate_errors, capsize=2,
                          label=self.condition_labels[condition])
            
            # Add value labels on bars (positioned higher to avoid error bar overlap)
            for bar, rate, error in zip(bars, challenge_rates, challenge_rate_errors):
                label_y = bar.get_height() + error + (max(challenge_rates) * 0.08)  # Reduced spacing
                ax_challenge_rate.text(bar.get_x() + bar.get_width()/2, 
                        label_y,
                        f'{rate/100:.2f}', ha='center', va='bottom', 
                        fontsize=13)  # Smaller and not bold
        
        ax_challenge_rate.set_ylabel('Mean Challenge Rate', fontsize=36, fontweight='bold')
        ax_challenge_rate.set_title('Mean Challenge Rate', fontsize=40, fontweight='bold')
        ax_challenge_rate.set_xticks(x_positions)
        ax_challenge_rate.set_xticklabels([f"{p}\n({self.name_to_model[p]})" for p in self.players], fontsize=28)
        ax_challenge_rate.tick_params(axis='y', labelsize=32)
        
        legend_elements = [Rectangle((0,0),1,1, facecolor=grey_colors[i], label=self.condition_labels[condition]) 
                          for i, condition in enumerate(self.conditions)]
        ax_challenge_rate.legend(handles=legend_elements, fontsize=28, loc='lower left')
        ax_challenge_rate.grid(True, alpha=0.3, axis='y')
        # Make subplot outline thicker
        for spine in ax_challenge_rate.spines.values():
            spine.set_linewidth(3)
        
        # Add significance annotations for each player
        for player in self.players:
            self.add_behavioral_significance_annotations(ax_challenge_rate, statistical_results, player, 'mean_challenge_rate')
        
        # Set y-axis to [0, 100] but display as [0, 1]
        ax_challenge_rate.set_ylim(0, 100)
        ax_challenge_rate.set_yticks(np.arange(0, 101, 10))
        ax_challenge_rate.set_yticklabels([f'{i/100:.1f}' for i in range(0, 101, 10)])
        
        # === TOP CENTER: Successful Bluff Rate ===
        for i, condition in enumerate(self.conditions):
            success_rates = [self.behavioral_stats[condition]['successful_bluff_rate'][player] for player in self.players]
            success_rate_errors = [self.behavioral_stats[condition]['successful_bluff_rate_error'][player] for player in self.players]
            colors = [self.get_bar_color_variations(self.base_colors[player], condition) for player in self.players]
            
            # Calculate offset to center bars dynamically
            offset = (i - (num_conditions - 1) / 2) * bar_width
            bars = ax_success_bluff.bar(x_positions + offset, success_rates, bar_width,
                          color=colors, alpha=0.8, yerr=success_rate_errors, capsize=2,
                          label=self.condition_labels[condition])
            
            # Add value labels on bars (positioned higher to avoid error bar overlap)
            for bar, rate, error in zip(bars, success_rates, success_rate_errors):
                label_y = bar.get_height() + error + 0.02  # Much closer to bars
                ax_success_bluff.text(bar.get_x() + bar.get_width()/2, 
                        label_y,
                        f'{rate:.2f}', ha='center', va='bottom', 
                        fontsize=13)  # Smaller and not bold
        
        ax_success_bluff.set_ylabel('Successful Bluff Rate', fontsize=36, fontweight='bold')
        ax_success_bluff.set_title('Successful Bluff Rate', fontsize=40, fontweight='bold')
        ax_success_bluff.set_xticks(x_positions)
        ax_success_bluff.set_xticklabels([f"{p}\n({self.name_to_model[p]})" for p in self.players], fontsize=28)
        ax_success_bluff.tick_params(axis='y', labelsize=32)
        # Add significance annotations for each player
        for player in self.players:
            self.add_behavioral_significance_annotations(ax_success_bluff, statistical_results, player, 'successful_bluff_rate')
        
        ax_success_bluff.set_ylim(0, 1.0)  # Set full range to 1.0
        ax_success_bluff.set_yticks(np.arange(0, 1.1, 0.1))  # Set ticks from 0 to 1.0
        
        legend_elements = [Rectangle((0,0),1,1, facecolor=grey_colors[i], label=self.condition_labels[condition]) 
                          for i, condition in enumerate(self.conditions)]
        ax_success_bluff.legend(handles=legend_elements, fontsize=28, loc='center left')
        ax_success_bluff.grid(True, alpha=0.3, axis='y')
        # Make subplot outline thicker
        for spine in ax_success_bluff.spines.values():
            spine.set_linewidth(3)
        
        # === BOTTOM CENTER: Successful Challenge Rate ===
        for i, condition in enumerate(self.conditions):
            success_rates = [self.behavioral_stats[condition]['successful_challenge_rate'][player] for player in self.players]
            success_rate_errors = [self.behavioral_stats[condition]['successful_challenge_rate_error'][player] for player in self.players]
            colors = [self.get_bar_color_variations(self.base_colors[player], condition) for player in self.players]
            
            # Calculate offset to center bars dynamically
            offset = (i - (num_conditions - 1) / 2) * bar_width
            bars = ax_success_challenge.bar(x_positions + offset, success_rates, bar_width,
                          color=colors, alpha=0.8, yerr=success_rate_errors, capsize=2,
                          label=self.condition_labels[condition])
            
            # Add value labels on bars (positioned higher to avoid error bar overlap)
            for bar, rate, error in zip(bars, success_rates, success_rate_errors):
                label_y = bar.get_height() + error + 0.05  # Reduced spacing
                ax_success_challenge.text(bar.get_x() + bar.get_width()/2, 
                        label_y,
                        f'{rate:.2f}', ha='center', va='bottom', 
                        fontsize=13)  # Smaller and not bold
        
        ax_success_challenge.set_ylabel('Successful Challenge Rate', fontsize=36, fontweight='bold')
        ax_success_challenge.set_title('Successful Challenge Rate', fontsize=40, fontweight='bold')
        ax_success_challenge.set_xticks(x_positions)
        ax_success_challenge.set_xticklabels([f"{p}\n({self.name_to_model[p]})" for p in self.players], fontsize=28)
        ax_success_challenge.tick_params(axis='y', labelsize=32)
        # Add significance annotations for each player
        for player in self.players:
            self.add_behavioral_significance_annotations(ax_success_challenge, statistical_results, player, 'successful_challenge_rate')
        
        ax_success_challenge.set_ylim(0, 1.0)  # Set limit to 1.0
        ax_success_challenge.set_yticks(np.arange(0, 1.1, 0.2))  # Set y-ticks from 0 to 1.0
        
        legend_elements = [Rectangle((0,0),1,1, facecolor=grey_colors[i], label=self.condition_labels[condition]) 
                          for i, condition in enumerate(self.conditions)]
        ax_success_challenge.legend(handles=legend_elements, fontsize=28, loc='lower left')
        ax_success_challenge.grid(True, alpha=0.3, axis='y')
        # Make subplot outline thicker
        for spine in ax_success_challenge.spines.values():
            spine.set_linewidth(3)
        
        plt.tight_layout(pad=1.5)
        plt.subplots_adjust(top=0.92, bottom=0.10, left=0.06, right=0.98, hspace=0.20, wspace=0.15)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        print(f"Barplot comparison saved as {save_path}")
        print(f"Statistical analysis results saved as {stats_filename}")
        
        # Print summary statistics
        self.print_summary_statistics()
        
        return statistical_results, stats_filename
    
    def print_summary_statistics(self):
        """Print summary statistics for each condition"""
        print("\n" + "="*80)
        print("PLAYER PERFORMANCE SUMMARY ACROSS CONDITIONS")
        print("="*80)
        
        for condition in self.conditions:
            print(f"\n{self.condition_labels[condition].replace(chr(10), ' ')}:")
            print("-" * 60)
            
            total_wins = sum(self.data[condition]['wins'].values())
            avg_final_score = np.mean(list(self.data[condition]['final_scores'].values()))
            avg_rounds_survived = np.mean(list(self.data[condition]['rounds_survived'].values()))
            
            print(f"Total Games Won: {total_wins}/50")
            print(f"Average Final Score: {avg_final_score:.2f}")
            print(f"Average Rounds Survived: {avg_rounds_survived:.2f}")
            
            print("\nPlayer-wise breakdown:")
            for player in self.players:
                wins = self.data[condition]['wins'][player]
                win_pct = self.data[condition]['win_percent'][player]
                final_score = self.data[condition]['final_scores'][player]
                rounds = self.data[condition]['rounds_survived'][player]
                
                print(f"  {player:6s}: {wins:2d} wins ({win_pct:5.1f}%), "
                      f"Avg Score: {final_score:5.1f}, Avg Rounds: {rounds:5.1f}")

def main():
    """Main function to create barplot comparison"""
    print("=== Creating Player Statistics Barplot Comparison ===")
    
    creator = GameStatsBarplotCreator()
    
    # Interactive condition selection
    selected_conditions = creator.select_conditions_and_paths()
    
    # Create the comparison barplot
    creator.create_comparison_barplot()
    
    print("\n" + "="*50)
    print("Barplot comparison complete!")
    print("📁 Generated: player_stats_comparison.png")

if __name__ == "__main__":
    main()