# RPS+ AI Referee: Technical Overview

## 1. State Model
The game state is encapsulated in a dedicated `GameState` class to ensure consistency and isolate logic from the interface.
*   **Core Attributes**: 
    *   `round_count` (int): Tracks progress (max 3 rounds).
    *   `user_score`, `bot_score` (int): Tracks the score.
    *   `user_bomb_used`, `bot_bomb_used` (bool): A strict flag ensures the "Bomb" power-up is one-time use only.
    *   `game_over` (bool): Terminal state flag.
*   **State Transitions**: State is mutated exclusively through deterministic functions (`play_round`), ensuring that the Agent cannot hallucinate the score or rules.

## 2. Agent & Tool Design
The system uses a **Pattern-Separated Architecture**:
*   **The Agent (Persona & interface)**: The LLM (Gemini) acts as the "Referee". Its role is purely conversational—welcoming the user, explaining invalid inputs, and announcing results with personality.
*   **The Tool (Deterministic Logic)**: The `play_turn` function is the source of truth.
    *   **Agent Responsibility**: Identify the user's move intent ("I throw rock", "rock", "use bomb").
    *   **Tool Responsibility**: Validate the move (e.g., check if bomb was already used), calculate the winner, and return the structured result.
    *   **Data Flow**: User Input -> LLM -> `play_turn` Tool -> LLM -> Final Response.

## 3. Tradeoffs
*   **Deterministic vs. Generative Rules**: I chose to hardcode game rules (Rock beats Scissors) in Python rather than letting the LLM decide. **Tradeoff**: Less "creative" flexibility for house rules, but guarantees 100% fairness and prevents hallucinations.
*   **In-Memory State**: State is held in a Python object instance. **Tradeoff**: Very fast and simple to implement, but state is lost if the script crashes or restarts. It does not persist across different sessions.
*   **Synchronous Tool Execution**: The Agent waits for the tool to complete. **Tradeoff**: Simplifies the control flow logic but could block the UI if the logic was computationally heavy (not an issue for RPS).

## 4. Future Improvements
*   **State Persistence**: Implement a lightweight database (SQLite) or Redis to allow users to pause and resume games later, or track lifetime stats.
*   **Dynamic Difficulty**: Instead of a random bot backend, implement a Markov Chain or simple ML model to predict player moves and increase difficulty.

