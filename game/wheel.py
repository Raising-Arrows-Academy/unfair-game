"""
Wheel mechanics for the Unfair Review Game.

This module handles the wheel spinning logic, outcome processing, and
integration with game state and configuration.
"""

import random
from typing import Dict, List, Tuple, Optional
from .config import GameConfig
from .state import GameState


class WheelOutcome:
    """
    Represents the result of a wheel spin.

    Attributes:
        label: Human-readable description of the outcome
        action: Action identifier for processing
        weight: Weight used for selection (for reference)
        score_changes: Dictionary of team -> score change
        description: Detailed description of what happened
    """

    def __init__(self, label: str, action: str, weight: int):
        self.label = label
        self.action = action
        self.weight = weight
        self.score_changes: Dict[str, int] = {}
        self.description = ""


class GameWheel:
    """
    Manages wheel spinning and outcome processing.

    Handles random selection from wheel options, processes different types
    of outcomes, and integrates with game state for score updates.
    """

    def __init__(self, config: GameConfig, game_state: GameState):
        """
        Initialize the game wheel.

        Args:
            config: Game configuration with wheel options
            game_state: Current game state for score updates
        """
        self.config = config
        self.game_state = game_state

    def spin_wheel(self) -> WheelOutcome:
        """
        Spin the wheel and return a random outcome.

        Returns:
            WheelOutcome representing the selected option
        """
        wheel_options = self.config.get_wheel_options()

        # Extract labels, actions, and weights
        options = [(opt["label"], opt["action"], opt["weight"]) for opt in wheel_options]
        weights = [opt[2] for opt in options]

        # Randomly select based on weights
        selected = random.choices(options, weights=weights, k=1)[0]

        return WheelOutcome(selected[0], selected[1], selected[2])

    def process_outcome(self, outcome: WheelOutcome, spinning_team: str) -> None:
        """
        Process a wheel outcome and update game state.

        Args:
            outcome: The wheel outcome to process
            spinning_team: Team that spun the wheel
        """
        # Process different types of actions
        if ":" in outcome.action:
            action_type, value = outcome.action.split(":", 1)
            self._process_parameterized_action(outcome, spinning_team, action_type, value)
        else:
            self._process_simple_action(outcome, spinning_team, outcome.action)

        # Update game state with the outcome
        self.game_state.update_scores(
            outcome.score_changes,
            spinning_team,
            outcome.action,
            outcome.description
        )

    def _process_parameterized_action(self, outcome: WheelOutcome, team: str, 
                                    action_type: str, value: str) -> None:
        """Process actions that have parameters (e.g., add_fixed:5)."""
        if action_type == "add_fixed":
            points = int(value)
            # Apply rubber-banding: if team has 0 points and would lose points, give +5 instead
            if self.game_state.get_scores()[team] <= 0 and points < 0:
                points = 5
                outcome.description = f"{team} would lose points but gets +5 instead (rubber-band effect)!"
            else:
                outcome.description = f"{team} {'gains' if points >= 0 else 'loses'} {abs(points)} points!"

            outcome.score_changes[team] = points

        elif action_type == "steal":
            self._process_steal(outcome, team, int(value))

        elif action_type == "share_all":
            points = int(value)
            for team_name in self.game_state.teams:
                outcome.score_changes[team_name] = points
            outcome.description = f"Everyone gains {points} points!"

        elif action_type == "multiply":
            multiplier = int(value)
            current_score = self.game_state.get_scores()[team]
            max_points = self.config.get_max_points()

            new_score = current_score * multiplier
            if max_points > 0:
                new_score = min(new_score, max_points)

            score_change = new_score - current_score
            outcome.score_changes[team] = score_change

            if max_points > 0 and new_score == max_points:
                outcome.description = f"{team} multiplies score by {multiplier} (capped at {max_points})!"
            else:
                outcome.description = f"{team} multiplies their score by {multiplier}!"

        elif action_type == "divide":
            divisor = int(value)
            current_score = self.game_state.get_scores()[team]
            new_score = max((current_score + divisor - 1) // divisor, 0)  # Round up division, min 0
            score_change = new_score - current_score
            outcome.score_changes[team] = score_change
            outcome.description = f"{team} divides their score by {divisor}!"

    def _process_simple_action(self, outcome: WheelOutcome, team: str, action: str) -> None:
        """Process simple actions without parameters."""
        if action == "swap_random":
            self._process_swap(outcome, team)
        elif action == "wildcard":
            # Wildcard - teacher's choice, default to +5 points
            outcome.score_changes[team] = 5
            outcome.description = f"Wildcard! {team} completes a mini-challenge and gains 5 points!"
        else:
            # Unknown action, give default points
            outcome.score_changes[team] = 5
            outcome.description = f"{team} gets a mystery bonus: +5 points!"

    def _process_steal(self, outcome: WheelOutcome, stealing_team: str, amount: int) -> None:
        """Process steal actions."""
        scores = self.game_state.get_scores()

        # Find teams that have points to steal
        eligible_victims = [
            team for team in self.game_state.teams 
            if team != stealing_team and scores[team] > 0
        ]

        if not eligible_victims:
            # No one to steal from, give consolation points
            outcome.score_changes[stealing_team] = 3
            outcome.description = f"{stealing_team} tried to steal but no one has points! Gets 3 consolation points."
            return

        # Randomly select a victim
        victim = random.choice(eligible_victims)
        actual_stolen = min(amount, scores[victim])

        outcome.score_changes[stealing_team] = actual_stolen
        outcome.score_changes[victim] = -actual_stolen
        outcome.description = f"{stealing_team} steals {actual_stolen} points from {victim}!"

    def _process_swap(self, outcome: WheelOutcome, swapping_team: str) -> None:
        """Process score swap actions."""
        other_teams = [team for team in self.game_state.teams if team != swapping_team]

        if not other_teams:
            # Only one team (shouldn't happen in normal play)
            outcome.description = f"{swapping_team} tries to swap but there's no other team!"
            return

        # Randomly select team to swap with
        swap_target = random.choice(other_teams)
        scores = self.game_state.get_scores()

        swapping_score = scores[swapping_team]
        target_score = scores[swap_target]

        # Calculate the changes needed
        outcome.score_changes[swapping_team] = target_score - swapping_score
        outcome.score_changes[swap_target] = swapping_score - target_score
        outcome.description = f"{swapping_team} swaps scores with {swap_target}!"

    def spin_and_process(self, team: Optional[str] = None) -> Tuple[WheelOutcome, str]:
        """
        Convenience method to spin wheel and process outcome for current team.

        Args:
            team: Team to spin for (uses current team if None)

        Returns:
            Tuple of (outcome, team_that_spun)
        """
        if team is None:
            team = self.game_state.get_current_team()

        outcome = self.spin_wheel()
        self.process_outcome(outcome, team)

        return outcome, team

    def advance_turn(self) -> str:
        """
        Advance to the next team's turn.

        Returns:
            Name of the team whose turn it now is
        """
        return self.game_state.next_turn()

    def advance_round(self) -> int:
        """
        Advance to the next round.

        Returns:
            New round number
        """
        return self.game_state.next_round()

    def is_game_over(self) -> bool:
        """
        Check if the game should end based on configuration limits.

        Returns:
            True if game should end
        """
        max_rounds = self.config.get_max_rounds()
        max_points = self.config.get_max_points()

        # Check round limit
        if self.game_state.get_current_round() > max_rounds:
            return True

        # Check point limit (if set)
        if max_points > 0:
            scores = self.game_state.get_scores()
            if any(score >= max_points for score in scores.values()):
                return True

        return False

    def get_game_status(self) -> str:
        """
        Get current game status summary.

        Returns:
            Formatted string with game status
        """
        lines = []
        lines.append(self.game_state.get_game_summary())

        if self.is_game_over():
            lines.append("")
            lines.append("🎉 GAME OVER! 🎉")

            # Find winner(s)
            scores = self.game_state.get_scores()
            max_score = max(scores.values())
            winners = [team for team, score in scores.items() if score == max_score]

            if len(winners) == 1:
                lines.append(f"Winner: {winners[0]} with {max_score} points!")
            else:
                lines.append(f"Tie between: {', '.join(winners)} with {max_score} points!")

        return "\n".join(lines)


def create_wheel(config: GameConfig, game_state: GameState) -> GameWheel:
    """
    Create a new game wheel instance.

    Args:
        config: Game configuration
        game_state: Current game state

    Returns:
        GameWheel instance
    """
    return GameWheel(config, game_state)


def pick_random_starting_team(teams: List[str]) -> str:
    """
    Randomly select which team goes first.

    Args:
        teams: List of team names

    Returns:
        Name of the randomly selected team
    """
    return random.choice(teams)