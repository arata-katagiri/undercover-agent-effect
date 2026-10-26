import os
import json

def convert_game_record_to_chinese_text(json_file_path):
    """Convert game records to readable English text format"""
    with open(json_file_path, 'r', encoding='utf-8') as f:
        game_data = json.load(f)

    game_id = game_data["game_id"]
    player_names = game_data["player_names"]
    rounds = game_data["rounds"]
    winner = game_data.get("winner", "Game still in progress")
    final_scores = game_data.get("final_scores", {})

    # Introduction
    text = f"Game ID: {game_id}\n"
    text += f"Players: {', '.join(player_names)}\n\n"
    
    # Display initial scores
    text += "Initial Scores:\n"
    for player in player_names:
        text += f"{player}: 0 points\n"
    text += "\n"
        
    text += "════════════════════════════\n"
    text += "         GAME START\n"
    text += "════════════════════════════\n\n"

    for round_record in rounds:
        # Separator for each round
        text += "────────────────────────────\n"
        text += f"Round {round_record['round_id']}\n"
        text += "────────────────────────────\n"
        text += f"Players this round: {', '.join(round_record['round_players'])}\n"
        text += f"Starting with: {round_record['starting_player']}\n\n"
        
        # Display current round scores
        if "player_scores" in round_record:
            text += "Current Scores:\n"
            for player, score in round_record["player_scores"].items():
                text += f"{player}: {score} points\n"
            text += "\n"

        # Record player opinions
        active_players = round_record["round_players"]
        for player_name, opinions in round_record["player_opinions"].items():
            # Only show opinions of players in this round
            if player_name in active_players:
                text += f"{player_name}'s impressions of other players:\n"
                for other_player, opinion in opinions.items():
                    if other_player in active_players:
                        text += f"  - {other_player}: {opinion}\n"
                text += "\n"
            
        text += "Dealing cards...\n\n"
        text += f"Target card for this round: {round_record['target_card']}\n"

        # Add player initial states
        if "player_initial_states" in round_record:
            text += "Players' initial states:\n"
            for player_state in round_record["player_initial_states"]:
                player_name = player_state["player_name"]
                bullet_pos = player_state["bullet_position"]
                gun_pos = player_state["current_gun_position"]
                initial_hand = ", ".join(player_state["initial_hand"])
                
                text += f"{player_name}:\n"
                text += f"  - Bullet position: {bullet_pos}\n"
                text += f"  - Current chamber position: {gun_pos}\n"
                text += f"  - Initial hand: {initial_hand}\n\n"

        text += "----------------------------------\n"
        for action in round_record["play_history"]:
            # Get player behavior from JSON
            text += f"{action['player_name']}'s turn to play\n"
            text += f"{action['player_name']} {action['behavior']}\n"
            # Display cards played and remaining hand
            text += f"Played: {', '.join(action['played_cards'])}, Remaining hand: {', '.join(action['remaining_cards'])} (Target card: {round_record['target_card']})\n"
            text += f"Reason for play: {action['play_reason']}\n\n"

            # Show challenge information
            if action['was_challenged']:
                text += f"{action['next_player']} chose to challenge\n"
                text += f"Reason for challenge: {action['challenge_reason']}\n"
            else:
                text += f"{action['next_player']} chose not to challenge\n"
                text += f"Reason for not challenging: {action['challenge_reason']}\n"

            # Challenge result
            if action['was_challenged']:
                if action['challenge_result']:
                    text += f"Challenge successful, {action['player_name']} was caught bluffing.\n"
                else:
                    text += f"Challenge failed, {action['next_player']} must face penalty.\n"
            text += "\n----------------------------------\n"

        # Record shooting result
        if round_record['round_result']:
            result = round_record['round_result']
            text += f"Shooting result:\n"

            if result["bullet_hit"]:
                text += f"Bullet hit, {result['shooter_name']} has died.\n"
            else:
                text += f"Bullet missed, {result['shooter_name']} survived.\n"

            # Display score updates after shooting
            if "player_scores" in round_record:
                text += "\nScore update:\n"
                for player, score in round_record["player_scores"].items():
                    text += f"{player}: {score} points\n"

            text += "\n"

    # Game end separator and winner announcement
    text += "\n════════════════════════════\n"
    text += "         GAME OVER\n"
    text += "════════════════════════════\n\n"
    
    # Display final scores
    text += "Final Scores:\n"
    for player, score in final_scores.items():
        text += f"{player}: {score} points\n"
    text += "\n"
    
    # Highlight the winner
    text += "★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★\n"
    text += f"    WINNER: {winner}\n"
    text += "★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★\n"
    
    return text

def process_game_records(input_directory, output_directory):
    """Process all game record JSON files in the directory and generate readable text files"""
    # Ensure output directory exists
    os.makedirs(output_directory, exist_ok=True)
    
    for filename in os.listdir(input_directory):
        if filename.endswith('.json'):
            json_file_path = os.path.join(input_directory, filename)
            txt_file_path = os.path.join(output_directory, os.path.splitext(filename)[0] + '.txt')

            print(f"Processing {filename}...")
            game_text = convert_game_record_to_chinese_text(json_file_path)

            with open(txt_file_path, 'w', encoding='utf-8') as txt_file:
                txt_file.write(game_text)
            print(f"Generated: {txt_file_path}")

if __name__ == '__main__':
    game_records_directory = 'game_records'
    output_directory = 'converted_game_records'  # New output directory
    process_game_records(game_records_directory, output_directory)