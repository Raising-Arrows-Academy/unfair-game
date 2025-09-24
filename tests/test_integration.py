"""
Integration tests for the Unfair Review Game.

Tests the interaction between different components to ensure
they work together correctly.
"""

import os
import tempfile
import pytest
from game.config import GameConfig
from game.state import create_new_game, load_saved_game
from game.wheel import create_wheel


class TestGameIntegration:
    """Integration tests for complete game functionality."""
    
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
    
    def teardown_method(self):
        """Clean up temporary files."""
        for path in [self.config_path, self.state_path]:
            if os.path.exists(path):
                os.unlink(path)
    
    def test_complete_game_flow(self):
        """Test a complete game flow from creation to completion."""
        # Create configuration
        config = GameConfig(self.config_path)
        
        # Customize configuration
        config.update_teams(["Warriors", "Knights", "Dragons"])
        config.update_starting_points(15)
        config.update_max_points(50)  # Game ends at 50 points
        
        # Create new game
        game_state = create_new_game(
            teams=["Warriors", "Knights", "Dragons"],
            starting_points=15,
            state_file=self.state_path
        )
        
        # Create wheel
        wheel = create_wheel(config, game_state)
        
        # Initial state verification
        assert game_state.get_current_team() == "Warriors"
        assert game_state.get_current_round() == 1
        assert game_state.get_scores() == {"Warriors": 15, "Knights": 15, "Dragons": 15}
        
        # Simulate several turns
        spin_count = 0
        max_spins = 50  # Safety limit to prevent infinite loops
        
        while not wheel.is_game_over() and spin_count < max_spins:
            current_team = game_state.get_current_team()
            scores_before = game_state.get_scores()
            
            # Spin the wheel
            outcome, team = wheel.spin_and_process()
            
            # Verify outcome is processed
            assert outcome.label is not None
            assert outcome.description is not None
            assert team == current_team
            
            # Verify scores changed or stayed the same
            scores_after = game_state.get_scores()
            if outcome.score_changes:
                for team_name, change in outcome.score_changes.items():
                    expected_score = max(0, scores_before[team_name] + change)
                    # Account for potential point cap
                    if config.get_max_points() > 0:
                        expected_score = min(expected_score, config.get_max_points())
                    assert scores_after[team_name] == expected_score
            
            # Advance turn and verify
            next_team = wheel.advance_turn()
            assert game_state.get_current_team() == next_team
            
            spin_count += 1
        
        # Game should either be over or we hit the safety limit
        if wheel.is_game_over():
            # Verify game over conditions
            status = wheel.get_game_status()
            assert "GAME OVER" in status
            
            # Check if someone reached the point limit
            scores = game_state.get_scores()
            max_score = max(scores.values())
            if config.get_max_points() > 0:
                assert max_score >= config.get_max_points() or game_state.get_current_round() > config.get_max_rounds()
        
        # Verify state persistence
        game_state.save_state()
        assert os.path.exists(self.state_path)
        
        # Load the saved game and verify it matches
        loaded_game = load_saved_game(self.state_path)
        assert loaded_game is not None
        assert loaded_game.teams == game_state.teams
        assert loaded_game.get_scores() == game_state.get_scores()
        assert loaded_game.get_current_round() == game_state.get_current_round()
        assert loaded_game.get_current_team() == game_state.get_current_team()
        assert len(loaded_game.events) == len(game_state.events)
    
    def test_config_state_integration(self):
        """Test integration between configuration and game state."""
        # Create configuration with custom settings
        config = GameConfig(self.config_path)
        config.update_starting_points(25)
        config.update_max_rounds(5)
        
        # Create game with different starting points (should use game parameter)
        game_state = create_new_game(
            teams=["Team1", "Team2"],
            starting_points=20,  # Different from config
            state_file=self.state_path
        )
        
        # Game should use the parameter, not config
        assert game_state.get_scores()["Team1"] == 20
        assert game_state.get_scores()["Team2"] == 20
        
        # But wheel should use config for game rules
        wheel = create_wheel(config, game_state)
        
        # Advance to round 6 (beyond max_rounds)
        for _ in range(6):
            wheel.advance_round()
        
        # Game should be over due to round limit
        assert wheel.is_game_over()
    
    def test_wheel_state_synchronization(self):
        """Test that wheel and state stay synchronized."""
        config = GameConfig(self.config_path)
        game_state = create_new_game(["Alpha", "Beta"], state_file=self.state_path)
        wheel = create_wheel(config, game_state)
        
        initial_round = game_state.get_current_round()
        initial_team = game_state.get_current_team()
        
        # Use wheel to advance turn
        next_team = wheel.advance_turn()
        
        # State should be updated
        assert game_state.get_current_team() == next_team
        assert game_state.get_current_round() == initial_round  # Same round
        
        # Use wheel to advance round
        new_round = wheel.advance_round()
        
        # State should be updated
        assert game_state.get_current_round() == new_round
        assert game_state.get_current_team() == "Alpha"  # Reset to first team
    
    def test_error_recovery(self):
        """Test game recovery from various error conditions."""
        config = GameConfig(self.config_path)
        game_state = create_new_game(["Red", "Blue"], state_file=self.state_path)
        
        # Simulate corrupted state by modifying scores directly
        game_state.scores["Red"] = -10  # Invalid negative score
        
        # Game should auto-correct on next score update
        wheel = create_wheel(config, game_state)
        outcome, _ = wheel.spin_and_process("Red")
        
        # Negative scores should be corrected to 0
        assert game_state.get_scores()["Red"] >= 0
    
    def test_event_tracking_integration(self):
        """Test that events are properly tracked across components."""
        config = GameConfig(self.config_path)
        game_state = create_new_game(["Team1", "Team2"], state_file=self.state_path)
        wheel = create_wheel(config, game_state)
        
        initial_events = len(game_state.events)
        
        # Perform several actions
        wheel.spin_and_process("Team1")
        wheel.advance_turn()
        wheel.advance_round()
        
        # Events should be recorded
        assert len(game_state.events) > initial_events
        
        # Events should have proper round tracking
        events = game_state.events
        for event in events:
            assert event.round_number > 0
            assert event.timestamp is not None
            assert event.action is not None
    
    def test_configuration_changes_during_game(self):
        """Test that configuration changes affect ongoing games appropriately."""
        config = GameConfig(self.config_path)
        game_state = create_new_game(["Red", "Blue"], starting_points=10, state_file=self.state_path)
        wheel = create_wheel(config, game_state)
        
        # Initially, no point limit
        assert not wheel.is_game_over()
        
        # Set a low point limit
        config.update_max_points(15)
        
        # Give a team enough points to exceed limit
        game_state.update_scores({"Red": 10}, "Red", "test", "Test points")
        
        # Game should now be over
        assert wheel.is_game_over()
        
        # Verify game status reflects the win condition
        status = wheel.get_game_status()
        assert "GAME OVER" in status
        assert "Red" in status