"""
Tests for game/wheel.py module.

Tests wheel mechanics, outcome processing, and game integration.
"""

import pytest
from unittest.mock import patch
from game.config import GameConfig
from game.state import create_new_game
from game.wheel import GameWheel, WheelOutcome, create_wheel, pick_random_starting_team


class TestWheelOutcome:
    """Test cases for WheelOutcome class."""

    def test_wheel_outcome_creation(self):
        """Test creating a WheelOutcome."""
        outcome = WheelOutcome("+5 points", "add_fixed:5", 3)

        assert outcome.label == "+5 points"
        assert outcome.action == "add_fixed:5"
        assert outcome.weight == 3
        assert outcome.score_changes == {}
        assert outcome.description == ""


class TestGameWheel:
    """Test cases for GameWheel class."""

    def setup_method(self):
        """Set up test with config and game state."""
        self.config = GameConfig("test_wheel_config.json")
        self.teams = ["Red", "Blue", "Green"]
        self.game_state = create_new_game(self.teams, starting_points=20, state_file="test_wheel_state.json")
        self.wheel = GameWheel(self.config, self.game_state)

    def teardown_method(self):
        """Clean up test files."""
        import os
        for file in ["test_wheel_config.json", "test_wheel_state.json"]:
            if os.path.exists(file):
                os.unlink(file)

    def test_wheel_initialization(self):
        """Test wheel initialization."""
        assert self.wheel.config == self.config
        assert self.wheel.game_state == self.game_state

    @patch('random.choices')
    def test_spin_wheel(self, mock_choices):
        """Test wheel spinning mechanism."""
        # Mock random selection to return first option
        mock_choices.return_value = [("+5 points", "add_fixed:5", 3)]

        outcome = self.wheel.spin_wheel()

        assert outcome.label == "+5 points"
        assert outcome.action == "add_fixed:5"
        assert outcome.weight == 3

        # Verify random.choices was called with weights
        mock_choices.assert_called_once()
        args = mock_choices.call_args[0]
        weights = mock_choices.call_args[1]['weights']
        assert len(weights) == 10  # Default config has 10 options

    def test_process_add_fixed_positive(self):
        """Test processing positive point addition."""
        outcome = WheelOutcome("+5 points", "add_fixed:5", 3)

        self.wheel.process_outcome(outcome, "Red")

        assert outcome.score_changes == {"Red": 5}
        assert "Red gains 5 points" in outcome.description
        assert self.game_state.get_scores()["Red"] == 25  # 20 + 5

    def test_process_add_fixed_negative(self):
        """Test processing negative point addition."""
        outcome = WheelOutcome("-5 points", "add_fixed:-5", 2)

        self.wheel.process_outcome(outcome, "Red")

        assert outcome.score_changes == {"Red": -5}
        assert "Red loses 5 points" in outcome.description
        assert self.game_state.get_scores()["Red"] == 15  # 20 - 5

    def test_process_add_fixed_rubber_band(self):
        """Test rubber-band effect for negative points when team has 0."""
        # Set Red team to 0 points
        self.game_state.scores["Red"] = 0
        outcome = WheelOutcome("-5 points", "add_fixed:-5", 2)

        self.wheel.process_outcome(outcome, "Red")

        assert outcome.score_changes == {"Red": 5}
        assert "rubber-band effect" in outcome.description
        assert self.game_state.get_scores()["Red"] == 5

    def test_process_steal_successful(self):
        """Test successful steal action."""
        outcome = WheelOutcome("Steal 5", "steal:5", 2)

        with patch('random.choice', return_value="Blue"):
            self.wheel.process_outcome(outcome, "Red")

        assert outcome.score_changes["Red"] == 5
        assert outcome.score_changes["Blue"] == -5
        assert "Red steals 5 points from Blue" in outcome.description
        assert self.game_state.get_scores()["Red"] == 25  # 20 + 5
        assert self.game_state.get_scores()["Blue"] == 15  # 20 - 5

    def test_process_steal_no_victims(self):
        """Test steal when no other teams have points."""
        # Set all other teams to 0 points
        for team in ["Blue", "Green"]:
            self.game_state.scores[team] = 0

        outcome = WheelOutcome("Steal 5", "steal:5", 2)
        self.wheel.process_outcome(outcome, "Red")

        assert outcome.score_changes == {"Red": 3}  # Consolation points
        assert "no one has points" in outcome.description
        assert self.game_state.get_scores()["Red"] == 23  # 20 + 3

    def test_process_steal_partial(self):
        """Test steal when victim has fewer points than steal amount."""
        # Set Blue to only have 3 points
        self.game_state.scores["Blue"] = 3
        outcome = WheelOutcome("Steal 10", "steal:10", 1)

        with patch('random.choice', return_value="Blue"):
            self.wheel.process_outcome(outcome, "Red")

        assert outcome.score_changes["Red"] == 3  # Can only steal what's available
        assert outcome.score_changes["Blue"] == -3
        assert "Red steals 3 points from Blue" in outcome.description

    def test_process_share_all(self):
        """Test share points to all teams."""
        outcome = WheelOutcome("Share +5 to all", "share_all:5", 2)

        self.wheel.process_outcome(outcome, "Red")

        assert outcome.score_changes == {"Red": 5, "Blue": 5, "Green": 5}
        assert "Everyone gains 5 points" in outcome.description

        # Check all teams got points
        scores = self.game_state.get_scores()
        assert all(score == 25 for score in scores.values())  # 20 + 5

    def test_process_multiply(self):
        """Test score multiplication."""
        outcome = WheelOutcome("Double your score", "multiply:2", 1)

        self.wheel.process_outcome(outcome, "Red")

        assert outcome.score_changes == {"Red": 20}  # 20 * 2 - 20 = 20
        assert "Red multiplies their score by 2" in outcome.description
        assert self.game_state.get_scores()["Red"] == 40  # 20 * 2

    def test_process_multiply_with_cap(self):
        """Test score multiplication with point cap."""
        # Set max points to 30
        self.config.update_max_points(30)
        outcome = WheelOutcome("Double your score", "multiply:2", 1)

        self.wheel.process_outcome(outcome, "Red")

        assert outcome.score_changes == {"Red": 10}  # Capped at 30, so 30 - 20 = 10
        assert "capped at 30" in outcome.description
        assert self.game_state.get_scores()["Red"] == 30

    def test_process_divide(self):
        """Test score division."""
        outcome = WheelOutcome("Halve your score", "divide:2", 1)

        self.wheel.process_outcome(outcome, "Red")

        # 20 / 2 = 10, so change is 10 - 20 = -10
        assert outcome.score_changes == {"Red": -10}
        assert "Red divides their score by 2" in outcome.description
        assert self.game_state.get_scores()["Red"] == 10

    def test_process_swap_random(self):
        """Test random score swap."""
        outcome = WheelOutcome("Swap scores", "swap_random", 1)

        with patch('random.choice', return_value="Blue"):
            self.wheel.process_outcome(outcome, "Red")

        # Red and Blue should swap scores (both had 20, so no change)
        assert outcome.score_changes == {"Red": 0, "Blue": 0}
        assert "Red swaps scores with Blue" in outcome.description

    def test_process_swap_different_scores(self):
        """Test score swap with different scores."""
        # Give Blue different score
        self.game_state.scores["Blue"] = 15
        outcome = WheelOutcome("Swap scores", "swap_random", 1)

        with patch('random.choice', return_value="Blue"):
            self.wheel.process_outcome(outcome, "Red")

        # Red: 20 -> 15 (change: -5), Blue: 15 -> 20 (change: +5)
        assert outcome.score_changes == {"Red": -5, "Blue": 5}
        assert self.game_state.get_scores()["Red"] == 15
        assert self.game_state.get_scores()["Blue"] == 20

    def test_process_wildcard(self):
        """Test wildcard action."""
        outcome = WheelOutcome("Wildcard", "wildcard", 1)

        self.wheel.process_outcome(outcome, "Red")

        assert outcome.score_changes == {"Red": 5}
        assert "Wildcard" in outcome.description
        assert "mini-challenge" in outcome.description
        assert self.game_state.get_scores()["Red"] == 25  # 20 + 5

    def test_spin_and_process(self):
        """Test convenience method for spinning and processing."""
        with patch.object(self.wheel, 'spin_wheel') as mock_spin, \
             patch.object(self.wheel, 'process_outcome') as mock_process:

            mock_outcome = WheelOutcome("+5 points", "add_fixed:5", 3)
            mock_spin.return_value = mock_outcome

            outcome, team = self.wheel.spin_and_process()

            assert outcome == mock_outcome
            assert team == "Red"  # Current team
            mock_spin.assert_called_once()
            mock_process.assert_called_once_with(mock_outcome, "Red")

    def test_spin_and_process_specific_team(self):
        """Test spin and process for specific team."""
        with patch.object(self.wheel, 'spin_wheel') as mock_spin, \
             patch.object(self.wheel, 'process_outcome') as mock_process:

            mock_outcome = WheelOutcome("+5 points", "add_fixed:5", 3)
            mock_spin.return_value = mock_outcome

            outcome, team = self.wheel.spin_and_process("Blue")

            assert team == "Blue"
            mock_process.assert_called_once_with(mock_outcome, "Blue")

    def test_advance_turn(self):
        """Test advancing to next turn."""
        assert self.game_state.get_current_team() == "Red"

        next_team = self.wheel.advance_turn()

        assert next_team == "Blue"
        assert self.game_state.get_current_team() == "Blue"

    def test_advance_round(self):
        """Test advancing to next round."""
        assert self.game_state.get_current_round() == 1

        new_round = self.wheel.advance_round()

        assert new_round == 2
        assert self.game_state.get_current_round() == 2
        assert self.game_state.get_current_team() == "Red"  # Reset to first team

    def test_is_game_over_round_limit(self):
        """Test game over due to round limit."""
        # Set to last round
        self.game_state.current_round = 20
        assert not self.wheel.is_game_over()

        # Exceed round limit
        self.game_state.current_round = 21
        assert self.wheel.is_game_over()

    def test_is_game_over_point_limit(self):
        """Test game over due to point limit."""
        # Set max points
        self.config.update_max_points(50)
        assert not self.wheel.is_game_over()

        # Reach point limit
        self.game_state.scores["Red"] = 50
        assert self.wheel.is_game_over()

    def test_is_game_over_no_limits(self):
        """Test game continues when no limits reached."""
        assert not self.wheel.is_game_over()

    def test_get_game_status_ongoing(self):
        """Test game status for ongoing game."""
        status = self.wheel.get_game_status()

        assert "Current Game State" in status
        assert "Round: 1" in status
        assert "GAME OVER" not in status

    def test_get_game_status_game_over(self):
        """Test game status when game is over."""
        # Set game to be over
        self.game_state.current_round = 21
        self.game_state.scores["Red"] = 30
        self.game_state.scores["Blue"] = 20

        status = self.wheel.get_game_status()

        assert "GAME OVER" in status
        assert "Winner: Red with 30 points" in status

    def test_get_game_status_tie(self):
        """Test game status with tie."""
        # Set up tie
        self.game_state.current_round = 21
        self.game_state.scores["Red"] = 25
        self.game_state.scores["Blue"] = 25

        status = self.wheel.get_game_status()

        assert "GAME OVER" in status
        assert "Tie between" in status
        assert "Red, Blue" in status


class TestUtilityFunctions:
    """Test utility functions."""

    def test_create_wheel(self):
        """Test create_wheel function."""
        config = GameConfig("test_config.json")
        game_state = create_new_game(["Red", "Blue"], state_file="test_state.json")

        try:
            wheel = create_wheel(config, game_state)
            assert isinstance(wheel, GameWheel)
            assert wheel.config == config
            assert wheel.game_state == game_state
        finally:
            import os
            for file in ["test_config.json", "test_state.json"]:
                if os.path.exists(file):
                    os.unlink(file)

    @patch('random.choice')
    def test_pick_random_starting_team(self, mock_choice):
        """Test picking random starting team."""
        teams = ["Red", "Blue", "Green"]
        mock_choice.return_value = "Blue"

        selected = pick_random_starting_team(teams)

        assert selected == "Blue"
        mock_choice.assert_called_once_with(teams)