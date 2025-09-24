"""
Tests for main.py module.

Tests CLI argument parsing and main entry point functionality.
"""

import argparse
import pytest
from unittest.mock import patch, MagicMock
from main import create_parser, main


class TestCreateParser:
    """Test cases for create_parser function."""

    def test_parser_creation(self):
        """Test that parser is created with correct structure."""
        parser = create_parser()
        assert isinstance(parser, argparse.ArgumentParser)
        assert parser.description
        assert "Unfair Review Game" in parser.description

    def test_global_options(self):
        """Test global command line options."""
        parser = create_parser()

        # Test --config option
        args = parser.parse_args(["--config", "test.json", "status"])
        assert args.config == "test.json"

        # Test --state option
        args = parser.parse_args(["--state", "game.json", "status"])
        assert args.state == "game.json"

        # Test short versions
        args = parser.parse_args(["-c", "test.json", "-s", "game.json", "status"])
        assert args.config == "test.json"
        assert args.state == "game.json"

    def test_start_command_parsing(self):
        """Test start command argument parsing."""
        parser = create_parser()

        # Basic team names
        args = parser.parse_args(["start", "Red", "Blue", "Green"])
        assert args.command == "start"
        assert args.teams == ["Red", "Blue", "Green"]
        assert args.points is None
        assert args.random_start is False

        # With options
        args = parser.parse_args(["start", "Team1", "Team2", "--points", "15", "--random-start"])
        assert args.points == 15
        assert args.random_start is True

    def test_spin_command_parsing(self):
        """Test spin command argument parsing."""
        parser = create_parser()

        # No team specified
        args = parser.parse_args(["spin"])
        assert args.command == "spin"
        assert args.team is None

        # Team specified
        args = parser.parse_args(["spin", "Blue"])
        assert args.team == "Blue"

    def test_load_command_parsing(self):
        """Test load command argument parsing."""
        parser = create_parser()

        args = parser.parse_args(["load", "saved_game.json"])
        assert args.command == "load"
        assert args.file == "saved_game.json"

    def test_interactive_command_parsing(self):
        """Test interactive command parsing."""
        parser = create_parser()

        args = parser.parse_args(["interactive"])
        assert args.command == "interactive"

    def test_auto_spin_command_parsing(self):
        """Test auto-spin command parsing."""
        parser = create_parser()

        # Default delay
        args = parser.parse_args(["auto-spin"])
        assert args.command == "auto-spin"
        assert args.delay == 2.0

        # Custom delay
        args = parser.parse_args(["auto-spin", "--delay", "1.5"])
        assert args.delay == 1.5

    def test_simple_command_parsing(self):
        """Test simple command parsing."""
        parser = create_parser()

        # Basic simple mode
        args = parser.parse_args(["simple"])
        assert args.command == "simple"
        assert args.verbose is False

        # Verbose mode
        args = parser.parse_args(["simple", "--verbose"])
        assert args.verbose is True

    def test_config_command_parsing(self):
        """Test config command parsing."""
        parser = create_parser()

        # Show config
        args = parser.parse_args(["config", "show"])
        assert args.command == "config"
        assert args.config_action == "show"

        # Edit config
        args = parser.parse_args(["config", "edit"])
        assert args.config_action == "edit"

    def test_status_command_parsing(self):
        """Test status command parsing."""
        parser = create_parser()

        args = parser.parse_args(["status"])
        assert args.command == "status"


class TestMainFunction:
    """Test cases for main function."""

    @patch('main.GameConfig')
    @patch('main.handle_start_command')
    def test_main_start_command(self, mock_handle_start, mock_config_class):
        """Test main function with start command."""
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config

        with patch('sys.argv', ['main.py', 'start', 'Red', 'Blue']):
            main()

            mock_config_class.assert_called_once_with('config.json')
            mock_handle_start.assert_called_once()

    @patch('main.GameConfig')
    @patch('main.handle_spin_command')
    def test_main_spin_command(self, mock_handle_spin, mock_config_class):
        """Test main function with spin command."""
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config

        with patch('sys.argv', ['main.py', 'spin']):
            main()

            mock_handle_spin.assert_called_once()

    @patch('main.GameConfig')
    @patch('main.run_interactive_mode')
    def test_main_interactive_command(self, mock_interactive, mock_config_class):
        """Test main function with interactive command."""
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config

        with patch('sys.argv', ['main.py', 'interactive']):
            main()

            mock_interactive.assert_called_once()

    @patch('main.GameConfig')
    @patch('main.run_auto_spin_mode')
    def test_main_auto_spin_command(self, mock_auto_spin, mock_config_class):
        """Test main function with auto-spin command."""
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config

        with patch('sys.argv', ['main.py', 'auto-spin', '--delay', '1.0']):
            main()

            mock_auto_spin.assert_called_once()

    @patch('main.GameConfig')
    @patch('main.run_simple_mode')
    def test_main_simple_command(self, mock_simple, mock_config_class):
        """Test main function with simple command."""
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config

        with patch('sys.argv', ['main.py', 'simple', '--verbose']):
            main()

            mock_simple.assert_called_once()

    @patch('main.GameConfig')
    @patch('main.handle_config_command')
    def test_main_config_command(self, mock_handle_config, mock_config_class):
        """Test main function with config command."""
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config

        with patch('sys.argv', ['main.py', 'config', 'show']):
            main()

            mock_handle_config.assert_called_once()

    @patch('main.GameConfig')
    @patch('main.handle_status_command')
    def test_main_status_command(self, mock_handle_status, mock_config_class):
        """Test main function with status command."""
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config

        with patch('sys.argv', ['main.py', 'status']):
            main()

            mock_handle_status.assert_called_once()

    @patch('main.GameConfig')
    def test_main_no_command(self, mock_config_class):
        """Test main function with no command (help mode)."""
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config

        with patch('sys.argv', ['main.py']):
            with patch('builtins.print') as mock_print:
                main()

                calls = [str(call) for call in mock_print.call_args_list]
                assert any("Unfair Review Game" in call for call in calls)

    @patch('main.GameConfig')
    def test_main_config_error(self, mock_config_class):
        """Test main function when config loading fails."""
        mock_config_class.side_effect = Exception("Config error")

        with patch('sys.argv', ['main.py', 'status']):
            with pytest.raises(SystemExit):
                with patch('builtins.print'):
                    main()

    @patch('main.GameConfig')
    @patch('main.handle_start_command')
    def test_main_keyboard_interrupt(self, mock_handle_start, mock_config_class):
        """Test main function handling KeyboardInterrupt."""
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config
        mock_handle_start.side_effect = KeyboardInterrupt()

        with patch('sys.argv', ['main.py', 'start', 'Red', 'Blue']):
            with patch('builtins.print') as mock_print:
                main()

                calls = [str(call) for call in mock_print.call_args_list]
                assert any("Goodbye" in call for call in calls)

    @patch('main.GameConfig')
    @patch('main.handle_start_command')
    def test_main_general_exception(self, mock_handle_start, mock_config_class):
        """Test main function handling general exceptions."""
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config
        mock_handle_start.side_effect = Exception("Test error")

        with patch('sys.argv', ['main.py', 'start', 'Red', 'Blue']):
            with pytest.raises(SystemExit):
                with patch('builtins.print'):
                    main()