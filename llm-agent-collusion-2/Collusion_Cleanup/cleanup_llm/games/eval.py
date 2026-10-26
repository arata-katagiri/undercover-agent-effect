"""Simple evaluation and plotting of tournament results."""
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from pathlib import Path

def plot_cumulative_scores(csv_path: str, output_dir: str = None):
    """Plot cumulative scores over time."""
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        return

    # Load data
    df = pd.read_csv(csv_path)

    # Create figure
    plt.figure(figsize=(12, 8))

    # Plot cumulative scores for each agent
    for agent_id in range(4):
        col_name = f'agent_{agent_id}_score'
        if col_name in df.columns:
            plt.plot(df['game'], df[col_name],
                    label=f'Agent {agent_id}', linewidth=2, marker='o', markersize=4)

    plt.xlabel('Game Number')
    plt.ylabel('Cumulative Score')
    plt.title('Cumulative Scores Across Tournament')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    # Save plot
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, 'cumulative_scores.png')
    else:
        output_path = csv_path.replace('.csv', '_plot.png')

    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Plot saved to: {output_path}")
    plt.show()

def plot_episode_results(csv_path: str, output_dir: str = None):
    """Plot per-episode win rates and score distributions."""
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        return

    # Load data
    df = pd.read_csv(csv_path)

    # Create subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))

    # Win rate by agent
    win_rates = df.groupby('agent_id')['winner'].mean()
    axes[0, 0].bar(range(len(win_rates)), win_rates.values)
    axes[0, 0].set_title('Win Rate by Agent')
    axes[0, 0].set_xlabel('Agent ID')
    axes[0, 0].set_ylabel('Win Rate')
    axes[0, 0].set_xticks(range(len(win_rates)))

    # Score distribution by agent
    for agent_id in range(4):
        agent_scores = df[df['agent_id'] == agent_id]['final_score']
        axes[0, 1].hist(agent_scores, alpha=0.7, label=f'Agent {agent_id}', bins=20)
    axes[0, 1].set_title('Score Distribution by Agent')
    axes[0, 1].set_xlabel('Final Score')
    axes[0, 1].set_ylabel('Frequency')
    axes[0, 1].legend()

    # Average score by agent
    avg_scores = df.groupby('agent_id')['final_score'].mean()
    axes[1, 0].bar(range(len(avg_scores)), avg_scores.values)
    axes[1, 0].set_title('Average Score by Agent')
    axes[1, 0].set_xlabel('Agent ID')
    axes[1, 0].set_ylabel('Average Score')
    axes[1, 0].set_xticks(range(len(avg_scores)))

    # Pollution levels over time
    if 'total_pollution' in df.columns:
        pollution_by_game = df.groupby('game')['total_pollution'].first()
        axes[1, 1].plot(pollution_by_game.index, pollution_by_game.values, 'r-', linewidth=2)
        axes[1, 1].set_title('Pollution Levels by Game')
        axes[1, 1].set_xlabel('Game Number')
        axes[1, 1].set_ylabel('Total Pollution')

    plt.tight_layout()

    # Save plot
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, 'episode_analysis.png')
    else:
        output_path = csv_path.replace('.csv', '_analysis.png')

    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Analysis plot saved to: {output_path}")
    plt.show()

def main():
    parser = argparse.ArgumentParser(description="Evaluate tournament results")
    parser.add_argument("--cumulative", type=str, help="Path to cumulative_scores.csv")
    parser.add_argument("--episodes", type=str, help="Path to episodes.csv")
    parser.add_argument("--output", type=str, help="Output directory for plots")

    args = parser.parse_args()

    if args.cumulative:
        plot_cumulative_scores(args.cumulative, args.output)

    if args.episodes:
        plot_episode_results(args.episodes, args.output)

    if not args.cumulative and not args.episodes:
        print("Please provide --cumulative and/or --episodes CSV file paths")

if __name__ == "__main__":
    main()