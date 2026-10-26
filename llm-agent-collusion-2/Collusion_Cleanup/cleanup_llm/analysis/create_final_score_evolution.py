"""
Create line plot showing final score evolution for each model across games
Adapted from Liar's Bar final score evolution analysis for Cleanup game
"""

import matplotlib.pyplot as plt
import numpy as np
import json
import os
import glob
from scipy.ndimage import gaussian_filter1d
from typing import Dict, List

class CleanupFinalScoreEvolutionPlotter:
    """Create line plots showing final score evolution across Cleanup games"""

    def __init__(self):
        # Model to player name mapping
        self.model_to_player = {
            'llama-3.1-8b': 'Lily',
            'llama-3.2-3b': 'Luke',
            'ministral-8b': 'Mike',
            'qwen2.5-7b': 'Quinn'
        }

        # Color scheme - Lily: red, Luke: purple, Mike: orange, Quinn: green
        self.base_colors = {
            'llama-3.1-8b': '#e41a1c',    # red (Lily)
            'llama-3.2-3b': '#984ea3',      # purple (Luke)
            'ministral-8b': '#ff7f00',      # orange (Mike)
            'qwen2.5-7b': '#4daf4a'       # green (Quinn)
        }

        # Different line styles and markers - Lily: circles, Luke: triangles, Mike: squares, Quinn: stars
        self.line_styles = {
            'llama-3.1-8b': {'marker': 'o', 'linestyle': '-', 'markersize': 17},     # circles (Lily)
            'llama-3.2-3b': {'marker': '^', 'linestyle': '--', 'markersize': 25},      # triangles (Luke)
            'ministral-8b': {'marker': 's', 'linestyle': '-.', 'markersize': 17},      # squares (Mike)
            'qwen2.5-7b': {'marker': '*', 'linestyle': ':', 'markersize': 25}        # stars (Quinn)
        }

        # Order for legend: Lily, Luke, Mike, Quinn
        self.models = ['llama-3.1-8b', 'llama-3.2-3b', 'ministral-8b', 'qwen2.5-7b']

    def smooth_data(self, x, y, window_size=2, sigma=1.5):
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

    def extract_final_scores(self, directory_path: str) -> Dict[str, List[float]]:
        """Extract final scores for each model from JSON game records"""
        model_data = {model: [] for model in self.models}

        try:
            if not os.path.exists(directory_path):
                print(f"Warning: Directory {directory_path} not found")
                return model_data

            # Get all JSON files in the directory and sort by game number
            json_files = [f for f in os.listdir(directory_path) if f.endswith('.json')]
            json_files.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))  # Sort by game number

            for json_file in json_files:
                file_path = os.path.join(directory_path, json_file)
                try:
                    with open(file_path, 'r') as file:
                        game_data = json.load(file)

                    # Handle different game formats
                    if 'final_results' in game_data and 'scores' in game_data['final_results']:
                        final_scores = game_data['final_results']['scores']

                        # Check if this is baseline format (has model in agents) or secret format (has agent_configs)
                        if 'agents' in game_data and any('model' in agent_info for agent_info in game_data['agents'].values()):
                            # Baseline format: model info in agents[id]['model']
                            agents = game_data.get('agents', {})
                            for agent_id, score in final_scores.items():
                                if agent_id in agents:
                                    model_name = agents[agent_id].get('model', '')
                                    if model_name in model_data:
                                        model_data[model_name].append(float(score))

                        elif 'game_info' in game_data and 'agent_configs' in game_data['game_info']:
                            # Secret communication/hint format: model info in game_info['agent_configs']
                            agent_configs = game_data['game_info'].get('agent_configs', [])
                            for agent_id, score in final_scores.items():
                                agent_idx = int(agent_id)
                                if agent_idx < len(agent_configs) and 'model' in agent_configs[agent_idx]:
                                    model_name = agent_configs[agent_idx]['model']
                                    if model_name in model_data:
                                        model_data[model_name].append(float(score))

                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    print(f"Warning: Error reading {json_file}: {e}")
                    continue

        except Exception as e:
            print(f"Warning: Error accessing directory {directory_path}: {e}")

        return model_data

    def create_multi_condition_final_score_plot(self, data_directories: List[str], condition_names: List[str], save_path: str = "cleanup_final_score_evolution_multi.png"):
        """Create multi-condition plot showing final score evolution for multiple conditions"""

        num_conditions = len(data_directories)
        if num_conditions != len(condition_names):
            print("Error: Number of directories must match number of condition names")
            return

        # Load data for all conditions
        all_score_data = []
        for i, data_directory in enumerate(data_directories):
            print(f"Loading final score data from {data_directory}...")
            score_data = self.extract_final_scores(data_directory)
            all_score_data.append(score_data)

        # Check if we have data for any condition
        has_data = False
        for score_data in all_score_data:
            for model in self.models:
                if score_data[model]:
                    has_data = True
                    break
            if has_data:
                break

        if not has_data:
            print("No final score data found. Please check the directory paths.")
            return

        # Create 1xN subplot layout with equal width and height
        fig, axes = plt.subplots(1, num_conditions, figsize=(10 * num_conditions, 10))

        # Handle single condition case
        if num_conditions == 1:
            axes = [axes]

        # For each condition
        for cond_idx, (score_data, condition_name) in enumerate(zip(all_score_data, condition_names)):

            # Check if we have data for this condition
            total_games = 0
            for model in self.models:
                if score_data[model]:
                    total_games = max(total_games, len(score_data[model]))

            if total_games == 0:
                print(f"No data found for condition {condition_name}")
                continue

            print(f"✓ Extracted {total_games} games for {condition_name}")

            ax = axes[cond_idx]

            # Game numbers (x-axis)
            game_numbers = np.arange(1, total_games + 1)

            # Plot lines for each model with shaded areas for standard deviation
            for model in self.models:
                scores_data = score_data[model]
                if scores_data and len(scores_data) > 2:
                    color = self.base_colors[model]
                    alpha = 0.8

                    games = np.array(range(1, len(scores_data) + 1))
                    scores_array = np.array(scores_data)
                    games_smooth, scores_smooth, stds = self.smooth_data(games, scores_array)

                    # Plot shaded area for standard deviation (using 0.5 * std)
                    ax.fill_between(games_smooth,
                                   scores_smooth - stds * 0.5,
                                   scores_smooth + stds * 0.5,
                                   color=color, alpha=0.2, zorder=1)

                    # Plot smoothed line with distinctive markers and line styles
                    style = self.line_styles[model]
                    ax.plot(games_smooth, scores_smooth,
                           color=color, alpha=alpha, linewidth=4,
                           marker=style['marker'], linestyle=style['linestyle'],
                           markersize=style['markersize'], markeredgewidth=1.5,
                           markeredgecolor='white', markerfacecolor=color,
                           markevery=max(1, total_games//20), zorder=2,  # Adaptive marker frequency
                           label=f'{self.model_to_player[model]} ({model})')

            # Customize the plot with large fonts
            ax.set_xlabel('Game Number', fontsize=36, fontweight='bold')
            if cond_idx == 0:  # Only show y-label on first subplot
                ax.set_ylabel('Final Score', fontsize=36, fontweight='bold')
            ax.set_title(condition_name, fontsize=36, fontweight='bold')

            # Grid and styling
            ax.grid(True, alpha=0.3)
            ax.tick_params(axis='both', which='major', labelsize=32)

            # Legend
            ax.legend(fontsize=24, loc='best')

            # Set limits
            all_scores = [score for model_scores in score_data.values() for score in model_scores if score is not None]
            if all_scores:
                min_score = max(0, min(all_scores) - 2)  # Small padding below, don't go below 0
                max_score = max(all_scores) + 2  # Small padding above
                ax.set_ylim(min_score, max_score)
            else:
                ax.set_ylim(0, 20)  # Default range if no data
            ax.set_xlim(1, total_games)

            # Add statistics as text (only show player names)
            stats_text = []
            for model in self.models:
                if score_data[model]:
                    mean_score = np.mean(score_data[model])
                    std_score = np.std(score_data[model])
                    player_name = self.model_to_player[model]
                    stats_text.append(f'{player_name}: {mean_score:.1f}±{std_score:.1f}')

            # Add statistics box
            stats_str = '\n'.join(stats_text)
            ax.text(0.05, 0.95, f'Mean ± Std:\n{stats_str}',
                   transform=ax.transAxes, fontsize=26,
                   verticalalignment='top', horizontalalignment='left',
                   bbox=dict(boxstyle='round,pad=0.6', facecolor='white', alpha=0.85))

        # Adjust layout and save
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        print(f"Multi-condition final score evolution plot saved as {save_path}")

        return all_score_data

    def create_final_score_evolution_plot(self, data_directory: str, save_path: str = "cleanup_final_score_evolution.png"):
        """Create line plot showing final score evolution for Cleanup game"""

        # Use the multi-condition function with a single condition
        result = self.create_multi_condition_final_score_plot([data_directory], ["Cleanup Baseline"], save_path)
        return result[0] if result else None

def main():
    """Main function to create final score evolution plots"""
    print("=== Creating Cleanup Final Score Evolution Plot ===")

    # Ask user whether to analyze single condition or multiple conditions
    print("\nChoose analysis type:")
    print("1. Single condition analysis")
    print("2. Multi-condition analysis (up to 3 conditions)")

    choice = input("Enter choice (1 or 2): ").strip()

    plotter = CleanupFinalScoreEvolutionPlotter()

    if choice == "1":
        # Single condition analysis
        default_path = "/project/6101774/xijiez/Collusion_Cleanup/cleanup_llm/runs/base_1/game_record"
        print(f"\nDefault data directory: {default_path}")
        custom_path = input("Press Enter to use default, or enter custom path: ").strip()

        data_directory = custom_path if custom_path else default_path

        if not os.path.exists(data_directory):
            print(f"Warning: Directory {data_directory} not found")
            print("No data found. Please check the directory path.")
            return

        plotter.create_final_score_evolution_plot(data_directory)
        print("\n" + "="*50)
        print("Cleanup final score evolution plot complete!")
        print("📁 Generated: cleanup_final_score_evolution.png")

    elif choice == "2":
        # Multi-condition analysis
        print("\nMulti-condition analysis")
        print("You can select up to 3 conditions (baseline, secret comm, secret hint)")

        data_directories = []
        condition_names = []

        # Available condition templates
        available_conditions = {
            "1": {
                "name": "Cleanup Baseline",
                "path_template": "/project/6101774/xijiez/Collusion_Cleanup/cleanup_llm/runs/base_{}/game_record"
            },
            "2": {
                "name": "Cleanup Secret Comm",
                "path_template": "/project/6101774/xijiez/Collusion_Cleanup/cleanup_llm/runs/secret_comm_{}/game_record"
            },
            "3": {
                "name": "Cleanup Secret Hint",
                "path_template": "/project/6101774/xijiez/Collusion_Cleanup/cleanup_llm/runs/secret_hint_{}/game_record"
            }
        }

        print("\nAvailable conditions:")
        for key, info in available_conditions.items():
            print(f"{key}. {info['name']}")

        # Get condition selections
        selected_conditions = input("\nEnter condition numbers (e.g., '1,2,3' for all three): ").strip().split(',')
        selected_conditions = [c.strip() for c in selected_conditions if c.strip()]

        if not selected_conditions:
            print("No conditions selected. Exiting.")
            return

        # For each selected condition, ask for specific run number
        for cond_num in selected_conditions:
            if cond_num in available_conditions:
                cond_info = available_conditions[cond_num]
                print(f"\nFor {cond_info['name']}:")

                # Check available runs
                base_path = cond_info['path_template'].replace('_{}', '_*').replace('/game_record', '')
                available_runs = glob.glob(base_path)

                if available_runs:
                    print("Available runs:")
                    run_numbers = []
                    for run_path in sorted(available_runs):
                        run_num = run_path.split('_')[-1]
                        run_numbers.append(run_num)
                        print(f"  Run {run_num}: {run_path}")

                    default_run = run_numbers[0] if run_numbers else "1"
                    run_choice = input(f"Enter run number (default: {default_run}): ").strip()
                    run_choice = run_choice if run_choice else default_run
                else:
                    print("No runs found, using run number 1")
                    run_choice = "1"

                full_path = cond_info['path_template'].format(run_choice)

                if os.path.exists(full_path):
                    data_directories.append(full_path)
                    condition_names.append(cond_info['name'])
                    print(f"✓ Added: {full_path}")
                else:
                    print(f"⚠ Warning: Path not found: {full_path}")
            else:
                print(f"⚠ Warning: Invalid condition number: {cond_num}")

        if not data_directories:
            print("No valid directories found. Exiting.")
            return

        print(f"\nAnalyzing {len(data_directories)} conditions...")
        plotter.create_multi_condition_final_score_plot(data_directories, condition_names)

        print("\n" + "="*50)
        print("Multi-condition cleanup final score evolution plot complete!")
        print("📁 Generated: cleanup_final_score_evolution_multi.png")

    else:
        print("Invalid choice. Please run again and select 1 or 2.")

if __name__ == "__main__":
    main()