# Unfair Review Game 🎯

An interactive CLI-based review game for classrooms where teams compete through a "wheel of fortune" style system. Perfect for making review sessions fun and engaging!

## Quick Start

### Installation
1. Make sure you have Python 3.10+ installed
2. Clone this repository
3. Set up the virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

### Basic Usage

#### Start a New Game
```bash
python main.py start Red Blue Green
```
This creates a new game with three teams: Red, Blue, and Green.

#### Spin the Wheel
```bash
python main.py spin
```
The current team spins the wheel and sees their outcome!

#### Interactive Mode (Recommended)
```bash
python main.py interactive
```
This starts a full interactive session where you can:
- Spin the wheel repeatedly
- See live scores
- Navigate through turns automatically
- Save and load games

#### Simple Mode (Quick Play)
```bash
python main.py simple
```
A streamlined mode perfect for fast-paced classroom sessions:
- Clean, minimal display
- Just press Enter to spin
- Automatic team rotation
- Less visual clutter
- Use `--verbose` flag for detailed outcomes

#### Auto-Spin Mode (Hands-Free)
```bash
python main.py auto-spin
```
Continuous spinning with automatic progression:
- No manual input needed
- Configurable delay between spins
- Auto-saves progress
- Perfect for demonstrations

## Example Game Session

```bash
# Start a new game with random starting team
python main.py start Wolves Eagles Dragons --random-start

# Output:
# Random starting team selected: Eagles
# New game started with teams: Wolves, Eagles, Dragons
# Starting points: 10
# Current team: Eagles

# Spin the wheel
python main.py spin

# Output:
# Eagles is spinning the wheel...
# 🎯 Steal 5
# 📝 Eagles steals 5 points from Wolves!
# 
# 📊 Score Changes:
#    Eagles: +5
#    Wolves: -5
# 
# 🏆 Current Scores:
# 👑 Eagles: 15
#    Dragons: 10
#    Wolves: 5
# 
# Next turn: Dragons
```

## Game Features

### Wheel Outcomes
- **Points**: Gain or lose fixed points (+5, +10, -5, etc.)
- **Steal**: Take points from another team
- **Share**: Give points to all teams
- **Multiply/Divide**: Double or halve your score
- **Swap**: Exchange scores with another team
- **Wildcard**: Teacher's choice (mini-challenge)

### Special Rules
- **Rubber-band Effect**: Teams at 0 points gain points instead of losing them
- **Score Protection**: Scores never go below 0
- **Turn Management**: Automatic progression or manual team selection

## Commands Reference

| Command | Description |
|---------|-------------|
| `python main.py start Team1 Team2 ...` | Start new game with teams |
| `python main.py spin [TeamName]` | Spin wheel (current team or specific team) |
| `python main.py interactive` | Start interactive game session |
| `python main.py simple` | Start simple mode (minimal display) |
| `python main.py simple --verbose` | Simple mode with detailed outcomes |
| `python main.py auto-spin` | Auto-spin mode (hands-free) |
| `python main.py status` | Show current game state |
| `python main.py config show` | Display current settings |
| `python main.py config edit` | Modify game configuration |
| `python main.py load filename.json` | Load a saved game |
| `python main.py --help` | Show all available options |

## Configuration

The game uses sensible defaults but can be customized:
- Starting points per team
- Maximum points (game end condition)
- Maximum rounds (game end condition)
- Wheel outcomes and their probabilities

Use `python main.py config edit` to modify these settings interactively.

## Perfect for Classrooms

This game is designed specifically for educational environments:
- **Quick Setup**: Start a game in seconds
- **Flexible Teams**: Support for any number of teams
- **Engaging**: Students love the unpredictability
- **Educational**: Great for any subject's review content
- **No Prep**: No materials needed beyond a computer/projector

Enjoy your review sessions! 🎉