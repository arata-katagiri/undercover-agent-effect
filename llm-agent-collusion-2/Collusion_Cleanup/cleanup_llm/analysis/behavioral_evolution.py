"""
Cleanup Behavioral Evolution Analysis
Tracks CLEAN and ZAP action rates for each model across games
Adapted from Liar's Bar behavioral analysis with exact same styling
"""

import matplotlib.pyplot as plt
import numpy as np
import json
import os
import glob
from scipy.ndimage import gaussian_filter1d
from typing import Dict, List

class CleanupBehavioralEvolution:
    """Create behavioral evolution plots tracking CLEAN and ZAP actions"""

    def __init__(self):
        # Model to player name mapping (same as final score evolution)
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

        # Action mappings - ZAP includes all directional zaps
        self.zap_actions = ['ZAP_UP', 'ZAP_DOWN', 'ZAP_LEFT', 'ZAP_RIGHT']
        self.clean_actions = ['CLEAN']

    def smooth_data(self, x, y, window_size=5, sigma=2):
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

    def extract_action_rates_from_directory(self, directory_path: str) -> Dict[str, Dict]:
        """Extract CLEAN and ZAP rates for each model from Cleanup game records"""

        # Initialize data structure
        action_data = {}
        for model in self.models:
            action_data[model] = {'clean_rates': [], 'zap_rates': []}

        try:
            if not os.path.exists(directory_path):
                print(f"Warning: Directory {directory_path} not found")
                return action_data

            # Get all JSON files in the directory
            json_files = [f for f in os.listdir(directory_path) if f.endswith('.json')]
            json_files.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))  # Sort by game number

            if not json_files:
                print(f"No JSON files found in {directory_path}")
                return action_data

            print(f"Processing {len(json_files)} game files...")

            # Process each game file
            for json_file in json_files:
                file_path = os.path.join(directory_path, json_file)
                try:
                    with open(file_path, 'r') as file:
                        game_data = json.load(file)

                    # Extract agent to model mapping - handle different formats
                    agent_to_model = {}

                    # Check if this is baseline format (has 'rounds') or secret format (has 'steps')
                    if 'rounds' in game_data:
                        # Baseline format: model info in agents[id]['model']
                        if 'agents' in game_data:
                            for agent_id, agent_info in game_data['agents'].items():
                                if 'model' in agent_info:
                                    agent_to_model[agent_id] = agent_info['model']
                    elif 'steps' in game_data:
                        # Secret communication/hint format: model info in game_info['agent_configs']
                        if 'game_info' in game_data and 'agent_configs' in game_data['game_info']:
                            for i, agent_config in enumerate(game_data['game_info']['agent_configs']):
                                if 'model' in agent_config:
                                    agent_to_model[str(i)] = agent_config['model']

                    # Count actions for each agent in this game
                    agent_action_counts = {}

                    # Initialize counters
                    for agent_id in agent_to_model.keys():
                        agent_action_counts[agent_id] = {'clean': 0, 'zap': 0, 'total': 0}

                    # Count actions - handle both 'rounds' and 'steps' formats
                    action_data_key = 'rounds' if 'rounds' in game_data else 'steps'

                    if action_data_key in game_data:
                        for action_round in game_data[action_data_key]:
                            if 'actions' in action_round:
                                for agent_id, action in action_round['actions'].items():
                                    if agent_id in agent_action_counts:
                                        # Count all actions
                                        agent_action_counts[agent_id]['total'] += 1

                                        # Count specific action types
                                        if action in self.clean_actions:
                                            agent_action_counts[agent_id]['clean'] += 1
                                        elif action in self.zap_actions:
                                            agent_action_counts[agent_id]['zap'] += 1

                    # Calculate rates for this game and add to model data
                    for agent_id, model in agent_to_model.items():
                        if model in action_data and agent_id in agent_action_counts:
                            clean_count = agent_action_counts[agent_id]['clean']
                            zap_count = agent_action_counts[agent_id]['zap']
                            total_actions = agent_action_counts[agent_id]['total']

                            # Denominator: all actions (includes movement, clean, zap, collect, stay)
                            if total_actions > 0:
                                clean_rate = clean_count / total_actions
                                zap_rate = zap_count / total_actions
                            else:
                                clean_rate = 0.0
                                zap_rate = 0.0

                            action_data[model]['clean_rates'].append(clean_rate)
                            action_data[model]['zap_rates'].append(zap_rate)

                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    print(f"Warning: Error reading {json_file}: {e}")
                    continue

            # Print summary
            total_games = len(json_files)
            models_with_data = sum(1 for model in self.models
                                 if action_data[model]['clean_rates'])
            print(f"✓ Extracted {total_games} games with data for {models_with_data} models")

        except Exception as e:
            print(f"Warning: Error accessing directory {directory_path}: {e}")

        return action_data

    def create_multi_condition_behavioral_plot(self, data_directories: List[str], condition_names: List[str], save_path: str = "cleanup_behavioral_evolution_multi.png"):
        """Create 2x3 subplot showing CLEAN and ZAP rate evolution for multiple conditions"""

        num_conditions = len(data_directories)
        if num_conditions != len(condition_names):
            print("Error: Number of directories must match number of condition names")
            return

        # Load data for all conditions
        all_action_data = []
        for i, data_directory in enumerate(data_directories):
            print(f"Loading behavioral data from {data_directory}...")
            action_data = self.extract_action_rates_from_directory(data_directory)
            all_action_data.append(action_data)

        # Check if we have data for any condition
        has_data = False
        for action_data in all_action_data:
            for model in self.models:
                if action_data[model]['clean_rates']:
                    has_data = True
                    break
            if has_data:
                break

        if not has_data:
            print("No behavioral data found. Please check the directory paths.")
            return

        # Create 2xN subplot layout (2 rows: clean rates and zap rates)
        fig, axes = plt.subplots(2, num_conditions, figsize=(15 * num_conditions, 20))

        # Handle single condition case
        if num_conditions == 1:
            axes = axes.reshape(2, 1)

        # For each condition
        for cond_idx, (action_data, condition_name) in enumerate(zip(all_action_data, condition_names)):

            # Determine total games for x-axis
            total_games = 0
            for model in self.models:
                if action_data[model]['clean_rates']:
                    total_games = max(total_games, len(action_data[model]['clean_rates']))

            if total_games == 0:
                print(f"No games found in data for condition {condition_name}")
                continue

            # Plot CLEAN rates (top row)
            ax_clean = axes[0, cond_idx]
            for model in self.models:
                clean_rates = action_data[model]['clean_rates'].copy()
                if clean_rates and len(clean_rates) > 2:
                    color = self.base_colors[model]
                    style = self.line_styles[model]

                    # Pad data to match total_games if needed
                    while len(clean_rates) < total_games:
                        clean_rates.append(0.0)

                    games = np.array(range(1, len(clean_rates) + 1))
                    rates_array = np.array(clean_rates)

                    # Apply smoothing
                    games_smooth, rates_smooth, stds = self.smooth_data(
                        games, rates_array, window_size=5, sigma=1.0
                    )

                    # Plot shaded area for standard deviation
                    ax_clean.fill_between(games_smooth,
                                        rates_smooth - stds * 0.45,
                                        rates_smooth + stds * 0.45,
                                        color=color, alpha=0.2, zorder=1)

                    # Plot smoothed line with distinctive markers and line styles
                    ax_clean.plot(games_smooth, rates_smooth,
                                color=color, alpha=0.8, linewidth=4,
                                marker=style['marker'], linestyle=style['linestyle'],
                                markersize=style['markersize'], markeredgewidth=1.5,
                                markeredgecolor='white', markerfacecolor=color,
                                markevery=max(1, total_games//20), zorder=2,
                                label=f'{self.model_to_player[model]} ({model})')

            # Customize CLEAN subplot
            ax_clean.set_title(condition_name, fontsize=42, fontweight='bold')
            if cond_idx == 0:  # Only show y-label on first subplot of each row
                ax_clean.set_ylabel('Clean Rate', fontsize=48, fontweight='bold')
            ax_clean.set_ylim(-0.05, 1.05)
            ax_clean.set_xlim(1, total_games)
            ax_clean.set_xticks([0, 5, 10, 15, 20])
            ax_clean.grid(True, alpha=0.3)
            ax_clean.tick_params(axis='both', which='major', labelsize=36)
            ax_clean.legend(fontsize=28, loc='best')

            # Add statistics panel for CLEAN rates
            clean_stats_text = []
            for model in self.models:
                clean_rates = action_data[model]['clean_rates']
                if clean_rates:
                    mean_rate = np.mean(clean_rates)
                    std_rate = np.std(clean_rates)
                    player_name = self.model_to_player[model]
                    clean_stats_text.append(f'{player_name}: {mean_rate:.2f}±{std_rate:.2f}')

            clean_stats_str = '\n'.join(clean_stats_text)
            ax_clean.text(0.03, 0.96, f'Mean ± Std:\n{clean_stats_str}',
                         transform=ax_clean.transAxes, fontsize=30,
                         verticalalignment='top', horizontalalignment='left',
                         bbox=dict(boxstyle='round,pad=0.6', facecolor='white', alpha=0.85))

            # Plot ZAP rates (bottom row)
            ax_zap = axes[1, cond_idx]
            for model in self.models:
                zap_rates = action_data[model]['zap_rates'].copy()
                if zap_rates and len(zap_rates) > 2:
                    color = self.base_colors[model]
                    style = self.line_styles[model]

                    # Pad data to match total_games if needed
                    while len(zap_rates) < total_games:
                        zap_rates.append(0.0)

                    games = np.array(range(1, len(zap_rates) + 1))
                    rates_array = np.array(zap_rates)

                    # Apply smoothing
                    games_smooth, rates_smooth, stds = self.smooth_data(
                        games, rates_array, window_size=5, sigma=1.0
                    )

                    # Plot shaded area for standard deviation
                    ax_zap.fill_between(games_smooth,
                                      rates_smooth - stds * 0.5,
                                      rates_smooth + stds * 0.5,
                                      color=color, alpha=0.2, zorder=1)

                    # Plot smoothed line with distinctive markers and line styles
                    ax_zap.plot(games_smooth, rates_smooth,
                              color=color, alpha=0.8, linewidth=4,
                              marker=style['marker'], linestyle=style['linestyle'],
                              markersize=style['markersize'], markeredgewidth=1.5,
                              markeredgecolor='white', markerfacecolor=color,
                              markevery=max(1, total_games//20), zorder=2,
                              label=f'{self.model_to_player[model]} ({model})')

            # Customize ZAP subplot
            ax_zap.set_xlabel('Game Number', fontsize=48, fontweight='bold')
            if cond_idx == 0:  # Only show y-label on first subplot of each row
                ax_zap.set_ylabel('Zap Rate', fontsize=48, fontweight='bold')
            ax_zap.set_ylim(-0.05, 1.05)
            ax_zap.set_xlim(1, total_games)
            ax_zap.set_xticks([0, 5, 10, 15, 20])
            ax_zap.grid(True, alpha=0.3)
            ax_zap.tick_params(axis='both', which='major', labelsize=36)

            # Add statistics panel for ZAP rates
            zap_stats_text = []
            for model in self.models:
                zap_rates = action_data[model]['zap_rates']
                if zap_rates:
                    mean_rate = np.mean(zap_rates)
                    std_rate = np.std(zap_rates)
                    player_name = self.model_to_player[model]
                    zap_stats_text.append(f'{player_name}: {mean_rate:.2f}±{std_rate:.2f}')

            zap_stats_str = '\n'.join(zap_stats_text)

            # Position statistics panel - top right for middle subplot when 3 conditions
            if num_conditions == 3 and cond_idx == 1:  # Middle subplot
                ax_zap.text(0.97, 0.96, f'Mean ± Std:\n{zap_stats_str}',
                           transform=ax_zap.transAxes, fontsize=30,
                           verticalalignment='top', horizontalalignment='right',
                           bbox=dict(boxstyle='round,pad=0.6', facecolor='white', alpha=0.85))
            else:
                ax_zap.text(0.03, 0.96, f'Mean ± Std:\n{zap_stats_str}',
                           transform=ax_zap.transAxes, fontsize=30,
                           verticalalignment='top', horizontalalignment='left',
                           bbox=dict(boxstyle='round,pad=0.6', facecolor='white', alpha=0.85))

        plt.tight_layout()
        plt.subplots_adjust(wspace=0.08)  # Reduce horizontal spacing between subplots
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        print(f"Multi-condition cleanup behavioral evolution plot saved as {save_path}")

    def create_combined_behavioral_plot(self, data_directory: str, save_path: str = "cleanup_behavioral_evolution.png"):
        """Create 1x2 subplot showing CLEAN and ZAP rate evolution with exact styling from final score plot"""

        # Use the multi-condition function with a single condition
        self.create_multi_condition_behavioral_plot([data_directory], ["Cleanup Baseline"], save_path)

def main():
    """Main function to create Cleanup behavioral evolution plots"""
    print("=== Creating Cleanup Behavioral Evolution Plot ===")

    # Ask user whether to analyze single condition or multiple conditions
    print("\nChoose analysis type:")
    print("1. Single condition analysis")
    print("2. Multi-condition analysis (up to 3 conditions)")

    choice = input("Enter choice (1 or 2): ").strip()

    plotter = CleanupBehavioralEvolution()

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

        plotter.create_combined_behavioral_plot(data_directory)
        print("\n" + "="*50)
        print("Cleanup behavioral evolution plot complete!")
        print("📁 Generated: cleanup_behavioral_evolution.png")

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
                "path_template": "/project/6101774/xijiez/Collusion_Cleanup/cleanup_llm/runs/base_20/game_record"
            },
            "2": {
                "name": "Cleanup Secret Comm",
                "path_template": "/project/6101774/xijiez/Collusion_Cleanup/cleanup_llm/runs/secret_comm_20_{}/game_record"
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
        plotter.create_multi_condition_behavioral_plot(data_directories, condition_names)

        print("\n" + "="*50)
        print("Multi-condition cleanup behavioral evolution plot complete!")
        print("📁 Generated: cleanup_behavioral_evolution_multi.png")

    else:
        print("Invalid choice. Please run again and select 1 or 2.")

if __name__ == "__main__":
    main()