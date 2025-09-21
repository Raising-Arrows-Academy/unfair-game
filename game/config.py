"""
Configuration management for the Unfair Review Game.

This module handles loading, saving, and editing game configuration including:
- Wheel options and their weights
- Team settings
- Game rules and limits
"""

import json
import os
from typing import Dict, List, Any


class GameConfig:
    """
    Manages game configuration with sensible defaults and validation.

    Handles loading/saving configuration from JSON files and provides
    methods to update configuration values.
    """

    def __init__(self, config_file: str = "config.json"):
        """
        Initialize GameConfig with optional config file path.

        Args:
            config_file: Path to JSON configuration file
        """
        self.config_file = config_file
        self.config = self._get_default_config()
        self.load_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """
        Return default configuration with sensible game settings.

        Returns:
            Dictionary containing default configuration
        """
        return {
            "wheel_options": [
                {"label": "+5 points", "action": "add_fixed:5", "weight": 3},
                {"label": "+10 points", "action": "add_fixed:10", "weight": 2},
                {"label": "+15 points", "action": "add_fixed:15", "weight": 1},
                {"label": "-5 points", "action": "add_fixed:-5", "weight": 2},
                {"label": "-10 points", "action": "add_fixed:-10", "weight": 1},
                {"label": "Steal 5", "action": "steal:5", "weight": 2},
                {"label": "Steal 10", "action": "steal:10", "weight": 1},
                {"label": "Share +5 to all", "action": "share_all:5", "weight": 2},
                {"label": "Swap scores", "action": "swap_random", "weight": 1},
                {"label": "Double your score", "action": "multiply:2", "weight": 1}
            ],
            "teams": ["Red", "Blue"],
            "starting_points": 10,
            "max_points": 0,  # 0 means no maximum
            "max_rounds": 20,
            "starting_round": 1
        }

    def load_config(self) -> None:
        """
        Load configuration from file, creating default if file doesn't exist.
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    self.config.update(loaded_config)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config file: {e}")
                print("Using default configuration.")
        else:
            # Create default config file
            self.save_config()

    def save_config(self) -> None:
        """
        Save current configuration to file.
        """
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except IOError as e:
            print(f"Error saving config file: {e}")

    def get_config(self) -> Dict[str, Any]:
        """
        Get current configuration.

        Returns:
            Dictionary containing current configuration
        """
        return self.config.copy()

    def get_wheel_options(self) -> List[Dict[str, Any]]:
        """Get wheel options configuration."""
        return self.config["wheel_options"]

    def get_teams(self) -> List[str]:
        """Get list of team names."""
        return self.config["teams"]

    def get_starting_points(self) -> int:
        """Get starting points for teams."""
        return self.config["starting_points"]

    def get_max_points(self) -> int:
        """Get maximum points (0 means no limit)."""
        return self.config["max_points"]

    def get_max_rounds(self) -> int:
        """Get maximum number of rounds."""
        return self.config["max_rounds"]

    def get_starting_round(self) -> int:
        """Get starting round number."""
        return self.config["starting_round"]

    def update_teams(self, teams: List[str]) -> None:
        """
        Update team list.

        Args:
            teams: List of team names
        """
        if not teams or len(teams) < 2:
            raise ValueError("Must have at least 2 teams")
        self.config["teams"] = teams
        self.save_config()

    def update_starting_points(self, points: int) -> None:
        """
        Update starting points for teams.

        Args:
            points: Starting points (must be >= 0)
        """
        if points < 0:
            raise ValueError("Starting points must be >= 0")
        self.config["starting_points"] = points
        self.save_config()

    def update_max_points(self, points: int) -> None:
        """
        Update maximum points.

        Args:
            points: Maximum points (0 means no limit, must be >= 0)
        """
        if points < 0:
            raise ValueError("Maximum points must be >= 0")
        self.config["max_points"] = points
        self.save_config()

    def update_max_rounds(self, rounds: int) -> None:
        """
        Update maximum number of rounds.

        Args:
            rounds: Maximum rounds (must be > 0)
        """
        if rounds <= 0:
            raise ValueError("Maximum rounds must be > 0")
        self.config["max_rounds"] = rounds
        self.save_config()

    def update_starting_round(self, round_num: int) -> None:
        """
        Update starting round number.

        Args:
            round_num: Starting round (must be > 0)
        """
        if round_num <= 0:
            raise ValueError("Starting round must be > 0")
        self.config["starting_round"] = round_num
        self.save_config()

    def update_wheel_options(self, wheel_options: List[Dict[str, Any]]) -> None:
        """
        Update wheel options.

        Args:
            wheel_options: List of wheel option dictionaries
        """
        if not wheel_options or len(wheel_options) == 0:
            raise ValueError("Must have at least one wheel option")

        # Validate wheel options structure
        for option in wheel_options:
            required_keys = ["label", "action", "weight"]
            if not all(key in option for key in required_keys):
                msg = "Each wheel option must have 'label', 'action', and 'weight'"
                raise ValueError(msg)
            if option["weight"] <= 0:
                raise ValueError("Wheel option weights must be > 0")

        self.config["wheel_options"] = wheel_options
        self.save_config()

    def display_config(self) -> str:
        """
        Return a formatted string displaying current configuration.

        Returns:
            Formatted configuration string
        """
        lines = []
        lines.append("=== Current Game Configuration ===")
        lines.append("")

        lines.append(f"Teams: {', '.join(self.get_teams())}")
        lines.append(f"Starting Points: {self.get_starting_points()}")
        max_pts = self.get_max_points()
        lines.append(f"Maximum Points: {'No limit' if max_pts == 0 else max_pts}")
        lines.append(f"Maximum Rounds: {self.get_max_rounds()}")
        lines.append(f"Starting Round: {self.get_starting_round()}")
        lines.append("")

        lines.append("Wheel Options:")
        for i, option in enumerate(self.get_wheel_options(), 1):
            lines.append(f"  {i:2d}. {option['label']} (weight: {option['weight']})")

        return "\n".join(lines)


def load_config(config_file: str = "config.json") -> GameConfig:
    """
    Load game configuration from file.

    Args:
        config_file: Path to configuration file

    Returns:
        GameConfig instance
    """
    return GameConfig(config_file)
