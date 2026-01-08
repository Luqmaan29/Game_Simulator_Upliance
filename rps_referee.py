import os
import random
import sys
from typing import Dict, Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Environment variables from .env might not be loaded.")

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Error: google-genai package is not installed.")
    print("Please install it using: pip install google-genai")
    sys.exit(1)

# --- Game State & Logic ---

class GameState:
    def __init__(self):
        self.max_rounds = 3
        self.round_count = 0
        self.user_score = 0
        self.bot_score = 0
        self.game_over = False
        self.history = []
        self.user_bomb_used = False
        self.bot_bomb_used = False

    def is_valid_move(self, move: str) -> bool:
        valid_moves = ["rock", "paper", "scissors", "bomb"]
        if move not in valid_moves:
            return False
        if move == "bomb" and self.user_bomb_used:
            return False
        return True

    def get_bot_move(self) -> str:
        choices = ["rock", "paper", "scissors"]
        if not self.bot_bomb_used:
            # 10% chance to use bomb if available
            if random.random() < 0.1:
                return "bomb"
        return random.choice(choices)

    def determine_round_winner(self, user_move: str, bot_move: str) -> str:
        if user_move == bot_move:
            return "draw"
        
        if user_move == "bomb":
            return "user"
        if bot_move == "bomb":
            return "bot"
            
        wins = {
            "rock": "scissors",
            "paper": "rock",
            "scissors": "paper"
        }
        
        if wins[user_move] == bot_move:
            return "user"
        return "bot"

    def play_round(self, user_move: str) -> Dict[str, Any]:
        if self.game_over:
            return {"error": "Game is already over."}

        user_move = user_move.lower().strip()
        
        round_info = {
            "round": self.round_count + 1,
            "user_move": user_move,
            "bot_move": None,
            "round_winner": None,
            "status": "normal"
        }

        # Validate move - Invalid move "wastes" the round
        move_error = None
        if not self.is_valid_move(user_move):
            if user_move == "bomb" and self.user_bomb_used:
                 move_error = "Invalid move: You have already used your Bomb! Round wasted."
            else:
                 valid = "rock, paper, scissors" + (", bomb" if not self.user_bomb_used else "")
                 move_error = f"Invalid move: '{user_move}'. Valid moves: {valid}. Round wasted."
        
        # Increment round count for ALL attempts (valid or invalid)
        self.round_count += 1
        
        if move_error:
            # Wasted round logic
            self.bot_score += 1 # Bot wins by default on wasted round
            round_info["round_winner"] = "bot"
            round_info["status"] = "invalid_move"
            round_info["message"] = move_error
            # Bot doesn't strictly need to move, but we can say it watched the user fail
            round_info["bot_move"] = "N/A"
        else:
            # Valid move logic
            if user_move == "bomb":
                self.user_bomb_used = True
                
            bot_move = self.get_bot_move()
            if bot_move == "bomb":
                self.bot_bomb_used = True
                
            winner = self.determine_round_winner(user_move, bot_move)
            
            if winner == "user":
                self.user_score += 1
            elif winner == "bot":
                self.bot_score += 1
                
            round_info["bot_move"] = bot_move
            round_info["round_winner"] = winner

        # Check game end
        if self.round_count >= self.max_rounds:
            self.game_over = True
            
        result = {
            **round_info,
            "user_score": self.user_score,
            "bot_score": self.bot_score,
            "game_over": self.game_over
        }
        
        if self.game_over:
            if self.user_score > self.bot_score:
                final_result = "User Wins the Game!"
            elif self.bot_score > self.user_score:
                final_result = "Bot Wins the Game!"
            else:
                final_result = "Game ends in a Draw!"
            result["final_result"] = final_result
            
        return result

# Initialize global state
game_state = GameState()

# --- Tool Definition ---

def play_turn(move: str) -> Dict[str, Any]:
    """
    Plays a single turn of Rock-Paper-Scissors-Plus against the bot.
    
    Args:
        move: The move selected by the user (rock, paper, scissors, or bomb).
        
    Returns:
        A dictionary containing the result of the round, including moves, winner, current scores, and game status.
    """
    return game_state.play_round(move)


# --- Main Application Loop ---

def main():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Please set the GOOGLE_API_KEY environment variable.")
        return

    client = genai.Client(api_key=api_key)
    
    system_instruction = """
    You are the AI Referee for a Rock-Paper-Scissors-Plus game.
    
    Game Rules:
    1. Best of 3 rounds.
    2. Moves: rock, paper, scissors, bomb.
    3. Bomb beats everything but can only be used ONCE per player per game.
    4. Bomb vs Bomb is a draw.
    
    Your Logic:
    1. Start by welcoming the user and briefly explaining the rules (<= 5 lines).
    2. Ask the user for their move.
    3. When the user provides a move, YOU MUST call the `play_turn` tool. Do not resolve the round yourself.
    4. Based on the tool output:
       - Report the Bot's move (or N/A if round wasted).
       - Declare the Round Winner.
       - Show the current Score.
    5. If the tool reports `game_over`, announce the final winner and say goodbye.
    6. If the tool reports `status` == "invalid_move", explain that the round was wasted due to invalid input.
    
    Persona:
    - Neutral, fair, efficient.
    - Focus on the game state.
    """
    
    tools = [play_turn]
    
    print("--- Starting AI Referee ---")
    
    chat = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=tools,
            temperature=0.7,
        )
    )

    # Allow the model to start the conversation (welcome message)
    response = chat.send_message("The game has started. Introduce yourself and the rules.")
    print(f"\nReferee: {response.text}")

    while not game_state.game_over:
        try:
            user_input = input("\n> ")
            if user_input.lower() in ["exit", "quit"]:
                break
                
            response = chat.send_message(user_input)
            
            # Check for tool calls

            
            for part in response.candidates[0].content.parts:
                if part.function_call:
                    fc = part.function_call
                    if fc.name == "play_turn":
                        # Execute logic
                        move_arg = fc.args.get("move")
                        result = play_turn(move_arg)
                        
                        # Send result back
                        response = chat.send_message(
                            types.Part.from_function_response(
                                name="play_turn",
                                response={"result": result}
                            )
                        )
                        # Print final response from model after tool
                        if response.text:
                             print(f"\nReferee: {response.text}")
                        break # Assume one tool call per turn for this game logic
            
            if response.text and not any(p.function_call for p in response.candidates[0].content.parts):
                 print(f"\nReferee: {response.text}")

        except Exception as e:
            print(f"An error occurred: {e}")
            break

if __name__ == "__main__":
    main()
