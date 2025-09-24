"""
Game state management for the Unfair Review Game.

This module handles the current state of an active game including:
- Team scores and turn tracking
- Round progression
- Event history for each round
- Game persistence and recovery
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class GameEvent:
    """
    Represents a single event that occurred during the game.

    Attributes:
        timestamp: When the event occurred
        round_number: Which round this event happened in
        team: Team that triggered the event
        action: What action was performed
        description: Human-readable description of what happened
        score_changes: Dictionary of team -> score change
    """
    timestamp: str
    round_number: int
    team: str
    action: str
    description: str
    score_changes: Dict[str, int]


class GameState:
    """
    Manages the current state of an active game.

    Handles team scores, round progression, turn tracking, event history,
    and persistence to allow game recovery after crashes.
    """

    def __init__(self, teams: List[str], starting_points: int = 10,
                 starting_round: int = 1,
                 state_file: str = "game_state.json"):
        """
        Initialize a new game state.

        Args:
            teams: List of team names
            starting_points: Initial points for each team
            starting_round: Starting round number
            state_file: Path to save game state
        """
        self.state_file = state_file
        self.teams = teams
        self.scores = {team: starting_points for team in teams}
        self.current_round = starting_round
        self.current_turn_index = 0  # Index into teams list
        self.events: List[GameEvent] = []
        self.game_started = datetime.now().isoformat()
        self.last_updated = self.game_started

        # Save initial state
        self.save_state()

    def get_current_team(self) -> str:
        """
        Get the team whose turn it currently is.

        Returns:
            Name of the current team
        """
        return self.teams[self.current_turn_index]

    def get_teams(self) -> List[str]:
        """
        Get list of all team names.

        Returns:
            List of team names
        """
        return self.teams.copy()

    def set_current_team(self, team_name: str) -> None:
        """
        Set the current team (for starting team selection).

        Args:
            team_name: Name of the team to set as current

        Raises:
            ValueError: If team name is not valid
        """
        if team_name not in self.teams:
            raise ValueError(f"Team '{team_name}' not found in game")

        self.current_turn_index = self.teams.index(team_name)
        self.add_event("team_changed", f"Current team set to {team_name}")
        self.save_state()

    def get_scores(self) -> Dict[str, int]:
        """
        Get current scores for all teams.

        Returns:
            Dictionary mapping team names to scores
        """
        return self.scores.copy()

    def get_current_round(self) -> int:
        """Get the current round number."""
        return self.current_round

    def get_round_events(self, round_number: Optional[int] = None) -> List[GameEvent]:
        """
        Get events for a specific round.

        Args:
            round_number: Round to get events for (current round if None)

        Returns:
            List of events for the specified round
        """
        if round_number is None:
            round_number = self.current_round

        return [event for event in self.events if event.round_number == round_number]

    def update_scores(self, score_changes: Dict[str, int], team: str,
                      action: str, description: str) -> None:
        """
        Update team scores and record the event.

        Args:
            score_changes: Dictionary of team -> score change
            team: Team that triggered the action
            action: Action identifier
            description: Human-readable description
        """
        # Apply score changes
        for team_name, change in score_changes.items():
            if team_name in self.scores:
                self.scores[team_name] += change
                # Ensure scores don't go below 0
                self.scores[team_name] = max(0, self.scores[team_name])

        # Record the event
        event = GameEvent(
            timestamp=datetime.now().isoformat(),
            round_number=self.current_round,
            team=team,
            action=action,
            description=description,
            score_changes=score_changes
        )
        self.events.append(event)

        # Update timestamp and save
        self.last_updated = datetime.now().isoformat()
        self.save_state()

    def add_event(self, action: str, description: str, team: str = "",
                  score_changes: Optional[Dict[str, int]] = None) -> None:
        """
        Add a simple event to the game history.

        Args:
            action: Type of action that occurred
            description: Description of what happened
            team: Team involved (optional)
            score_changes: Score changes (optional)
        """
        event = GameEvent(
            timestamp=datetime.now().isoformat(),
            round_number=self.current_round,
            team=team,
            action=action,
            description=description,
            score_changes=score_changes or {}
        )
        self.events.append(event)
        self.last_updated = datetime.now().isoformat()
        self.save_state()

    def next_turn(self) -> str:
        """
        Advance to the next team's turn.

        Returns:
            Name of the team whose turn it now is
        """
        # Advance to next team
        self.current_turn_index = (self.current_turn_index + 1) % len(self.teams)

        self.last_updated = datetime.now().isoformat()
        self.save_state()
        return self.get_current_team()

    def next_round(self) -> int:
        """
        Advance to the next round and reset turn to first team.

        Returns:
            New current round number
        """
        self.current_round += 1
        self.current_turn_index = 0
        self.last_updated = datetime.now().isoformat()
        self.save_state()
        return self.current_round

    def get_game_summary(self) -> str:
        """
        Get a formatted summary of the current game state.

        Returns:
            Formatted string with game information
        """
        lines = []
        lines.append("=== Current Game State ===")
        lines.append(f"Round: {self.current_round}")
        lines.append(f"Current Turn: {self.get_current_team()}")
        lines.append("")

        # Scores
        lines.append("Scores:")
        sorted_teams = sorted(self.scores.items(), key=lambda x: x[1], reverse=True)
        for i, (team, score) in enumerate(sorted_teams, 1):
            marker = " <-- Current turn" if team == self.get_current_team() else ""
            lines.append(f"  {i}. {team}: {score} points{marker}")

        lines.append("")
        lines.append(f"Total Events: {len(self.events)}")
        lines.append(f"Events This Round: {len(self.get_round_events())}")

        return "\n".join(lines)

    def get_round_history(self, round_number: Optional[int] = None) -> str:
        """
        Get formatted history for a specific round.

        Args:
            round_number: Round to show history for (current if None)

        Returns:
            Formatted string with round events
        """
        if round_number is None:
            round_number = self.current_round

        events = self.get_round_events(round_number)

        lines = []
        lines.append(f"=== Round {round_number} History ===")

        if not events:
            lines.append("No events yet this round.")
        else:
            for i, event in enumerate(events, 1):
                time = datetime.fromisoformat(event.timestamp).strftime("%H:%M:%S")
                lines.append(f"{i:2d}. [{time}] {event.team}: {event.description}")

        return "\n".join(lines)

    def save_state(self) -> None:
        """Save current game state to file."""
        state_data = {
            "teams": self.teams,
            "scores": self.scores,
            "current_round": self.current_round,
            "current_turn_index": self.current_turn_index,
            "game_started": self.game_started,
            "last_updated": self.last_updated,
            "events": [asdict(event) for event in self.events]
        }

        try:
            with open(self.state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
        except IOError as e:
            print(f"Error saving game state: {e}")

    @classmethod
    def load_state(cls, state_file: str = "game_state.json") -> Optional['GameState']:
        """
        Load a previously saved game state.

        Args:
            state_file: Path to the saved state file

        Returns:
            GameState instance if successful, None if file doesn't exist or is invalid
        """
        if not os.path.exists(state_file):
            return None

        try:
            with open(state_file, 'r') as f:
                state_data = json.load(f)

            # Create new instance
            game_state = cls.__new__(cls)
            game_state.state_file = state_file
            game_state.teams = state_data["teams"]
            game_state.scores = state_data["scores"]
            game_state.current_round = state_data["current_round"]
            game_state.current_turn_index = state_data["current_turn_index"]
            game_state.game_started = state_data["game_started"]
            game_state.last_updated = state_data["last_updated"]

            # Reconstruct events
            game_state.events = [
                GameEvent(**event_data)
                for event_data in state_data["events"]
            ]

            return game_state

        except (json.JSONDecodeError, KeyError, IOError) as e:
            print(f"Error loading game state: {e}")
            return None

    def delete_save_file(self) -> None:
        """Delete the saved game state file."""
        try:
            if os.path.exists(self.state_file):
                os.unlink(self.state_file)
        except IOError as e:
            print(f"Error deleting save file: {e}")


def has_saved_game(state_file: str = "game_state.json") -> bool:
    """
    Check if a saved game exists.

    Args:
        state_file: Path to check for saved game

    Returns:
        True if saved game exists and is valid
    """
    if not os.path.exists(state_file):
        return False

    try:
        with open(state_file, 'r') as f:
            state_data = json.load(f)
        # Check for required keys
        required_keys = ["teams", "scores", "current_round"]
        return all(key in state_data for key in required_keys)
    except (json.JSONDecodeError, IOError):
        return False


def create_new_game(teams: List[str], starting_points: int = 10,
                    starting_round: int = 1,
                    state_file: str = "game_state.json") -> GameState:
    """
    Create a new game state.

    Args:
        teams: List of team names
        starting_points: Initial points for each team
        starting_round: Starting round number
        state_file: Path to save game state

    Returns:
        New GameState instance
    """
    return GameState(teams, starting_points, starting_round, state_file)


def load_saved_game(state_file: str = "game_state.json") -> Optional[GameState]:
    """
    Load a saved game.

    Args:
        state_file: Path to saved game file

    Returns:
        GameState instance if successful, None otherwise
    """
    return GameState.load_state(state_file)
