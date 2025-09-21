"""
Tests for config.py module.

Tests configuration loading, saving, updating, and validation.
"""

import json
import os
import tempfile
import pytest
from config import GameConfig, load_config


class TestGameConfig:
    """Test cases for GameConfig class."""
    
    def setup_method(self):
        """Set up test with temporary config file."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.config_path = self.temp_file.name
        # Remove the empty file so GameConfig creates a new one
        os.unlink(self.config_path)
        self.config = GameConfig(self.config_path)
    
    def teardown_method(self):
        """Clean up temporary files."""
        if os.path.exists(self.config_path):
            os.unlink(self.config_path)
    
    def test_default_config_creation(self):
        """Test that default configuration is created correctly."""
        config = self.config.get_config()
        
        # Check all required keys exist
        assert "wheel_options" in config
        assert "teams" in config
        assert "starting_points" in config
        assert "max_points" in config
        assert "max_rounds" in config
        assert "starting_round" in config
        
        # Check default values
        assert len(config["wheel_options"]) == 10
        assert config["teams"] == ["Red", "Blue"]
        assert config["starting_points"] == 10
        assert config["max_points"] == 0
        assert config["max_rounds"] == 20
        assert config["starting_round"] == 1
    
    def test_config_file_creation(self):
        """Test that config file is created with defaults."""
        assert os.path.exists(self.config_path)
        
        with open(self.config_path, 'r') as f:
            saved_config = json.load(f)
        
        assert "teams" in saved_config
        assert saved_config["teams"] == ["Red", "Blue"]
    
    def test_load_existing_config(self):
        """Test loading configuration from existing file."""
        test_config = {
            "teams": ["Alpha", "Beta", "Gamma"],
            "starting_points": 15,
            "max_points": 100
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(test_config, f)
        
        config = GameConfig(self.config_path)
        assert config.get_teams() == ["Alpha", "Beta", "Gamma"]
        assert config.get_starting_points() == 15
        assert config.get_max_points() == 100
    
    def test_update_teams_valid(self):
        """Test updating teams with valid input."""
        new_teams = ["Warriors", "Knights", "Dragons"]
        self.config.update_teams(new_teams)
        assert self.config.get_teams() == new_teams
    
    def test_update_teams_invalid(self):
        """Test updating teams with invalid input."""
        with pytest.raises(ValueError):
            self.config.update_teams([])  # Empty list
        
        with pytest.raises(ValueError):
            self.config.update_teams(["OnlyOne"])  # Only one team
    
    def test_update_starting_points_valid(self):
        """Test updating starting points with valid values."""
        self.config.update_starting_points(25)
        assert self.config.get_starting_points() == 25
        
        self.config.update_starting_points(0)
        assert self.config.get_starting_points() == 0
    
    def test_update_starting_points_invalid(self):
        """Test updating starting points with invalid values."""
        with pytest.raises(ValueError):
            self.config.update_starting_points(-5)
    
    def test_update_max_points_valid(self):
        """Test updating max points with valid values."""
        self.config.update_max_points(50)
        assert self.config.get_max_points() == 50
        
        self.config.update_max_points(0)  # No limit
        assert self.config.get_max_points() == 0
    
    def test_update_max_points_invalid(self):
        """Test updating max points with invalid values."""
        with pytest.raises(ValueError):
            self.config.update_max_points(-10)
    
    def test_update_max_rounds_valid(self):
        """Test updating max rounds with valid values."""
        self.config.update_max_rounds(30)
        assert self.config.get_max_rounds() == 30
    
    def test_update_max_rounds_invalid(self):
        """Test updating max rounds with invalid values."""
        with pytest.raises(ValueError):
            self.config.update_max_rounds(0)
        
        with pytest.raises(ValueError):
            self.config.update_max_rounds(-5)
    
    def test_update_starting_round_valid(self):
        """Test updating starting round with valid values."""
        self.config.update_starting_round(3)
        assert self.config.get_starting_round() == 3
    
    def test_update_starting_round_invalid(self):
        """Test updating starting round with invalid values."""
        with pytest.raises(ValueError):
            self.config.update_starting_round(0)
        
        with pytest.raises(ValueError):
            self.config.update_starting_round(-1)
    
    def test_update_wheel_options_valid(self):
        """Test updating wheel options with valid data."""
        new_options = [
            {"label": "Test 1", "action": "test:1", "weight": 1},
            {"label": "Test 2", "action": "test:2", "weight": 2}
        ]
        self.config.update_wheel_options(new_options)
        assert self.config.get_wheel_options() == new_options
    
    def test_update_wheel_options_invalid(self):
        """Test updating wheel options with invalid data."""
        with pytest.raises(ValueError):
            self.config.update_wheel_options([])  # Empty list
        
        with pytest.raises(ValueError):
            # Missing required keys
            self.config.update_wheel_options([{"label": "Test"}])
        
        with pytest.raises(ValueError):
            # Invalid weight
            invalid_options = [{"label": "Test", "action": "test", "weight": 0}]
            self.config.update_wheel_options(invalid_options)
    
    def test_display_config(self):
        """Test configuration display format."""
        display = self.config.display_config()
        
        assert "Current Game Configuration" in display
        assert "Teams:" in display
        assert "Starting Points:" in display
        assert "Maximum Points:" in display
        assert "Wheel Options:" in display
        
        # Should show team names
        assert "Red" in display
        assert "Blue" in display
    
    def test_config_persistence(self):
        """Test that configuration changes persist after reload."""
        # Update configuration
        self.config.update_teams(["Persistent", "Test"])
        self.config.update_starting_points(42)
        
        # Create new config instance with same file
        new_config = GameConfig(self.config_path)
        
        # Verify changes persisted
        assert new_config.get_teams() == ["Persistent", "Test"]
        assert new_config.get_starting_points() == 42


def test_load_config_function():
    """Test the load_config convenience function."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        config_path = f.name
    
    try:
        config = load_config(config_path)
        assert isinstance(config, GameConfig)
        assert config.get_teams() == ["Red", "Blue"]
    finally:
        if os.path.exists(config_path):
            os.unlink(config_path)