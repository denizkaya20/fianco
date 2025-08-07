# Fianco - 2D Strategy Board Game with AI

**Fianco** is a turn-based strategy board game implemented using Python and Pygame. It features a 9x9 board, unique movement and capture rules, and supports both Human vs Human and Human vs AI gameplay modes.

## Game Rules

- **Board Size**: 9x9 grid.
- **Players**: Player1 (White) and Player2 (Black).
- **Moves**:
  - Forward movement
  - Sideways movement
  - Capture by jumping over an opponent piece (mandatory if possible)
- **Winning Conditions**:
  - Reach the opponent's base row.
  - Eliminate all opponent pieces.
- **Timers**: Each player has a 10-minute timer (600 seconds).

## AI Features

- **Negamax algorithm** with Alpha-Beta pruning.
- **Zobrist hashing** for board state hashing.
- **Transposition table** to avoid redundant calculations.
- **Move ordering** to prioritize captures.
- **Time management** to control AI decision speed.

## Project Structure

```
├── ai.py              # AI logic and search algorithm (Negamax + pruning)
├── board.py           # Board constants and piece logic
├── check.py           # Human vs Human mode (for testing)
├── fianco.py          # Core game engine with AI support
├── main.py            # Game launcher (Human vs AI)
├── ui.py              # Button and UI interaction system
```

## Installation

### Requirements

- Python 3.8+
- Pygame
- Numpy

### Install Dependencies

```bash
pip install pygame numpy
```

## How to Run

### Play against AI

```bash
python main.py
```

### Play Human vs Human

```bash
python check.py
```

## Controls

- Click to select a piece.
- Click again to move to a valid tile.
- Errors (e.g. invalid moves, mandatory capture) are displayed in-game.
- Use the main menu to choose your side (White or Black).

## AI Statistics

After the game, AI-related stats are printed to the console:

- Total prune count
- Maximum prunes in a single move
- Transposition table size
- Table access count

## Developer Notes

- `ai.py` uses a fixed search depth (5), but it's easily configurable.
- The `fianco.py` engine manages AI moves, error handling, and transitions.
- Zobrist keys are generated at runtime for hashing game states efficiently.
- `check.py` is a simplified version to test the game in human vs human mode.

## Screenshots

> Add in-game screenshots here if desired.

## Author

This project is a showcase of AI and game logic integration in Python.

---

🎯 Enjoy the game and feel free to contribute!
