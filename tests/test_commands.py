"""
Tests for game/commands.py module.

Tests CLI command handlers and their integration with other components.
"""

import os
import tempfile
import pytest
import argparse
from unittest.mock import patch, MagicMock
from game.commands import (
    handle_start_command,
    handle_spin_command,
    handle_load_command,
    handle_config_command,
    handle_status_command
)
from game.config import GameConfig
from game.state import create_new_game


class TestHandleStartCommand:
    """Test cases for handle_start_command."""

    def setup_method(self):
        """Set up test with temporary files."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.config_path = self.temp_file.name
        os.unlink(self.config_path)

        self.state_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.state_file.close()
        self.state_path = self.state_file.name
        os.unlink(self.state_path)

        self.config = GameConfig(self.config_path)

    def teardown_method(self):
        """Clean up temporary files."""
        for path in [self.config_path, self.state_path]:
            if os.path.exists(path):
                os.unlink(path)

    def test_start_command_basic(self):
        """Test basic start command functionality."""
        # Create mock args
        args = argparse.Namespace(
            teams=["Red", "Blue", "Green"],
            points=None,
            random_start=False,
            state=self.state_path
        )

        with patch('builtins.print') as mock_print:
            handle_start_command(args, self.config)

            # Verify output messages
            calls = [str(call) for call in mock_print.call_args_list]
            assert any("New game started" in call for call in calls)
            assert any("Red, Blue, Green" in call for call in calls)

    def test_start_command_with_points(self):
        """Test start command with custom starting points."""
        args = argparse.Namespace(
            teams=["Team1", "Team2"],
            points=25,
            random_start=False,
            state=self.state_path
        )

        with patch('builtins.print') as mock_print:
            handle_start_command(args, self.config)

            calls = [str(call) for call in mock_print.call_args_list]
            assert any("Starting points: 25" in call for call in calls)

    @patch('game.commands.pick_random_starting_team')
    def test_start_command_random_start(self, mock_random_team):
        """Test start command with random starting team."""
        mock_random_team.return_value = "Blue"

        args = argparse.Namespace(
            teams=["Red", "Blue"],
            points=None,
            random_start=True,
            state=self.state_path
        )

        with patch('builtins.print') as mock_print:
            handle_start_command(args, self.config)

            calls = [str(call) for call in mock_print.call_args_list]
            assert any("Random starting team selected: Blue" in call for call in calls)

    def test_start_command_insufficient_teams(self):
        """Test start command with too few teams."""
        args = argparse.Namespace(
            teams=["OnlyOne"],
            points=None,
            random_start=False,
            state=self.state_path
        )

        with pytest.raises(SystemExit):
            with patch('builtins.print'):
                handle_start_command(args, self.config)

    def test_start_command_duplicate_teams(self):
        """Test start command with duplicate team names."""
        args = argparse.Namespace(
            teams=["Red", "Blue", "Red"],
            points=None,
            random_start=False,
            state=self.state_path
        )

        with pytest.raises(SystemExit):
            with patch('builtins.print'):
                handle_start_command(args, self.config)


class TestHandleSpinCommand:
    """Test cases for handle_spin_command."""

    def setup_method(self):
        """Set up test with game state."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.config_path = self.temp_file.name
        os.unlink(self.config_path)

        self.state_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.state_file.close()
        self.state_path = self.state_file.name
        os.unlink(self.state_path)

        self.config = GameConfig(self.config_path)

        # Create a game state
        self.game_state = create_new_game(["Red", "Blue"], state_file=self.state_path)

    def teardown_method(self):
        """Clean up temporary files."""
        for path in [self.config_path, self.state_path]:
            if os.path.exists(path):
                os.unlink(path)

    def test_spin_command_no_game(self):
        """Test spin command when no saved game exists."""
        # Remove the game state file
        os.unlink(self.state_path)

        args = argparse.Namespace(
            team=None,
            state=self.state_path
        )

        with pytest.raises(SystemExit):
            with patch('builtins.print'):
                handle_spin_command(args, self.config)

    @patch('game.commands.create_wheel')
    def test_spin_command_current_team(self, mock_create_wheel):
        """Test spin command for current team."""
        # Mock the wheel
        mock_wheel = MagicMock()
        mock_wheel.is_game_over.return_value = False
        mock_wheel.spin_and_process.return_value = (MagicMock(
            label="+5 points",
            description="Red gains 5 points",
            score_changes={"Red": 5}
        ), "Red")
        mock_wheel.advance_turn.return_value = "Blue"
        mock_create_wheel.return_value = mock_wheel

        args = argparse.Namespace(
            team=None,
            state=self.state_path
        )

        with patch('builtins.print') as mock_print:
            handle_spin_command(args, self.config)

            # Verify wheel was used
            mock_wheel.spin_and_process.assert_called_once_with("Red")
            mock_wheel.advance_turn.assert_called_once()

    def test_spin_command_invalid_team(self):
        """Test spin command with invalid team name."""
        args = argparse.Namespace(
            team="InvalidTeam",
            state=self.state_path
        )

        with pytest.raises(SystemExit):
            with patch('builtins.print'):
                handle_spin_command(args, self.config)

    @patch('game.commands.create_wheel')
    def test_spin_command_game_over(self, mock_create_wheel):
        """Test spin command when game is over."""
        # Mock the wheel to indicate game is over
        mock_wheel = MagicMock()
        mock_wheel.is_game_over.return_value = True
        mock_wheel.get_game_status.return_value = "Game Over!"
        mock_create_wheel.return_value = mock_wheel

        args = argparse.Namespace(
            team=None,
            state=self.state_path
        )

        with patch('builtins.print') as mock_print:
            handle_spin_command(args, self.config)

            # Should show game over status and return early
            mock_wheel.get_game_status.assert_called_once()
            calls = [str(call) for call in mock_print.call_args_list]
            assert any("Game Over!" in call for call in calls)

    @patch('game.commands.create_wheel')
    def test_spin_command_specific_team(self, mock_create_wheel):
        """Test spin command for specific team (no turn advance)."""
        # Mock the wheel
        mock_wheel = MagicMock()
        mock_wheel.is_game_over.return_value = False
        mock_wheel.spin_and_process.return_value = (MagicMock(
            label="+10 points",
            description="Blue gains 10 points",
            score_changes={"Blue": 10}
        ), "Blue")
        mock_create_wheel.return_value = mock_wheel

        args = argparse.Namespace(
            team="Blue",  # Specific team
            state=self.state_path
        )

        with patch('builtins.print') as mock_print:
            handle_spin_command(args, self.config)

            # Should NOT advance turn when team is specified
            mock_wheel.advance_turn.assert_not_called()
            mock_wheel.spin_and_process.assert_called_once_with("Blue")


class TestHandleLoadCommand:
    """Test cases for handle_load_command."""

    def setup_method(self):
        """Set up test files."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.config_path = self.temp_file.name
        os.unlink(self.config_path)

        self.state_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.state_file.close()
        self.state_path = self.state_file.name
        os.unlink(self.state_path)

        self.load_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.load_file.close()
        self.load_path = self.load_file.name
        os.unlink(self.load_path)

        self.config = GameConfig(self.config_path)

    def teardown_method(self):
        """Clean up temporary files."""
        for path in [self.config_path, self.state_path, self.load_path]:
            if os.path.exists(path):
                os.unlink(path)

    def test_load_command_nonexistent_file(self):
        """Test load command with nonexistent file."""
        args = argparse.Namespace(
            file="nonexistent.json",
            state=self.state_path
        )

        with pytest.raises(SystemExit):
            with patch('builtins.print'):
                handle_load_command(args, self.config)

    @patch('game.commands.create_wheel')
    def test_load_command_success(self, mock_create_wheel):
        """Test successful load command."""
        # Create a game to load
        game_state = create_new_game(["Alpha", "Beta"], state_file=self.load_path)

        # Mock wheel
        mock_wheel = MagicMock()
        mock_wheel.get_game_status.return_value = "Game Status"
        mock_create_wheel.return_value = mock_wheel

        args = argparse.Namespace(
            file=self.load_path,
            state=self.state_path
        )

        with patch('builtins.print') as mock_print:
            handle_load_command(args, self.config)

            calls = [str(call) for call in mock_print.call_args_list]
            assert any(f"Game loaded from {self.load_path}" in call for call in calls)

    def test_load_command_error_handling(self):
        """Test load command with corrupted file."""
        # Create a corrupted JSON file
        with open(self.load_path, 'w') as f:
            f.write("invalid json content")

        args = argparse.Namespace(
            file=self.load_path,
            state=self.state_path
        )

        with pytest.raises(SystemExit):
            with patch('builtins.print') as mock_print:
                handle_load_command(args, self.config)

                # Should print error message
                calls = [str(call) for call in mock_print.call_args_list]
                assert any("Error loading game" in call for call in calls)


class TestHandleConfigCommand:
    """Test cases for handle_config_command."""

    def setup_method(self):
        """Set up test with config."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.config_path = self.temp_file.name
        os.unlink(self.config_path)

        self.config = GameConfig(self.config_path)

    def teardown_method(self):
        """Clean up temporary files."""
        if os.path.exists(self.config_path):
            os.unlink(self.config_path)

    def test_config_show_command(self):
        """Test config show command."""
        args = argparse.Namespace(config_action="show")

        with patch('builtins.print') as mock_print:
            handle_config_command(args, self.config)

            calls = [str(call) for call in mock_print.call_args_list]
            assert any("Current Configuration" in call for call in calls)

    @patch('builtins.input')
    def test_config_edit_command(self, mock_input):
        """Test config edit command."""
        # Mock user inputs (press Enter to keep defaults)
        mock_input.side_effect = ["", "", ""]  # Empty inputs to keep defaults

        args = argparse.Namespace(config_action="edit")

        with patch('builtins.print') as mock_print:
            handle_config_command(args, self.config)

            calls = [str(call) for call in mock_print.call_args_list]
            assert any("Configuration saved" in call for call in calls)

    @patch('builtins.input')
    def test_config_edit_command_with_values(self, mock_input):
        """Test config edit command with new values."""
        # Mock user inputs with actual values
        mock_input.side_effect = ["25", "100", "30"]  # New values

        args = argparse.Namespace(config_action="edit")

        with patch('builtins.print') as mock_print:
            handle_config_command(args, self.config)

            # Verify config was updated
            assert self.config.get_starting_points() == 25
            assert self.config.get_max_points() == 100
            assert self.config.get_max_rounds() == 30

    @patch('builtins.input')
    def test_config_edit_command_invalid_value(self, mock_input):
        """Test config edit command with invalid values."""
        # Mock user inputs with invalid value
        mock_input.side_effect = ["-5"]  # Invalid starting points

        args = argparse.Namespace(config_action="edit")

        with pytest.raises(SystemExit):
            with patch('builtins.print'):
                handle_config_command(args, self.config)

    @patch('builtins.input')
    def test_config_edit_command_keyboard_interrupt(self, mock_input):
        """Test config edit command with keyboard interrupt."""
        mock_input.side_effect = KeyboardInterrupt()

        args = argparse.Namespace(config_action="edit")

        with patch('builtins.print') as mock_print:
            handle_config_command(args, self.config)

            calls = [str(call) for call in mock_print.call_args_list]
            assert any("cancelled" in call for call in calls)

    def test_config_invalid_action(self):
        """Test config command with invalid action."""
        args = argparse.Namespace(config_action="invalid")

        with pytest.raises(SystemExit):
            with patch('builtins.print'):
                handle_config_command(args, self.config)


class TestHandleStatusCommand:
    """Test cases for handle_status_command."""

    def setup_method(self):
        """Set up test files."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.config_path = self.temp_file.name
        os.unlink(self.config_path)

        self.state_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.state_file.close()
        self.state_path = self.state_file.name
        os.unlink(self.state_path)

        self.config = GameConfig(self.config_path)

    def teardown_method(self):
        """Clean up temporary files."""
        for path in [self.config_path, self.state_path]:
            if os.path.exists(path):
                os.unlink(path)

    def test_status_command_no_game(self):
        """Test status command when no game exists."""
        args = argparse.Namespace(state=self.state_path)

        with patch('builtins.print') as mock_print:
            handle_status_command(args, self.config)

            calls = [str(call) for call in mock_print.call_args_list]
            assert any("No active game found" in call for call in calls)

    @patch('game.commands.create_wheel')
    def test_status_command_with_game(self, mock_create_wheel):
        """Test status command with existing game."""
        # Create a game
        create_new_game(["Red", "Blue"], state_file=self.state_path)

        # Mock wheel
        mock_wheel = MagicMock()
        mock_wheel.get_game_status.return_value = "Current Game Status"
        mock_create_wheel.return_value = mock_wheel

        args = argparse.Namespace(state=self.state_path)

        with patch('builtins.print') as mock_print:
            handle_status_command(args, self.config)

            calls = [str(call) for call in mock_print.call_args_list]
            assert any("Current Game Status" in call for call in calls)

    def test_status_command_error_handling(self):
        """Test status command with corrupted state file."""
        # Create corrupted state file
        with open(self.state_path, 'w') as f:
            f.write("invalid json")

        args = argparse.Namespace(state=self.state_path)

        with patch('builtins.print') as mock_print:
            handle_status_command(args, self.config)

            calls = [str(call) for call in mock_print.call_args_list]
            assert any("Error loading game status" in call for call in calls)