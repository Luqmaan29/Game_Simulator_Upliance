# AI Referee for Rock-Paper-Scissors-Plus

A minimal, stateful AI Referee that manages a "Rock-Paper-Scissors-Plus" game using the Google GenAI SDK.

## Features
- **Strict Rules Enforcement**: Validates moves (rock, paper, scissors) and the special "Bomb" rule (once per game).
- **State Persistence**: Tracks scores, round counts, and bomb usage across turns using a dedicated `GameState` class.
- **Robust Error Handling**: Invalid moves or bomb re-use "waste" the round (User loses the round), ensuring the game progresses.
- **Agentic Design**: Separation of concerns between:
    - **Intent Understanding** (LLM)
    - **Game Logic** (Deterministic Python Tool)
    - **Response Generation** (LLM Referee Persona)

## Architecture

The application defines a clear boundary between the LLM and the Game Engine.

1.  **User Input**: The user chats with the AI Referee.
2.  **Intent**: The AI identifies the move (e.g., "I choose rock") and calls the `play_turn` tool.
3.  **Engine**: The `GameState` class:
    - Validates the move.
    - Resolves the round (Win/Loss/Draw/Wasted).
    - Updates scores and round counters.
    - Returns a structured JSON result.
4.  **Response**: The AI interprets the JSON result and narrates the outcome (e.g., "You played Rock, I played Scissors. You win this round!").

## State Model

The state is managed in-memory via the `GameState` class:

- `round_count`: 0-3 (Game ends at 3).
- `scores`: User vs Bot.
- `bomb_used`: Boolean flags to enforce the "once per game" constraint.
- `history`: Log of moves (extensible for future analytics).

## Setup & Usage

### Prerequisites
- Python 3.9+
- `google-genai` SDK
- A valid `GOOGLE_API_KEY`

### Installation
```bash
pip install google-genai
export GOOGLE_API_KEY="your_api_key_here"
```

### Running the Game
```bash
python rps_referee.py
```

## Trade-offs & Future Improvements (What I'd do with more time)

- **Input Handling**: Currently, the logic for "wasting" a round is strict. A more forgiving UX might warn the user once before penalizing.
- **Persistence**: State is currently in-memory (RAM). For a production app, I would use a lightweight DB (SQLite/Redis) keyed by `session_id` to support concurrent users.
- **Tooling**: The current loop inspects tool calls manually for maximum control. With more time, I would leverage the SDK's automatic function calling features more deeply if they support local execution contexts seamlessly.
