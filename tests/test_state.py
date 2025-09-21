"""
Tests for game/state.py module.

Tests game state management, persistence, and recovery functionality.
"""

import json
import os
import tempfile
import pytest
from datetime import datetime
from game.state import (
    GameState, GameEvent, has_saved_game, 
    create_new_game, load_saved_game
)


class TestGameEvent:
    """Test cases for GameEvent dataclass."""
    
    def test_game_event_creation(self):
        """Test creating a GameEvent."""
        event = GameEvent(
            timestamp="2023-01-01T12:00:00",
            round_number=1,
            team="Red",
            action="add_fixed:5",
            description="Red team gains 5 points",
            score_changes={"Red": 5}
        )
        
        assert event.timestamp == "2023-01-01T12:00:00"
        assert event.round_number == 1
        assert event.team == "Red"
        assert event.action == "add_fixed:5"
        assert event.description == "Red team gains 5 points"
        assert event.score_changes == {"Red": 5}


class TestGameState:
    """Test cases for GameState class."""
    
    def setup_method(self):
        """Set up test with temporary state file."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.state_path = self.temp_file.name
        # Remove empty file
        os.unlink(self.state_path)
        
        self.teams = ["Red", "Blue", "Green"]
        self.game_state = GameState(
            teams=self.teams,
            starting_points=15,
            starting_round=2,
            state_file=self.state_path
        )
    
    def teardown_method(self):
        """Clean up temporary files."""
        if os.path.exists(self.state_path):
            os.unlink(self.state_path)
    
    def test_initial_state(self):
        """Test initial game state is correct."""
        assert self.game_state.teams == self.teams
        assert self.game_state.get_scores() == {"Red": 15, "Blue": 15, "Green": 15}
        assert self.game_state.get_current_round() == 2
        assert self.game_state.get_current_team() == "Red"
        assert len(self.game_state.events) == 0
    
    def test_state_file_creation(self):
        """Test that state file is created automatically."""
        assert os.path.exists(self.state_path)
        
        with open(self.state_path, 'r') as f:
            state_data = json.load(f)
        
        assert state_data["teams"] == self.teams
        assert state_data["scores"] == {"Red": 15, "Blue": 15, "Green": 15}
        assert state_data["current_round"] == 2
    
    def test_update_scores(self):
        """Test updating scores and recording events."""
        score_changes = {"Red": 10, "Blue": -5}
        self.game_state.update_scores(
            score_changes=score_changes,
            team="Red",
            action="test_action",
            description="Test event"
        )
        
        scores = self.game_state.get_scores()
        assert scores["Red"] == 25  # 15 + 10
        assert scores["Blue"] == 10  # 15 - 5
        assert scores["Green"] == 15  # unchanged
        
        # Check event was recorded
        assert len(self.game_state.events) == 1
        event = self.game_state.events[0]
        assert event.team == "Red"
        assert event.action == "test_action"
        assert event.description == "Test event"
        assert event.score_changes == score_changes
    
    def test_scores_never_go_negative(self):
        """Test that scores are clamped to 0."""
        score_changes = {"Red": -20}  # More than starting points
        self.game_state.update_scores(
            score_changes=score_changes,
            team="Red",
            action="big_loss",
            description="Red loses big"
        )
        
        scores = self.game_state.get_scores()
        assert scores["Red"] == 0  # Clamped to 0, not -5
    
    def test_next_turn(self):
        """Test advancing turns."""
        assert self.game_state.get_current_team() == "Red"
        
        next_team = self.game_state.next_turn()
        assert next_team == "Blue"
        assert self.game_state.get_current_team() == "Blue"
        
        self.game_state.next_turn()
        assert self.game_state.get_current_team() == "Green"
        
        # Should wrap around
        self.game_state.next_turn()
        assert self.game_state.get_current_team() == "Red"
    
    def test_next_round(self):
        """Test advancing rounds."""
        # Advance to Blue's turn
        self.game_state.next_turn()
        assert self.game_state.get_current_team() == "Blue"
        
        # Advance round - should reset to Red and increment round
        new_round = self.game_state.next_round()
        assert new_round == 3
        assert self.game_state.get_current_round() == 3
        assert self.game_state.get_current_team() == "Red"  # Reset to first team
    
    def test_round_events(self):
        """Test getting events for specific rounds."""
        # Add events to round 2
        self.game_state.update_scores({"Red": 5}, "Red", "test1", "Event 1")
        self.game_state.update_scores({"Blue": 3}, "Blue", "test2", "Event 2")
        
        # Advance to round 3
        self.game_state.next_round()
        
        # Add event to round 3
        self.game_state.update_scores({"Green": 2}, "Green", "test3", "Event 3")
        
        # Check round 2 events
        round_2_events = self.game_state.get_round_events(2)
        assert len(round_2_events) == 2
        assert round_2_events[0].description == "Event 1"
        assert round_2_events[1].description == "Event 2"
        
        # Check round 3 events
        round_3_events = self.game_state.get_round_events(3)
        assert len(round_3_events) == 1
        assert round_3_events[0].description == "Event 3"
        
        # Check current round (should be 3)
        current_events = self.game_state.get_round_events()
        assert len(current_events) == 1
        assert current_events[0].description == "Event 3"
    
    def test_game_summary(self):
        """Test game summary formatting."""
        # Update some scores
        self.game_state.update_scores({"Red": 10, "Blue": -5}, "Red", "test", "Test")
        
        summary = self.game_state.get_game_summary()
        
        assert "Current Game State" in summary
        assert "Round: 2" in summary
        assert "Current Turn: Red" in summary
        assert "Red: 25 points <-- Current turn" in summary
        assert "Total Events: 1" in summary
    
    def test_round_history(self):
        """Test round history formatting."""
        # Add some events
        self.game_state.update_scores({"Red": 5}, "Red", "test1", "Red gains 5")
        self.game_state.update_scores({"Blue": 3}, "Blue", "test2", "Blue gains 3")
        
        history = self.game_state.get_round_history()
        
        assert "Round 2 History" in history
        assert "Red gains 5" in history
        assert "Blue gains 3" in history
        
        # Test empty round
        self.game_state.next_round()
        empty_history = self.game_state.get_round_history()
        assert "No events yet this round" in empty_history
    
    def test_state_persistence(self):
        """Test that state changes are saved and can be loaded."""
        # Make some changes
        self.game_state.update_scores({"Red": 7}, "Red", "test", "Test event")
        self.game_state.next_turn()
        self.game_state.next_round()
        
        # Load state from file
        loaded_state = GameState.load_state(self.state_path)
        
        assert loaded_state is not None
        assert loaded_state.teams == self.teams
        assert loaded_state.get_scores()["Red"] == 22  # 15 + 7
        assert loaded_state.get_current_team() == "Red"  # Reset on new round
        assert loaded_state.get_current_round() == 3
        assert len(loaded_state.events) == 1
        assert loaded_state.events[0].description == "Test event"
    
    def test_load_nonexistent_state(self):
        """Test loading state from nonexistent file."""
        loaded_state = GameState.load_state("nonexistent.json")
        assert loaded_state is None
    
    def test_load_invalid_state(self):
        """Test loading state from invalid file."""
        # Create invalid JSON file
        with open(self.state_path, 'w') as f:
            f.write("invalid json")
        
        loaded_state = GameState.load_state(self.state_path)
        assert loaded_state is None
    
    def test_delete_save_file(self):
        """Test deleting save file."""
        assert os.path.exists(self.state_path)
        
        self.game_state.delete_save_file()
        assert not os.path.exists(self.state_path)


class TestUtilityFunctions:
    """Test utility functions."""
    
    def setup_method(self):
        """Set up test with temporary file."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.state_path = self.temp_file.name
        os.unlink(self.state_path)
    
    def teardown_method(self):
        """Clean up."""
        if os.path.exists(self.state_path):
            os.unlink(self.state_path)
    
    def test_has_saved_game_false(self):
        """Test has_saved_game with no file."""
        assert not has_saved_game(self.state_path)
    
    def test_has_saved_game_true(self):
        """Test has_saved_game with valid file."""
        # Create game state
        game_state = create_new_game(["Red", "Blue"], state_file=self.state_path)
        
        assert has_saved_game(self.state_path)
    
    def test_has_saved_game_invalid_file(self):
        """Test has_saved_game with invalid file."""
        with open(self.state_path, 'w') as f:
            f.write("invalid")
        
        assert not has_saved_game(self.state_path)
    
    def test_create_new_game(self):
        """Test create_new_game function."""
        teams = ["Alpha", "Beta"]
        game_state = create_new_game(teams, starting_points=20, state_file=self.state_path)
        
        assert game_state.teams == teams
        assert game_state.get_scores() == {"Alpha": 20, "Beta": 20}
        assert os.path.exists(self.state_path)
    
    def test_load_saved_game(self):
        """Test load_saved_game function."""
        # Create and save a game
        original = create_new_game(["Red", "Blue"], state_file=self.state_path)
        original.update_scores({"Red": 5}, "Red", "test", "Test")
        
        # Load it back
        loaded = load_saved_game(self.state_path)
        
        assert loaded is not None
        assert loaded.get_scores()["Red"] == 15  # 10 + 5
        assert len(loaded.events) == 1
    
    def test_load_saved_game_nonexistent(self):
        """Test load_saved_game with nonexistent file."""
        loaded = load_saved_game("nonexistent.json")
        assert loaded is None