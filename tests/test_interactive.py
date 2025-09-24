"""
Tests for game/interactive.py module.

Tests interactive mode functions and game loop logic.
"""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock, call
from game.interactive import (
    _load_or_create_game,
    _create_new_game_interactive,
    _get_team_names,
    _display_menu_and_get_choice,
    _handle_spin_wheel,
    _handle_show_status,
    _handle_change_team,
    _handle_save_and_quit,
    _handle_quit_without_saving
)
from game.config import GameConfig
from game.state import create_new_game
from game.wheel import create_wheel


class TestLoadOrCreateGame:
    """Test cases for _load_or_create_game function."""
    
    def setup_method(self):
        """Set up test with temporary files."""
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_config.close()
        self.config_path = self.temp_config.name
        os.unlink(self.config_path)
        
        self.temp_state = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_state.close()
        self.state_path = self.temp_state.name
        os.unlink(self.state_path)
        
        self.config = GameConfig(self.config_path)
    
    def teardown_method(self):
        """Clean up temporary files."""
        for path in [self.config_path, self.state_path]:
            if os.path.exists(path):
                os.unlink(path)
    
    @patch('game.interactive._create_new_game_interactive')
    def test_load_or_create_no_existing_game(self, mock_create_new):
        """Test when no existing game file exists."""
        mock_game_state = MagicMock()
        mock_create_new.return_value = mock_game_state
        
        result = _load_or_create_game(self.config, self.state_path)
        
        assert result == mock_game_state
        mock_create_new.assert_called_once_with(self.config, self.state_path)
    
    @patch('game.interactive.create_wheel')
    @patch('game.interactive._create_new_game_interactive')
    @patch('builtins.input')
    @patch('builtins.print')
    def test_load_existing_game_continue(self, mock_print, mock_input, mock_create_new, mock_create_wheel):
        """Test loading existing game and choosing to continue."""
        # Create an existing game
        game_state = create_new_game(["Red", "Blue"], state_file=self.state_path)
        
        mock_wheel = MagicMock()
        mock_wheel.get_game_status.return_value = "Game Status"
        mock_create_wheel.return_value = mock_wheel
        
        mock_input.return_value = "y"  # Continue existing game
        
        result = _load_or_create_game(self.config, self.state_path)
        
        assert result is not None
        assert result.teams == ["Red", "Blue"]
        mock_create_new.assert_not_called()
    
    @patch('game.interactive.create_wheel')
    @patch('game.interactive._create_new_game_interactive')
    @patch('builtins.input')
    @patch('builtins.print')
    def test_load_existing_game_dont_continue(self, mock_print, mock_input, mock_create_new, mock_create_wheel):
        """Test loading existing game and choosing not to continue."""
        # Create an existing game
        create_new_game(["Red", "Blue"], state_file=self.state_path)
        
        mock_wheel = MagicMock()
        mock_wheel.get_game_status.return_value = "Game Status"
        mock_create_wheel.return_value = mock_wheel
        
        mock_input.return_value = "n"  # Don't continue existing game
        mock_new_game = MagicMock()
        mock_create_new.return_value = mock_new_game
        
        result = _load_or_create_game(self.config, self.state_path)
        
        assert result == mock_new_game
        mock_create_new.assert_called_once()


class TestCreateNewGameInteractive:
    """Test cases for _create_new_game_interactive function."""
    
    def setup_method(self):
        """Set up test with config."""
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_config.close()
        self.config_path = self.temp_config.name
        os.unlink(self.config_path)
        
        self.temp_state = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_state.close()
        self.state_path = self.temp_state.name
        os.unlink(self.state_path)
        
        self.config = GameConfig(self.config_path)
    
    def teardown_method(self):
        """Clean up temporary files."""
        for path in [self.config_path, self.state_path]:
            if os.path.exists(path):
                os.unlink(path)
    
    @patch('game.interactive._get_team_names')
    @patch('game.interactive.pick_random_starting_team')
    @patch('builtins.input')
    @patch('builtins.print')
    def test_create_new_game_with_random_start(self, mock_print, mock_input, mock_random_team, mock_get_teams):
        """Test creating new game with random starting team."""
        mock_get_teams.return_value = ["Alpha", "Beta"]
        mock_random_team.return_value = "Beta"
        mock_input.return_value = "y"  # Yes to random start
        
        result = _create_new_game_interactive(self.config, self.state_path)
        
        assert result.teams == ["Alpha", "Beta"]
        assert result.get_current_team() == "Beta"
        mock_random_team.assert_called_once_with(["Alpha", "Beta"])
    
    @patch('game.interactive._get_team_names')
    @patch('builtins.input')
    @patch('builtins.print')
    def test_create_new_game_no_random_start(self, mock_print, mock_input, mock_get_teams):
        """Test creating new game without random starting team."""
        mock_get_teams.return_value = ["Team1", "Team2"]
        mock_input.return_value = "n"  # No to random start
        
        result = _create_new_game_interactive(self.config, self.state_path)
        
        assert result.teams == ["Team1", "Team2"]
        assert result.get_current_team() == "Team1"  # Default first team


class TestGetTeamNames:
    """Test cases for _get_team_names function."""
    
    @patch('builtins.input')
    def test_get_team_names_valid(self, mock_input):
        """Test getting valid team names."""
        mock_input.return_value = "Red Blue Green"
        
        result = _get_team_names()
        
        assert result == ["Red", "Blue", "Green"]
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_get_team_names_insufficient_teams(self, mock_print, mock_input):
        """Test handling insufficient team names."""
        mock_input.side_effect = [
            "OnlyOne",  # First input - too few teams
            "Team1 Team2"  # Second input - valid
        ]
        
        result = _get_team_names()
        
        assert result == ["Team1", "Team2"]
        # Should have printed error message
        mock_print.assert_called_with("❌ At least 2 teams required")
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_get_team_names_duplicate_teams(self, mock_print, mock_input):
        """Test handling duplicate team names."""
        mock_input.side_effect = [
            "Red Blue Red",  # First input - duplicates
            "Red Blue Green"  # Second input - valid
        ]
        
        result = _get_team_names()
        
        assert result == ["Red", "Blue", "Green"]
        # Should have printed error message
        mock_print.assert_called_with("❌ Team names must be unique")
    
    @patch('builtins.input')
    def test_get_team_names_empty_input(self, mock_input):
        """Test handling empty input."""
        mock_input.side_effect = [
            "",  # Empty input
            "   ",  # Whitespace only
            "Alpha Beta"  # Valid input
        ]
        
        result = _get_team_names()
        
        assert result == ["Alpha", "Beta"]


class TestMenuHelpers:
    """Test cases for menu helper functions."""
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_display_menu_and_get_choice(self, mock_print, mock_input):
        """Test menu display and choice input."""
        mock_input.return_value = "1"
        
        result = _display_menu_and_get_choice()
        
        assert result == "1"
        # Should have printed menu options
        assert mock_print.call_count > 0
        menu_text = " ".join(str(call) for call in mock_print.call_args_list)
        assert "Spin the wheel" in menu_text


class TestGameActions:
    """Test cases for game action handlers."""
    
    def setup_method(self):
        """Set up test with game components.""" 
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_config.close()
        self.config_path = self.temp_config.name
        os.unlink(self.config_path)
        
        self.temp_state = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_state.close()
        self.state_path = self.temp_state.name
        os.unlink(self.state_path)
        
        self.config = GameConfig(self.config_path)
        self.game_state = create_new_game(["Red", "Blue"], state_file=self.state_path)
        self.wheel = create_wheel(self.config, self.game_state)
    
    def teardown_method(self):
        """Clean up temporary files."""
        for path in [self.config_path, self.state_path]:
            if os.path.exists(path):
                os.unlink(path)
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_handle_spin_wheel(self, mock_print, mock_input):
        """Test handling wheel spin action."""
        mock_input.return_value = ""  # Press Enter to continue
        
        with patch.object(self.wheel, 'spin_and_process') as mock_spin, \
             patch.object(self.wheel, 'advance_turn') as mock_advance:
             
            mock_outcome = MagicMock()
            mock_outcome.label = "+5 points"
            mock_outcome.description = "Red gains 5 points"
            mock_outcome.score_changes = {"Red": 5}
            mock_spin.return_value = (mock_outcome, "Red")
            mock_advance.return_value = "Blue"
            
            _handle_spin_wheel(self.wheel, "Red")
            
            mock_spin.assert_called_once()
            mock_advance.assert_called_once()
            
            # Should print outcome details
            calls = [str(call) for call in mock_print.call_args_list]
            assert any("+5 points" in call for call in calls)
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_handle_show_status(self, mock_print, mock_input):
        """Test handling show status action."""
        mock_input.return_value = ""  # Press Enter to continue
        
        with patch.object(self.wheel, 'get_game_status') as mock_status:
            mock_status.return_value = "Game Status Info"
            
            _handle_show_status(self.wheel)
            
            mock_status.assert_called_once()
            calls = [str(call) for call in mock_print.call_args_list]
            assert any("Game Status Info" in call for call in calls)
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_handle_change_team_valid(self, mock_print, mock_input):
        """Test handling team change with valid team."""
        mock_input.side_effect = ["Blue", ""]  # Team name, then Enter to continue
        
        _handle_change_team(self.game_state)
        
        assert self.game_state.get_current_team() == "Blue"
        calls = [str(call) for call in mock_print.call_args_list]
        assert any("Current team changed to Blue" in call for call in calls)
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_handle_change_team_invalid(self, mock_print, mock_input):
        """Test handling team change with invalid team."""
        mock_input.side_effect = ["InvalidTeam", ""]  # Invalid team name, then Enter
        
        _handle_change_team(self.game_state)
        
        # Team should remain unchanged
        assert self.game_state.get_current_team() == "Red"
        calls = [str(call) for call in mock_print.call_args_list]
        assert any("Invalid team name" in call for call in calls)
    
    @patch('builtins.print')
    def test_handle_save_and_quit(self, mock_print):
        """Test handling save and quit action."""
        with patch.object(self.game_state, 'save_state') as mock_save:
            _handle_save_and_quit(self.game_state)
            
            mock_save.assert_called_once()
            calls = [str(call) for call in mock_print.call_args_list]
            assert any("Game saved" in call for call in calls)
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_handle_quit_without_saving_yes(self, mock_print, mock_input):
        """Test quit without saving when user confirms."""
        mock_input.return_value = "y"
        
        result = _handle_quit_without_saving()
        
        assert result is True
        calls = [str(call) for call in mock_print.call_args_list]
        assert any("Goodbye" in call for call in calls)
    
    @patch('builtins.input')
    def test_handle_quit_without_saving_no(self, mock_input):
        """Test quit without saving when user cancels."""
        mock_input.return_value = "n"
        
        result = _handle_quit_without_saving()
        
        assert result is False