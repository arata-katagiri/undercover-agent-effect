"""
Create line plot showing final score evolution for each player across conditions
Uses the same style as survival_rounds_evolution.py
"""

import matplotlib.pyplot as plt
import numpy as np
import json
import os
from scipy.ndimage import gaussian_filter1d
from typing import Dict, List

class FinalScoreEvolutionPlotter:
    """Create line plots showing final score evolution across games"""
    
    def __init__(self):
        # Color scheme - Luke: purple, Mike: orange, Lily: red, Quinn: green
        self.base_colors = {
            'Luke': '#984ea3',     # purple
            'Mike': '#ff7f00',     # orange
            'Lily': '#e41a1c',     # red
            'Quinn': '#4daf4a'     # green
        }

        # Different line styles and markers for each player
        self.line_styles = {
            'Lily': {'marker': 'o', 'linestyle': '-', 'markersize': 17},     # circles
            'Luke': {'marker': '^', 'linestyle': '--', 'markersize': 25},    # triangles
            'Mike': {'marker': 's', 'linestyle': '-.', 'markersize': 17},    # squares
            'Quinn': {'marker': '*', 'linestyle': ':', 'markersize': 25}     # stars
        }
        
        # Model mapping for labels
        self.name_to_model = {
            'Lily': 'llama-3.1-8b',
            'Mike': 'ministral-8b', 
            'Luke': 'llama-3.2-3b',
            'Quinn': 'qwen2.5-7b'
        }
        
        self.players = ['Lily', 'Luke', 'Mike', 'Quinn']
        
        # Initialize empty - will be populated by select_conditions_and_paths
        self.conditions = {}
        self.condition_labels = {}
        
        # All available conditions
        self.available_conditions = {
            'baseline': {
                'default_path': '../../experiments/game_records/Lily-Luke-Mike-Quinn',
                'label': 'Baseline'
            },
            '1_comm': {
                'default_path': '../../experiments/game_records/Lily-Luke-Mike-Quinn_communication',
                'label': 'Fair-Comm'
            },
            '3_comm': {
                'default_path': '../../experiments/game_records/Lily-Luke-Mike-Quinn_communication_3',
                'label': '3-Comm'
            },
            'secret': {
                'default_path': '../../experiments/game_records/Lily-Luke-Mike-Quinn_secret_comm',
                'label': 'Secret Comm'
            },
            'secret_hint': {
                'default_path': '../../experiments/game_records/Lily-Luke-Mike-Quinn_secret_hint',
                'label': 'Secret Hint'
            }
        }
    
    def get_bar_color_variations(self, base_color: str, condition: str) -> str:
        """Get color variation for different conditions (same as survival_rounds_evolution)"""
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
            # For secret hint, use same as base color
            return base_color
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
    
    def select_conditions_and_paths(self):
        """Interactive selection of conditions to analyze"""
        print("\n" + "="*60)
        print("CONDITION SELECTION")
        print("="*60)
        print("\nAvailable conditions:")
        for idx, (key, info) in enumerate(self.available_conditions.items(), 1):
            print(f"  {idx}. {info['label']} ({key})")
        
        print("\nEnter the numbers of conditions you want to analyze")
        print("(e.g., '1,4' for baseline vs secret, '1,2,3,4' for all):")
        
        while True:
            selection = input("Your selection: ").strip()
            try:
                indices = [int(x.strip()) for x in selection.split(',')]
                if all(1 <= idx <= len(self.available_conditions) for idx in indices):
                    break
                else:
                    print(f"Please enter numbers between 1 and {len(self.available_conditions)}")
            except:
                print("Invalid input. Please enter comma-separated numbers (e.g., '1,4')")
        
        # Map selected indices to conditions
        condition_keys = list(self.available_conditions.keys())
        selected_conditions = [condition_keys[idx-1] for idx in indices]
        
        print("\nSelected conditions:", ", ".join([self.available_conditions[c]['label'] for c in selected_conditions]))
        
        # Now get paths for each selected condition
        for condition in selected_conditions:
            info = self.available_conditions[condition]
            print(f"\n{info['label']} condition:")
            print(f"  Default path: {info['default_path']}")
            custom = input("  Press Enter to use default, or enter custom path: ").strip()
            
            if custom:
                path = custom
            else:
                path = info['default_path']
            
            self.conditions[condition] = path
            self.condition_labels[condition] = info['label']
        
        print("\n" + "="*60)
        print("Configuration complete!")
        print("="*60)
        
    def extract_final_scores(self, directory_path: str) -> Dict[str, List[float]]:
        """Extract final scores for each player from JSON files"""
        player_data = {player: [] for player in self.players}
        
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
                                score = float(final_scores[player])
                                player_data[player].append(score)
                            else:
                                player_data[player].append(0.0)
                    else:
                        # If no final scores data, append 0 for all players
                        for player in self.players:
                            player_data[player].append(0.0)
                                
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    print(f"Warning: Error reading {json_file}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Warning: Error accessing directory {directory_path}: {e}")
            
        return player_data
    
    def load_all_score_data(self):
        """Load final score data from all selected conditions"""
        print("\nLoading final score data...")
        
        self.score_data = {}
        
        for condition, directory in self.conditions.items():
            data = self.extract_final_scores(directory)
            self.score_data[condition] = data
            
            # Print summary
            total_games = len(data['Lily']) if data['Lily'] else 0
            print(f"✓ {self.condition_labels[condition]}: Extracted {total_games} games from {directory}")
    
    def create_final_score_evolution_plot(self, save_path: str = "final_score_evolution.png"):
        """Create line plot(s) showing final score evolution"""
        
        if not self.conditions:
            print("No conditions selected. Please run select_conditions_and_paths() first.")
            return None
            
        # Load data for all selected conditions
        self.load_all_score_data()
        
        # Determine subplot layout
        num_conditions = len(self.conditions)
        
        if num_conditions == 1:
            # Single square plot
            fig, ax = plt.subplots(1, 1, figsize=(10, 10))
            axes = [ax]
        else:
            # Multiple horizontal subplots - keep square aspect ratio for each subplot
            fig, axes = plt.subplots(1, num_conditions, figsize=(10 * num_conditions, 10))
            if num_conditions == 2:
                axes = [axes[0], axes[1]]  # Ensure axes is always a list
        
        # Create plots for each condition
        for idx, (condition, condition_data) in enumerate(self.score_data.items()):
            ax = axes[idx] if num_conditions > 1 else axes[0]
            
            # Check if we have data
            total_games = len(condition_data['Lily']) if condition_data['Lily'] else 0
            if total_games == 0:
                ax.text(0.5, 0.5, f'No data available\nfor {self.condition_labels[condition]}',
                       transform=ax.transAxes, ha='center', va='center', fontsize=24)
                ax.set_title(f'Liars Bar {self.condition_labels[condition]}', fontsize=36, fontweight='bold')
                continue
            
            # Game numbers (x-axis)
            game_numbers = np.arange(1, total_games + 1)
            
            # Plot lines for each player with shaded areas for standard deviation
            for player in self.players:
                scores_data = condition_data[player]
                if scores_data and len(scores_data) > 2:
                    color = self.get_bar_color_variations(self.base_colors[player], condition)
                    alpha = self.get_alpha_for_condition(condition)

                    games = np.array(range(1, len(scores_data) + 1))
                    scores_array = np.array(scores_data)
                    games_smooth, scores_smooth, stds = self.smooth_data(games, scores_array)

                    # Plot shaded area for standard deviation (thinner - using 0.5 * std)
                    ax.fill_between(games_smooth,
                                   scores_smooth - stds * 0.5,
                                   scores_smooth + stds * 0.5,
                                   color=color, alpha=0.2, zorder=1)

                    # Plot smoothed line with distinctive markers and line styles
                    style = self.line_styles[player]
                    ax.plot(games_smooth, scores_smooth,
                           color=color, alpha=alpha, linewidth=4,
                           marker=style['marker'], linestyle=style['linestyle'],
                           markersize=style['markersize'], markeredgewidth=1.5,
                           markeredgecolor='white', markerfacecolor=color,
                           markevery=5, zorder=2,  # Show markers every 5 points to avoid clutter
                           label=f'{player} ({self.name_to_model[player]})')
            
            # Customize the subplot with much larger fonts
            ax.set_xlabel('Game Number', fontsize=36, fontweight='bold')
            # Only show "Final Score" on the leftmost subplot
            if idx == 0:
                ax.set_ylabel('Final Score', fontsize=36, fontweight='bold')
            else:
                ax.set_ylabel('')  # Empty label for other subplots
            ax.set_title(f'Liars Bar {self.condition_labels[condition]}',
                        fontsize=36, fontweight='bold')

            # Grid and styling
            ax.grid(True, alpha=0.3)
            ax.tick_params(axis='both', which='major', labelsize=32)

            # Legend on all subplots
            ax.legend(fontsize=24, loc='best')

            # Set consistent limits - same y-axis scale for all conditions
            all_scores = [score for player_scores in condition_data.values() for score in player_scores if score is not None]
            if all_scores:
                min_score = min(all_scores)
                # Use consistent upper bound of 100 for all plots
                ax.set_ylim(min_score - 5, 100)  # Small padding below, fixed upper bound
            else:
                ax.set_ylim(0, 100)  # Default range if no data
            ax.set_xlim(1, total_games)

            # Add statistics as text
            stats_text = []
            for player in self.players:
                if condition_data[player]:
                    mean_score = np.mean(condition_data[player])
                    std_score = np.std(condition_data[player])
                    stats_text.append(f'{player}: {mean_score:.1f}±{std_score:.1f}')

            # Add statistics box with much larger font - moved lower and to the right
            stats_str = '\n'.join(stats_text)
            ax.text(0.05, 0.95, f'Mean ± Std:\n{stats_str}',
                   transform=ax.transAxes, fontsize=26,
                   verticalalignment='top', horizontalalignment='left',
                   bbox=dict(boxstyle='round,pad=0.6', facecolor='white', alpha=0.85))
        
        # Adjust layout and save
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        print(f"Final score evolution plot saved as {save_path}")
        
        return self.score_data

def main():
    """Main function to create final score evolution plot"""
    print("=== Creating Final Score Evolution Plot ===")
    
    plotter = FinalScoreEvolutionPlotter()
    
    # Interactive condition selection
    plotter.select_conditions_and_paths()
    
    # Create the final score evolution plot
    plotter.create_final_score_evolution_plot()
    
    print("\n" + "="*50)
    print("Final score evolution plot complete!")
    print("📁 Generated: final_score_evolution.png")

if __name__ == "__main__":
    main()