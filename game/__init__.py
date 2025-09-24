"""
Game package for the Unfair Review Game.

This package contains all the core game logic and functionality:
- config.py: Configuration management
- state.py: Game state and persistence
- wheel.py: Wheel mechanics
- interactive.py: Interactive menu system
"""

from .config import GameConfig
from .state import GameState, GameEvent, create_new_game, load_saved_game
from .wheel import GameWheel, WheelOutcome, create_wheel, pick_random_starting_team
from .interactive import run_interactive_mode
from .commands import (
    handle_start_command,
    handle_spin_command, 
    handle_load_command,
    handle_config_command,
    handle_status_command
)

__all__ = [
    "GameConfig",
    "GameState", 
    "GameEvent",
    "GameWheel",
    "WheelOutcome",
    "create_new_game",
    "load_saved_game", 
    "create_wheel",
    "pick_random_starting_team",
    "run_interactive_mode",
    "handle_start_command",
    "handle_spin_command", 
    "handle_load_command",
    "handle_config_command",
    "handle_status_command",
]
