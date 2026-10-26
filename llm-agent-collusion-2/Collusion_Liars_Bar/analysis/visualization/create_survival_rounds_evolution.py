"""
Create line plot showing survival rounds evolution for each player under secret communication
"""

import matplotlib.pyplot as plt
import numpy as np
import json
import os
from scipy.ndimage import gaussian_filter1d
from typing import Dict, List

class SurvivalRoundsEvolutionPlotter:
    """Create line plots showing survival rounds evolution across games"""
    
    def __init__(self):
        # Color scheme - Luke: purple, Mike: orange, Lily: red, Quinn: green
        self.base_colors = {
            'Luke': '#984ea3',     # purple  
            'Mike': '#ff7f00',     # orange
            'Lily': '#e41a1c',     # red
            'Quinn': '#4daf4a'     # green
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
                'label': '1-Comm'
            },
            '3_comm': {
                'default_path': '../../experiments/game_records/Lily-Luke-Mike-Quinn_communication_3',
                'label': '3-Comm'
            },
            'secret': {
                'default_path': '../../experiments/game_records/Lily-Luke-Mike-Quinn_secret_comm',
                'label': 'Secret'
            },
            'secret_hint': {
                'default_path': '../../experiments/game_records/Lily-Luke-Mike-Quinn_secret_hint',
                'label': 'Secret Hint'
            }
        }
    
    def get_bar_color_variations(self, base_color: str, condition: str) -> str:
        """Get color variation for different conditions (same as improved_behavioral_evolution)"""
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
        
        # Calculate rolling standard error for error bars
        y_errors = []
        half_window = window_size // 2
        
        for i in range(len(y)):
            start_idx = max(0, i - half_window)
            end_idx = min(len(y), i + half_window + 1)
            window_data = y[start_idx:end_idx]
            
            if len(window_data) > 1:
                std_err = np.std(window_data) / np.sqrt(len(window_data))
            else:
                std_err = 0
            y_errors.append(std_err)
        
        return x, y_smooth, np.array(y_errors)
    
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
        
    def extract_survival_rounds(self, directory_path: str) -> Dict[str, List[int]]:
        """Extract survival rounds for each player from JSON files"""
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
                            player_data[player].append(rounds_survived)
                    else:
                        # If no rounds data, append 0 for all players
                        for player in self.players:
                            player_data[player].append(0)
                                
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    print(f"Warning: Error reading {json_file}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Warning: Error accessing directory {directory_path}: {e}")
            
        return player_data
    
    def load_all_survival_data(self):
        """Load survival rounds data from all selected conditions"""
        print("\nLoading survival rounds data...")
        
        self.survival_data = {}
        
        for condition, directory in self.conditions.items():
            data = self.extract_survival_rounds(directory)
            self.survival_data[condition] = data
            
            # Print summary
            total_games = len(data['Lily']) if data['Lily'] else 0
            print(f"✓ {self.condition_labels[condition]}: Extracted {total_games} games from {directory}")
    
    def create_survival_rounds_plot(self, save_path: str = "survival_rounds_evolution.png"):
        """Create line plot(s) showing survival rounds evolution"""
        
        if not self.conditions:
            print("No conditions selected. Please run select_conditions_and_paths() first.")
            return None
            
        # Load data for all selected conditions
        self.load_all_survival_data()
        
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
        for idx, (condition, condition_data) in enumerate(self.survival_data.items()):
            ax = axes[idx] if num_conditions > 1 else axes[0]
            
            # Check if we have data
            total_games = len(condition_data['Lily']) if condition_data['Lily'] else 0
            if total_games == 0:
                ax.text(0.5, 0.5, f'No data available\nfor {self.condition_labels[condition]}', 
                       transform=ax.transAxes, ha='center', va='center', fontsize=16)
                ax.set_title(f'{self.condition_labels[condition]} Condition', fontsize=18, fontweight='bold')
                continue
            
            # Game numbers (x-axis)
            game_numbers = np.arange(1, total_games + 1)
            
            # Plot lines for each player using the same style as improved_behavioral_evolution
            for player in self.players:
                rounds_data = condition_data[player]
                if rounds_data and len(rounds_data) > 2:
                    color = self.get_bar_color_variations(self.base_colors[player], condition)
                    alpha = self.get_alpha_for_condition(condition)
                    
                    games = np.array(range(1, len(rounds_data) + 1))
                    rounds_array = np.array(rounds_data)
                    games_smooth, rounds_smooth, errors = self.smooth_data(games, rounds_array)
                    
                    # Plot raw data points (scatter)
                    ax.scatter(games, rounds_array, color=color, alpha=0.3, s=20, zorder=1)
                    
                    # Plot smoothed line with error bars
                    ax.errorbar(games_smooth, rounds_smooth, yerr=errors*0.5,
                               color=color, alpha=alpha, linewidth=2.5,
                               capsize=2, capthick=1, marker='o', markersize=3,
                               markeredgewidth=0.5, markeredgecolor='white',
                               markerfacecolor=color, zorder=2,
                               label=f'{player} ({self.name_to_model[player]})' if idx == 0 else "")
            
            # Customize the subplot
            ax.set_xlabel('Game Number', fontsize=16, fontweight='bold')
            ax.set_ylabel('Survival Rounds', fontsize=16, fontweight='bold')
            ax.set_title(f'Survival Rounds Evolution - {self.condition_labels[condition]} Condition', 
                        fontsize=18, fontweight='bold')
            
            # Grid and styling
            ax.grid(True, alpha=0.3)
            ax.tick_params(axis='both', which='major', labelsize=14)
            
            # Legend (only on first subplot to avoid clutter)
            if idx == 0:
                ax.legend(fontsize=14, loc='best')
            
            # Set reasonable limits
            max_rounds = max([max(data) if data else 0 for data in condition_data.values()])
            ax.set_ylim(0, max_rounds + 2)
            ax.set_xlim(1, total_games)
            
            # Add statistics as text
            stats_text = []
            for player in self.players:
                if condition_data[player]:
                    mean_survival = np.mean(condition_data[player])
                    std_survival = np.std(condition_data[player])
                    stats_text.append(f'{player}: {mean_survival:.1f}±{std_survival:.1f}')
            
            # Add statistics box
            stats_str = '\n'.join(stats_text)
            ax.text(0.02, 0.98, f'Mean ± Std:\n{stats_str}', 
                   transform=ax.transAxes, fontsize=11,
                   verticalalignment='top', horizontalalignment='left',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
        
        # Adjust layout and save
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        print(f"Survival rounds evolution plot saved as {save_path}")
        
        return self.survival_data

def main():
    """Main function to create survival rounds evolution plot"""
    print("=== Creating Survival Rounds Evolution Plot ===")
    
    plotter = SurvivalRoundsEvolutionPlotter()
    
    # Interactive condition selection
    plotter.select_conditions_and_paths()
    
    # Create the survival rounds evolution plot
    plotter.create_survival_rounds_plot()
    
    print("\n" + "="*50)
    print("Survival rounds evolution plot complete!")
    print("📁 Generated: survival_rounds_evolution.png")

if __name__ == "__main__":
    main()