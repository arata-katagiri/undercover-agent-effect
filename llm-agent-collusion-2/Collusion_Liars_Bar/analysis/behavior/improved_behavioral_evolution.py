"""
Improved Behavioral Evolution Plots using the same style as score progression
Creates separate subplots for each player with smoothed lines and error bars
"""

import os
import sys
import json
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d
from typing import Dict, List
# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from analysis.patterns.pattern_extractor import HistoricalPatternExtractor

class ImprovedBehavioralEvolution:
    """Create beautiful behavioral evolution plots with smoothing and error bars"""
    
    def __init__(self):
        # Same color scheme as score progression
        self.base_colors = {
            'Lily': '#e41a1c',     # red
            'Luke': '#984ea3',     # purple  
            'Mike': '#ff7f00',     # orange
            'Quinn': '#4daf4a'     # green
        }
        
        # Different line styles and markers for each player
        self.line_styles = {
            'Lily': {'marker': 'o', 'linestyle': '-', 'markersize': 17},     # circles
            'Luke': {'marker': '^', 'linestyle': '--', 'markersize': 25},    # triangles
            'Mike': {'marker': 's', 'linestyle': '-.', 'markersize': 17},    # squares
            'Quinn': {'marker': '*', 'linestyle': ':', 'markersize': 25}     # stars
        }

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
        
        # Initialize conditions and labels (will be populated based on user selection)
        self.conditions = {}
        self.condition_labels = {
            'baseline': 'Baseline',
            '1_comm': 'Fair-Comm',
            '3_comm': '3-Comm',
            'secret': 'Secret Comm',
            'secret_hint': 'Secret Hint'
        }
        
        # Colors for legend (grey tones plus distinctive colors for secret conditions)
        self.legend_colors = {
            'baseline': '#cccccc',  # light grey
            '1_comm': '#888888',    # grey
            '3_comm': '#444444',    # dark grey
            'secret': '#1f77b4',    # distinctive blue for secret comm
            'secret_hint': '#2ca02c'  # distinctive green for secret hint
        }
        
        self.players = ['Lily', 'Luke', 'Mike', 'Quinn']
        self.behavioral_data = {}  # Will store extracted behavioral data
        self.scores_data = {}  # Will store score progression data
    
    def get_bar_color_variations(self, base_color: str, condition: str) -> str:
        """Get color variation for different conditions (same as final score evolution)"""
        rgb = [int(base_color[i:i+2], 16) for i in (1, 3, 5)]

        if condition == 'baseline':
            # Use normal base color (same as other conditions)
            return base_color
        elif condition == '1_comm':
            # Normal base color
            return base_color
        elif condition == '3_comm':
            # Darker version - decrease brightness by 40%
            dark_rgb = [max(0, int(c * 0.6)) for c in rgb]
            return f"#{dark_rgb[0]:02x}{dark_rgb[1]:02x}{dark_rgb[2]:02x}"
        elif condition == 'secret':
            # For secret communication, use original base color (no blue-shift)
            return base_color
        elif condition == 'secret_hint':
            # For secret hint, use a green-shifted version
            green_rgb = [
                max(0, int(rgb[0] * 0.7)),  # Reduce red
                min(255, int(rgb[1] + (255 - rgb[1]) * 0.3)),  # Boost green
                max(0, int(rgb[2] * 0.8))   # Slightly reduce blue
            ]
            return f"#{green_rgb[0]:02x}{green_rgb[1]:02x}{green_rgb[2]:02x}"
        else:
            return base_color
    
    def get_alpha_for_condition(self, condition: str) -> float:
        """Get alpha transparency for different conditions"""
        alphas = {'baseline': 0.6, '1_comm': 0.7, '3_comm': 0.8, 'secret': 0.85, 'secret_hint': 0.9}
        return alphas.get(condition, 0.7)
    
    def smooth_data(self, x, y, window_size=5, sigma=1.5):
        """Apply smoothing to data using Gaussian filter"""
        if len(y) < window_size:
            return x, y, np.zeros_like(y)

        # Apply Gaussian smoothing
        y_smooth = gaussian_filter1d(y, sigma=sigma)

        # Calculate rolling standard deviation for shaded area
        y_stds = []
        half_window = window_size // 2

        for i in range(len(y)):
            start_idx = max(0, i - half_window)
            end_idx = min(len(y), i + half_window + 1)
            window_data = y[start_idx:end_idx]

            if len(window_data) > 1:
                std = np.std(window_data)
            else:
                std = 0
            y_stds.append(std)

        return x, y_smooth, np.array(y_stds)
    
    def extract_behavioral_data_from_directory(self, directory_path: str) -> Dict[str, Dict]:
        """Extract bluff and challenge rates for each player from game records"""
        player_data = {player: {'bluff_rates': [], 'challenge_rates': []} for player in self.players}
        
        try:
            if not os.path.exists(directory_path):
                print(f"Warning: Directory {directory_path} not found")
                return player_data
            
            # Use the pattern extractor to get behavioral data
            print(f"Processing {directory_path}...")
            extractor = HistoricalPatternExtractor(data_directory=directory_path)
            num_files = extractor.load_game_records()
            
            if num_files == 0:
                print(f"No files loaded from {directory_path}")
                return player_data
            
            # Extract patterns to get temporal trends
            patterns = extractor.extract_all_patterns()
            
            # Extract temporal trends for each player
            for player_name in self.players:
                if player_name in patterns:
                    player_patterns = patterns[player_name]
                    temporal_trends = player_patterns.temporal_trends
                    
                    if temporal_trends['bluff_trend'] and temporal_trends['challenge_trend']:
                        player_data[player_name]['bluff_rates'] = temporal_trends['bluff_trend']
                        player_data[player_name]['challenge_rates'] = temporal_trends['challenge_trend']
            
            print(f"✓ Extracted behavioral data for {directory_path}")
            
        except Exception as e:
            print(f"Warning: Error processing {directory_path}: {e}")
            
        return player_data
    
    def extract_scores_from_directory(self, directory_path: str) -> Dict[str, List[int]]:
        """Extract individual game scores for each player from game record JSON files"""
        player_scores = {player: [] for player in self.players}
        
        try:
            if not os.path.exists(directory_path):
                print(f"Warning: Directory {directory_path} not found")
                return player_scores
                
            # Get all JSON files in the directory
            json_files = [f for f in os.listdir(directory_path) if f.endswith('.json')]
            json_files.sort()  # Sort for consistent ordering
            
            for json_file in json_files:
                file_path = os.path.join(directory_path, json_file)
                try:
                    with open(file_path, 'r') as file:
                        game_data = json.load(file)
                        
                    # Extract final_scores from the JSON
                    if 'final_scores' in game_data:
                        final_scores = game_data['final_scores']
                        for player in self.players:
                            if player in final_scores:
                                player_scores[player].append(int(final_scores[player]))
                                
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    print(f"Warning: Error reading {json_file}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Warning: Error accessing directory {directory_path}: {e}")
            
        return player_scores

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
                    break
                else:
                    print("No valid conditions selected. Please try again.")
            except ValueError:
                print("Invalid input. Please enter comma-separated numbers (e.g., 1,5)")
        
        # Now ask for paths for each selected condition
        print("\n=== Path Configuration ===")
        for condition in selected_conditions:
            default_path = self.default_paths[condition]
            print(f"\nPath for {self.condition_labels[condition]} condition:")
            print(f"  Default: {default_path}")
            print("  Press Enter to use default, or enter a custom path:")
            
            custom_path = input("  Path: ").strip()
            if custom_path:
                self.conditions[condition] = custom_path
            else:
                self.conditions[condition] = default_path
        
        print("\n✓ Configuration complete!")
        print(f"Selected conditions: {', '.join([self.condition_labels[c] for c in selected_conditions])}")
        return selected_conditions
    
    def load_all_behavioral_data(self):
        """Load behavioral data from all conditions"""
        print("\nLoading behavioral evolution data...")
        
        for condition, directory in self.conditions.items():
            data = self.extract_behavioral_data_from_directory(directory)
            self.behavioral_data[condition] = data
            
            # Print summary
            players_with_data = sum(1 for player in self.players 
                                  if data[player]['bluff_rates'])
            print(f"✓ {self.condition_labels[condition]}: {players_with_data} players with data")
    
    def load_all_scores(self):
        """Load scores from all game record directories"""
        print("\nLoading individual game scores from JSON files...")
        
        for condition, directory in self.conditions.items():
            scores = self.extract_scores_from_directory(directory)
            self.scores_data[condition] = scores
            
            # Print summary
            total_games = len(scores['Lily']) if 'Lily' in scores else 0
            print(f"✓ {self.condition_labels[condition]}: Extracted {total_games} score records from {directory}")
    
    def create_single_bluff_evolution_plot(self, save_path: str = "single_bluff_evolution.png"):
        """Create single plot showing bluff rate evolution for all players"""

        if not self.behavioral_data:
            print("No data loaded. Please run load_all_behavioral_data() first.")
            return

        # Determine subplot layout based on number of conditions
        num_conditions = len(self.conditions)

        if num_conditions == 1:
            fig, ax = plt.subplots(1, 1, figsize=(15, 10))
            axes = [ax]
        else:
            fig, axes = plt.subplots(1, num_conditions, figsize=(15 * num_conditions, 10))
            if num_conditions == 2:
                axes = [axes[0], axes[1]]

        # Create plots for each condition
        for idx, (condition, condition_data) in enumerate(self.behavioral_data.items()):
            ax = axes[idx] if num_conditions > 1 else axes[0]

            # Plot each player on the same subplot
            for player in self.players:
                bluff_rates = condition_data[player]['bluff_rates']
                if bluff_rates and len(bluff_rates) > 2:
                    # Use player's base color (no condition variation since we're separating by subplot)
                    color = self.base_colors[player]

                    # Create game numbers
                    games = np.array(range(1, len(bluff_rates) + 1))
                    rates_array = np.array(bluff_rates)

                    # Apply smoothing and calculate standard deviations
                    games_smooth, rates_smooth, stds = self.smooth_data(
                        games, rates_array, window_size=8, sigma=1.8
                    )

                    # Plot shaded area for standard deviation
                    ax.fill_between(games_smooth,
                                   rates_smooth - stds * 0.45,
                                   rates_smooth + stds * 0.45,
                                   color=color, alpha=0.2, zorder=1)

                    # Plot smoothed line with distinctive markers and line styles
                    style = self.line_styles[player]
                    ax.plot(games_smooth, rates_smooth,
                           color=color, alpha=0.8, linewidth=4,
                           marker=style['marker'], linestyle=style['linestyle'],
                           markersize=style['markersize'], markeredgewidth=1.5,
                           markeredgecolor='white', markerfacecolor=color,
                           markevery=5, zorder=2,
                           label=f'{player} ({self.name_to_model[player]})')

            # Customize subplot
            ax.set_title(f'Liars Bar {self.condition_labels[condition]}',
                        fontsize=48, fontweight='bold')
            ax.set_xlabel('Game Number', fontsize=54, fontweight='bold')
            if idx == 0 or num_conditions == 1:
                ax.set_ylabel('Bluff Rate', fontsize=54, fontweight='bold')
            ax.set_ylim(-0.05, 1.05)
            ax.grid(True, alpha=0.3)
            ax.tick_params(axis='both', which='major', labelsize=48)

            # Legend
            ax.legend(fontsize=36, loc='best')

            # Add statistics panel
            stats_text = []
            for player in self.players:
                bluff_rates = condition_data[player]['bluff_rates']
                if bluff_rates:
                    mean_rate = np.mean(bluff_rates)
                    std_rate = np.std(bluff_rates)
                    stats_text.append(f'{player}: {mean_rate:.2f}±{std_rate:.2f}')

            stats_str = '\n'.join(stats_text)
            ax.text(0.03, 0.96, f'Mean ± Std:\n{stats_str}',
                   transform=ax.transAxes, fontsize=32,
                   verticalalignment='top', horizontalalignment='left',
                   bbox=dict(boxstyle='round,pad=0.6', facecolor='white', alpha=0.85))

        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        print(f"Single bluff evolution plot saved as {save_path}")
    
    def create_single_challenge_evolution_plot(self, save_path: str = "single_challenge_evolution.png"):
        """Create single plot showing challenge rate evolution for all players"""

        if not self.behavioral_data:
            print("No data loaded. Please run load_all_behavioral_data() first.")
            return

        # Determine subplot layout based on number of conditions
        num_conditions = len(self.conditions)

        if num_conditions == 1:
            fig, ax = plt.subplots(1, 1, figsize=(15, 10))
            axes = [ax]
        else:
            fig, axes = plt.subplots(1, num_conditions, figsize=(15 * num_conditions, 10))
            if num_conditions == 2:
                axes = [axes[0], axes[1]]

        # Create plots for each condition
        for idx, (condition, condition_data) in enumerate(self.behavioral_data.items()):
            ax = axes[idx] if num_conditions > 1 else axes[0]

            # Plot each player on the same subplot
            for player in self.players:
                challenge_rates = condition_data[player]['challenge_rates']
                if challenge_rates and len(challenge_rates) > 2:
                    # Use player's base color (no condition variation since we're separating by subplot)
                    color = self.base_colors[player]

                    # Create game numbers
                    games = np.array(range(1, len(challenge_rates) + 1))
                    rates_array = np.array(challenge_rates)

                    # Apply smoothing and calculate standard deviations
                    games_smooth, rates_smooth, stds = self.smooth_data(
                        games, rates_array, window_size=8, sigma=1.8
                    )

                    # Plot shaded area for standard deviation
                    ax.fill_between(games_smooth,
                                   rates_smooth - stds * 0.3,
                                   rates_smooth + stds * 0.3,
                                   color=color, alpha=0.2, zorder=1)

                    # Plot smoothed line with distinctive markers and line styles
                    style = self.line_styles[player]
                    ax.plot(games_smooth, rates_smooth,
                           color=color, alpha=0.8, linewidth=4,
                           marker=style['marker'], linestyle=style['linestyle'],
                           markersize=style['markersize'], markeredgewidth=1.5,
                           markeredgecolor='white', markerfacecolor=color,
                           markevery=5, zorder=2,
                           label=f'{player} ({self.name_to_model[player]})')

            # Customize subplot
            ax.set_title(f'Liars Bar {self.condition_labels[condition]}',
                        fontsize=48, fontweight='bold')
            ax.set_xlabel('Game Number', fontsize=54, fontweight='bold')
            if idx == 0 or num_conditions == 1:
                ax.set_ylabel('Challenge Rate', fontsize=54, fontweight='bold')
            ax.set_ylim(-0.05, 1.05)
            ax.grid(True, alpha=0.3)
            ax.tick_params(axis='both', which='major', labelsize=48)

            # Legend
            ax.legend(fontsize=36, loc='best')

            # Add statistics panel
            stats_text = []
            for player in self.players:
                challenge_rates = condition_data[player]['challenge_rates']
                if challenge_rates:
                    mean_rate = np.mean(challenge_rates)
                    std_rate = np.std(challenge_rates)
                    stats_text.append(f'{player}: {mean_rate:.2f}±{std_rate:.2f}')

            stats_str = '\n'.join(stats_text)
            ax.text(0.03, 0.96, f'Mean ± Std:\n{stats_str}',
                   transform=ax.transAxes, fontsize=32,
                   verticalalignment='top', horizontalalignment='left',
                   bbox=dict(boxstyle='round,pad=0.6', facecolor='white', alpha=0.85))

        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        print(f"Single challenge evolution plot saved as {save_path}")

    def create_combined_bluff_challenge_plot(self, save_path: str = "combined_bluff_challenge_evolution.png"):
        """Create single plot with 2 equal subplots: bluff rates and challenge rates"""

        if not self.behavioral_data:
            print("No data loaded. Please run load_all_behavioral_data() first.")
            return

        # Create 1x2 subplot layout with equal width and height
        fig, (ax_bluff, ax_challenge) = plt.subplots(1, 2, figsize=(30, 15))

        # For now, use the first condition (or combine all conditions if multiple)
        # If multiple conditions, we'll show the first one or could average them
        condition_key = list(self.conditions.keys())[0]
        condition_data = self.behavioral_data[condition_key]
        condition_label = self.condition_labels[condition_key]

        # Plot bluff rates (left subplot)
        for player in self.players:
            bluff_rates = condition_data[player]['bluff_rates']
            if bluff_rates and len(bluff_rates) > 2:
                color = self.base_colors[player]

                games = np.array(range(1, len(bluff_rates) + 1))
                rates_array = np.array(bluff_rates)
                games_smooth, rates_smooth, stds = self.smooth_data(
                    games, rates_array, window_size=8, sigma=1.8
                )

                # Plot shaded area for standard deviation
                ax_bluff.fill_between(games_smooth,
                                    rates_smooth - stds * 0.3,
                                    rates_smooth + stds * 0.3,
                                    color=color, alpha=0.2, zorder=1)

                # Plot smoothed line with distinctive markers and line styles
                style = self.line_styles[player]
                ax_bluff.plot(games_smooth, rates_smooth,
                            color=color, alpha=0.8, linewidth=4,
                            marker=style['marker'], linestyle=style['linestyle'],
                            markersize=style['markersize'], markeredgewidth=1.5,
                            markeredgecolor='white', markerfacecolor=color,
                            markevery=5, zorder=2,
                            label=f'{player} ({self.name_to_model[player]})')

        # Plot challenge rates (right subplot)
        for player in self.players:
            challenge_rates = condition_data[player]['challenge_rates']
            if challenge_rates and len(challenge_rates) > 2:
                color = self.base_colors[player]

                games = np.array(range(1, len(challenge_rates) + 1))
                rates_array = np.array(challenge_rates)
                games_smooth, rates_smooth, stds = self.smooth_data(
                    games, rates_array, window_size=8, sigma=1.8
                )

                # Plot shaded area for standard deviation
                ax_challenge.fill_between(games_smooth,
                                        rates_smooth - stds * 0.3,
                                        rates_smooth + stds * 0.3,
                                        color=color, alpha=0.2, zorder=1)

                # Plot smoothed line with distinctive markers and line styles
                style = self.line_styles[player]
                ax_challenge.plot(games_smooth, rates_smooth,
                                color=color, alpha=0.8, linewidth=4,
                                marker=style['marker'], linestyle=style['linestyle'],
                                markersize=style['markersize'], markeredgewidth=1.5,
                                markeredgecolor='white', markerfacecolor=color,
                                markevery=5, zorder=2,
                                label=f'{player} ({self.name_to_model[player]})')

        # Determine max game number for x-axis limits
        max_games = 0
        for player in self.players:
            bluff_rates = condition_data[player]['bluff_rates']
            if bluff_rates:
                max_games = max(max_games, len(bluff_rates))

        # Customize bluff subplot
        ax_bluff.set_title(f'Liars Bar {condition_label}',
                          fontsize=48, fontweight='bold')
        ax_bluff.set_xlabel('Game Number', fontsize=54, fontweight='bold')
        ax_bluff.set_ylabel('Bluff Rate', fontsize=54, fontweight='bold')
        ax_bluff.set_ylim(-0.05, 1.05)
        ax_bluff.set_xlim(1, max_games)
        ax_bluff.grid(True, alpha=0.3)
        ax_bluff.tick_params(axis='both', which='major', labelsize=48)
        ax_bluff.legend(fontsize=36, loc='best')

        # Add statistics panel for bluff rates
        bluff_stats_text = []
        for player in self.players:
            bluff_rates = condition_data[player]['bluff_rates']
            if bluff_rates:
                mean_rate = np.mean(bluff_rates)
                std_rate = np.std(bluff_rates)
                bluff_stats_text.append(f'{player}: {mean_rate:.2f}±{std_rate:.2f}')

        bluff_stats_str = '\n'.join(bluff_stats_text)
        ax_bluff.text(0.03, 0.96, f'Mean ± Std:\n{bluff_stats_str}',
                     transform=ax_bluff.transAxes, fontsize=32,
                     verticalalignment='top', horizontalalignment='left',
                     bbox=dict(boxstyle='round,pad=0.6', facecolor='white', alpha=0.85))

        # Customize challenge subplot
        ax_challenge.set_title(f'Liars Bar {condition_label}',
                             fontsize=48, fontweight='bold')
        ax_challenge.set_xlabel('Game Number', fontsize=54, fontweight='bold')
        ax_challenge.set_ylabel('Challenge Rate', fontsize=54, fontweight='bold')
        ax_challenge.set_ylim(-0.05, 1.05)
        ax_challenge.set_xlim(1, max_games)
        ax_challenge.grid(True, alpha=0.3)
        ax_challenge.tick_params(axis='both', which='major', labelsize=48)
        ax_challenge.legend(fontsize=36, loc='best')

        # Add statistics panel for challenge rates
        challenge_stats_text = []
        for player in self.players:
            challenge_rates = condition_data[player]['challenge_rates']
            if challenge_rates:
                mean_rate = np.mean(challenge_rates)
                std_rate = np.std(challenge_rates)
                challenge_stats_text.append(f'{player}: {mean_rate:.2f}±{std_rate:.2f}')

        challenge_stats_str = '\n'.join(challenge_stats_text)
        ax_challenge.text(0.03, 0.96, f'Mean ± Std:\n{challenge_stats_str}',
                         transform=ax_challenge.transAxes, fontsize=32,
                         verticalalignment='top', horizontalalignment='left',
                         bbox=dict(boxstyle='round,pad=0.6', facecolor='white', alpha=0.85))

        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        print(f"Combined bluff and challenge evolution plot saved as {save_path}")

    def create_multi_condition_comparison_plot(self, save_path: str = "multi_condition_behavioral_evolution.png"):
        """Create 2×N grid plot comparing bluff and challenge rates across multiple conditions"""

        if not self.behavioral_data:
            print("No data loaded. Please run load_all_behavioral_data() first.")
            return

        num_conditions = len(self.conditions)
        if num_conditions == 1:
            print("Only one condition selected. Use single condition plots instead.")
            return

        # Create 2×N subplot layout: first row for bluff rates, second row for challenge rates
        fig, axes = plt.subplots(2, num_conditions, figsize=(15 * num_conditions, 20))

        # Handle case where num_conditions == 2 (axes is 2D but first dimension has only 2 elements)
        if num_conditions == 2:
            axes = axes.reshape(2, 2)

        condition_list = list(self.conditions.keys())

        for col_idx, condition in enumerate(condition_list):
            condition_data = self.behavioral_data[condition]
            condition_label = self.condition_labels[condition]

            # Get axes for this condition
            ax_bluff = axes[0, col_idx]      # Top row: bluff rates
            ax_challenge = axes[1, col_idx]  # Bottom row: challenge rates

            # Plot bluff rates for all players in this condition
            for player in self.players:
                bluff_rates = condition_data[player]['bluff_rates']
                if bluff_rates and len(bluff_rates) > 2:
                    # Use player's base color (no condition variation since we're separating by subplot)
                    color = self.base_colors[player]

                    # Create game numbers
                    games = np.array(range(1, len(bluff_rates) + 1))
                    rates_array = np.array(bluff_rates)

                    # Apply smoothing and calculate standard deviations
                    games_smooth, rates_smooth, stds = self.smooth_data(
                        games, rates_array, window_size=8, sigma=1.8
                    )

                    # Plot shaded area for standard deviation
                    ax_bluff.fill_between(games_smooth,
                                        rates_smooth - stds * 0.45,
                                        rates_smooth + stds * 0.45,
                                        color=color, alpha=0.2, zorder=1)

                    # Plot smoothed line with distinctive markers and line styles
                    style = self.line_styles[player]
                    ax_bluff.plot(games_smooth, rates_smooth,
                                color=color, alpha=0.8, linewidth=4,
                                marker=style['marker'], linestyle=style['linestyle'],
                                markersize=style['markersize'], markeredgewidth=1.5,
                                markeredgecolor='white', markerfacecolor=color,
                                markevery=5, zorder=2,
                                label=f'{player} ({self.name_to_model[player]})')

            # Plot challenge rates for all players in this condition
            for player in self.players:
                challenge_rates = condition_data[player]['challenge_rates']
                if challenge_rates and len(challenge_rates) > 2:
                    # Use player's base color (no condition variation since we're separating by subplot)
                    color = self.base_colors[player]

                    # Create game numbers
                    games = np.array(range(1, len(challenge_rates) + 1))
                    rates_array = np.array(challenge_rates)

                    # Apply smoothing and calculate standard deviations
                    games_smooth, rates_smooth, stds = self.smooth_data(
                        games, rates_array, window_size=8, sigma=1.8
                    )

                    # Plot shaded area for standard deviation
                    ax_challenge.fill_between(games_smooth,
                                            rates_smooth - stds * 0.3,
                                            rates_smooth + stds * 0.3,
                                            color=color, alpha=0.2, zorder=1)

                    # Plot smoothed line with distinctive markers and line styles
                    style = self.line_styles[player]
                    ax_challenge.plot(games_smooth, rates_smooth,
                                    color=color, alpha=0.8, linewidth=4,
                                    marker=style['marker'], linestyle=style['linestyle'],
                                    markersize=style['markersize'], markeredgewidth=1.5,
                                    markeredgecolor='white', markerfacecolor=color,
                                    markevery=5, zorder=2,
                                    label=f'{player} ({self.name_to_model[player]})')

            # Customize bluff subplot (top row)
            ax_bluff.set_title(f'Liars Bar {condition_label}',
                             fontsize=42, fontweight='bold')
            ax_bluff.set_ylim(-0.05, 1.05)
            ax_bluff.grid(True, alpha=0.3)
            ax_bluff.tick_params(axis='both', which='major', labelsize=36)

            # Only leftmost subplot gets y-label for bluff rate
            if col_idx == 0:
                ax_bluff.set_ylabel('Bluff Rate', fontsize=48, fontweight='bold')

            # Legend for bluff rates
            ax_bluff.legend(fontsize=28, loc='best')

            # Add statistics panel for bluff rates
            bluff_stats_text = []
            for player in self.players:
                bluff_rates = condition_data[player]['bluff_rates']
                if bluff_rates:
                    mean_rate = np.mean(bluff_rates)
                    std_rate = np.std(bluff_rates)
                    bluff_stats_text.append(f'{player}: {mean_rate:.2f}±{std_rate:.2f}')

            bluff_stats_str = '\n'.join(bluff_stats_text)
            ax_bluff.text(0.03, 0.96, f'Mean ± Std:\n{bluff_stats_str}',
                         transform=ax_bluff.transAxes, fontsize=24,
                         verticalalignment='top', horizontalalignment='left',
                         bbox=dict(boxstyle='round,pad=0.6', facecolor='white', alpha=0.85))

            # Customize challenge subplot (bottom row) - NO TITLE
            ax_challenge.set_xlabel('Game Number', fontsize=48, fontweight='bold')
            ax_challenge.set_ylim(-0.05, 1.05)
            ax_challenge.grid(True, alpha=0.3)
            ax_challenge.tick_params(axis='both', which='major', labelsize=36)

            # Only leftmost subplot gets y-label for challenge rate
            if col_idx == 0:
                ax_challenge.set_ylabel('Challenge Rate', fontsize=48, fontweight='bold')

            # Legend for challenge rates
            ax_challenge.legend(fontsize=28, loc='best')

            # Add statistics panel for challenge rates
            challenge_stats_text = []
            for player in self.players:
                challenge_rates = condition_data[player]['challenge_rates']
                if challenge_rates:
                    mean_rate = np.mean(challenge_rates)
                    std_rate = np.std(challenge_rates)
                    challenge_stats_text.append(f'{player}: {mean_rate:.2f}±{std_rate:.2f}')

            challenge_stats_str = '\n'.join(challenge_stats_text)
            ax_challenge.text(0.03, 0.96, f'Mean ± Std:\n{challenge_stats_str}',
                             transform=ax_challenge.transAxes, fontsize=24,
                             verticalalignment='top', horizontalalignment='left',
                             bbox=dict(boxstyle='round,pad=0.6', facecolor='white', alpha=0.85))

        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        print(f"Multi-condition behavioral evolution plot saved as {save_path}")

    def create_combined_evolution_plots(self, save_path: str = "improved_behavioral_evolution.png"):
        """Create combined plots showing bluff, challenge, and score evolution"""

        if not self.behavioral_data or not self.scores_data:
            print("No data loaded. Please run load_all_behavioral_data() and load_all_scores() first.")
            return

        fig, axes = plt.subplots(3, 4, figsize=(40, 30))

        for i, player in enumerate(self.players):
            # Bluff rate subplot (top row)
            ax_bluff = axes[0, i]
            # Challenge rate subplot (middle row)
            ax_challenge = axes[1, i]
            # Score progression subplot (bottom row)
            ax_score = axes[2, i]

            # Plot bluff rates
            for condition in self.conditions.keys():
                if condition in self.behavioral_data:
                    bluff_rates = self.behavioral_data[condition][player]['bluff_rates']
                    if bluff_rates and len(bluff_rates) > 2:
                        color = self.get_bar_color_variations(self.base_colors[player], condition)
                        alpha = self.get_alpha_for_condition(condition)

                        games = np.array(range(1, len(bluff_rates) + 1))
                        rates_array = np.array(bluff_rates)
                        games_smooth, rates_smooth, stds = self.smooth_data(games, rates_array)

                        # Plot shaded area for standard deviation
                        ax_bluff.fill_between(games_smooth,
                                           rates_smooth - stds * 0.3,
                                           rates_smooth + stds * 0.3,
                                           color=color, alpha=0.2, zorder=1)

                        # Plot smoothed line with distinctive markers and line styles
                        style = self.line_styles[player]
                        ax_bluff.plot(games_smooth, rates_smooth,
                                    color=color, alpha=alpha, linewidth=4,
                                    marker=style['marker'], linestyle=style['linestyle'],
                                    markersize=style['markersize'], markeredgewidth=1.5,
                                    markeredgecolor='white', markerfacecolor=color,
                                    markevery=5, zorder=2)

            # Plot challenge rates
            for condition in self.conditions.keys():
                if condition in self.behavioral_data:
                    challenge_rates = self.behavioral_data[condition][player]['challenge_rates']
                    if challenge_rates and len(challenge_rates) > 2:
                        color = self.get_bar_color_variations(self.base_colors[player], condition)
                        alpha = self.get_alpha_for_condition(condition)

                        games = np.array(range(1, len(challenge_rates) + 1))
                        rates_array = np.array(challenge_rates)
                        games_smooth, rates_smooth, stds = self.smooth_data(games, rates_array)

                        # Plot shaded area for standard deviation
                        ax_challenge.fill_between(games_smooth,
                                               rates_smooth - stds * 0.3,
                                               rates_smooth + stds * 0.3,
                                               color=color, alpha=0.2, zorder=1)

                        # Plot smoothed line with distinctive markers and line styles
                        style = self.line_styles[player]
                        ax_challenge.plot(games_smooth, rates_smooth,
                                        color=color, alpha=alpha, linewidth=4,
                                        marker=style['marker'], linestyle=style['linestyle'],
                                        markersize=style['markersize'], markeredgewidth=1.5,
                                        markeredgecolor='white', markerfacecolor=color,
                                        markevery=5, zorder=2)

            # Plot score progression
            for condition in self.conditions.keys():
                if condition in self.scores_data:
                    scores = self.scores_data[condition][player]
                    if scores and len(scores) > 2:
                        color = self.get_bar_color_variations(self.base_colors[player], condition)
                        alpha = self.get_alpha_for_condition(condition)

                        games = np.array(range(1, len(scores) + 1))
                        scores_array = np.array(scores)
                        games_smooth, scores_smooth, stds = self.smooth_data(games, scores_array)

                        # Plot shaded area for standard deviation
                        ax_score.fill_between(games_smooth,
                                            scores_smooth - stds * 0.3,
                                            scores_smooth + stds * 0.3,
                                            color=color, alpha=0.2, zorder=1)

                        # Plot smoothed line with distinctive markers and line styles
                        style = self.line_styles[player]
                        ax_score.plot(games_smooth, scores_smooth,
                                    color=color, alpha=alpha, linewidth=4,
                                    marker=style['marker'], linestyle=style['linestyle'],
                                    markersize=style['markersize'], markeredgewidth=1.5,
                                    markeredgecolor='white', markerfacecolor=color,
                                    markevery=5, zorder=2)

            # Customize bluff subplot (only top row gets titles)
            ax_bluff.set_title(f'Liars Bar {player} ({self.name_to_model[player]})',
                             fontsize=30, fontweight='bold')
            ax_bluff.set_ylim(-0.05, 1.05)
            ax_bluff.grid(True, alpha=0.3)
            ax_bluff.tick_params(axis='both', which='major', labelsize=32)

            # Only leftmost subplot gets y-label for bluff rate
            if i == 0:
                ax_bluff.set_ylabel('Bluff Rate', fontsize=36, fontweight='bold')

            # Customize challenge subplot (no title for middle row)
            ax_challenge.set_ylim(-0.05, 1.05)
            ax_challenge.grid(True, alpha=0.3)
            ax_challenge.tick_params(axis='both', which='major', labelsize=32)

            # Only leftmost subplot gets y-label for challenge rate
            if i == 0:
                ax_challenge.set_ylabel('Challenge Rate', fontsize=36, fontweight='bold')

            # Customize score subplot (no title for bottom row)
            ax_score.grid(True, alpha=0.3)
            ax_score.tick_params(axis='both', which='major', labelsize=32)
            ax_score.axhline(y=0, color='black', linestyle='--', alpha=0.3)

            # Only leftmost subplot gets y-label for score
            if i == 0:
                ax_score.set_ylabel('Final Score', fontsize=36, fontweight='bold')

            # Add legend to all subplots
            ax_bluff.legend(fontsize=24, loc='best')
            ax_challenge.legend(fontsize=24, loc='best')
            ax_score.legend(fontsize=24, loc='best')

        # Add a single x-axis label for the entire figure
        fig.text(0.5, 0.02, 'Game Number', ha='center', va='bottom',
                fontsize=36, fontweight='bold')

        plt.tight_layout()
        plt.subplots_adjust(bottom=0.08)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        print(f"Combined behavioral evolution plots saved as {save_path}")

def main():
    """Main function to create improved behavioral evolution plots"""
    print("=== Creating Improved Behavioral Evolution Plots ===")
    
    plotter = ImprovedBehavioralEvolution()
    
    # Interactive condition selection
    selected_conditions = plotter.select_conditions_and_paths()
    
    # Load data for selected conditions
    plotter.load_all_behavioral_data()
    
    # Ask which plots to generate
    print("\n=== Plot Selection ===")
    print("Which plots would you like to generate?")

    # Check if multiple conditions were selected to offer multi-condition plot
    if len(selected_conditions) > 1:
        print("  1. Single bluff evolution plot (all players together)")
        print("  2. Single challenge evolution plot (all players together)")
        print("  3. Both single plots")
        print("  4. Multi-condition comparison (2×N grid: bluff rates top row, challenge rates bottom row)")
    else:
        print("  1. Single bluff evolution plot (all players together)")
        print("  2. Single challenge evolution plot (all players together)")
        print("  3. Both plots")

    if len(selected_conditions) > 1:
        plot_selection = input("Your selection (1, 2, 3, or 4): ").strip()
    else:
        plot_selection = input("Your selection (1, 2, or 3): ").strip()

    try:
        plot_choice = int(plot_selection)
    except ValueError:
        if len(selected_conditions) > 1:
            print("Invalid input. Generating multi-condition comparison by default.")
            plot_choice = 4
        else:
            print("Invalid input. Generating both plots by default.")
            plot_choice = 3

    # Create selected visualizations
    if plot_choice == 1:
        plotter.create_single_bluff_evolution_plot()
    elif plot_choice == 2:
        plotter.create_single_challenge_evolution_plot()
    elif plot_choice == 3:
        if len(selected_conditions) > 1:
            # For multiple conditions, generate separate single plots
            plotter.create_single_bluff_evolution_plot()
            plotter.create_single_challenge_evolution_plot()
        else:
            plotter.create_combined_bluff_challenge_plot()
    elif plot_choice == 4 and len(selected_conditions) > 1:
        plotter.create_multi_condition_comparison_plot()

    print("\n" + "="*60)
    print("Behavioral evolution plots complete!")
    if plot_choice == 1:
        print("📁 Generated: single_bluff_evolution.png")
    elif plot_choice == 2:
        print("📁 Generated: single_challenge_evolution.png")
    elif plot_choice == 3:
        if len(selected_conditions) > 1:
            print("📁 Generated: single_bluff_evolution.png")
            print("📁 Generated: single_challenge_evolution.png")
        else:
            print("📁 Generated: combined_bluff_challenge_evolution.png")
    elif plot_choice == 4 and len(selected_conditions) > 1:
        print("📁 Generated: multi_condition_behavioral_evolution.png")

if __name__ == "__main__":
    main()