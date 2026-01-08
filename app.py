import streamlit as st
import os
import random
from typing import Dict, Any
from google import genai
from google.genai import types

# ---------------- GAME LOGIC ---------------- #

class GameState:
    def __init__(self):
        self.max_rounds = 3
        self.round_count = 0
        self.user_score = 0
        self.bot_score = 0
        self.game_over = False
        self.user_bomb_used = False
        self.bot_bomb_used = False

    def is_valid_move(self, move):
        if move not in ["rock", "paper", "scissors", "bomb"]:
            return False
        if move == "bomb" and self.user_bomb_used:
            return False
        return True

    def get_bot_move(self):
        if not self.bot_bomb_used and random.random() < 0.1:
            return "bomb"
        return random.choice(["rock", "paper", "scissors"])

    def determine_winner(self, user, bot):
        if user == bot:
            return "draw"
        if user == "bomb":
            return "user"
        if bot == "bomb":
            return "bot"

        rules = {
            "rock": "scissors",
            "paper": "rock",
            "scissors": "paper"
        }
        return "user" if rules[user] == bot else "bot"

    def play_round(self, move):
        self.round_count += 1

        if not self.is_valid_move(move):
            self.bot_score += 1
            return {
                "status": "invalid",
                "round": self.round_count,
                "message": "Invalid move — round wasted!"
            }

        if move == "bomb":
            self.user_bomb_used = True

        bot_move = self.get_bot_move()
        if bot_move == "bomb":
            self.bot_bomb_used = True

        winner = self.determine_winner(move, bot_move)
        if winner == "user":
            self.user_score += 1
        elif winner == "bot":
            self.bot_score += 1

        if self.round_count >= self.max_rounds:
            self.game_over = True

        return {
            "status": "ok",
            "round": self.round_count,
            "user_move": move,
            "bot_move": bot_move,
            "winner": winner,
            "user_score": self.user_score,
            "bot_score": self.bot_score,
            "game_over": self.game_over
        }


# ---------------- STREAMLIT APP ---------------- #

st.set_page_config(page_title="RPS+ AI Referee", page_icon="🎮")

st.title("🎮 Rock–Paper–Scissors–Plus")
st.caption("AI Referee | Best of 3 | Bomb usable once")

if "game" not in st.session_state:
    st.session_state.game = GameState()

game = st.session_state.game

st.divider()

st.subheader(f"Round {game.round_count + 1} / 3")

cols = st.columns(4)
moves = ["rock", "paper", "scissors", "bomb"]

for i, move in enumerate(moves):
    disabled = (move == "bomb" and game.user_bomb_used) or game.game_over
    if cols[i].button(move.capitalize(), disabled=disabled):
        result = game.play_round(move)
        st.session_state.last_result = result
        st.rerun()

# ---------------- RESULTS ---------------- #

if "last_result" in st.session_state:
    r = st.session_state.last_result

    st.divider()
    st.subheader("🧾 Round Result")

    if r["status"] == "invalid":
        st.error(r["message"])
    else:
        st.write(f"**You:** {r['user_move']}")
        st.write(f"**Bot:** {r['bot_move']}")
        st.success(f"**Winner:** {r['winner'].capitalize()}")

    st.info(f"Score → You: {game.user_score} | Bot: {game.bot_score}")

if game.game_over:
    st.divider()
    st.subheader("🏁 Final Result")

    if game.user_score > game.bot_score:
        st.success("🎉 You win the game!")
    elif game.bot_score > game.user_score:
        st.error("🤖 Bot wins the game!")
    else:
        st.warning("🤝 It's a draw!")

    if st.button("🔄 Restart Game"):
        st.session_state.clear()
        st.rerun()
