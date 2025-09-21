"""
Interactive menu system for the Unfair Review Game.

Handles the full interactive game session with menu-driven interface.
"""

import os
from typing import Optional

from .config import GameConfig
from .state import GameState, create_new_game, load_saved_game
from .wheel import GameWheel, create_wheel, pick_random_starting_team


def run_interactive_mode(config: GameConfig, state_file: str) -> None:
    """
    Run the interactive game mode with full menu system.
    
    Args:
        config: Game configuration
        state_file: Path to game state file
    """
    print("🎯 Welcome to Unfair Review Game - Interactive Mode")
    print("=" * 50)

    # Check for existing game
    game_state = _load_or_create_game(config, state_file)
    
    # Main game loop
    wheel = create_wheel(config, game_state)
    _run_game_loop(wheel, game_state)


def _load_or_create_game(config: GameConfig, state_file: str) -> GameState:
    """
    Load existing game or create new one based on user choice.
    
    Args:
        config: Game configuration
        state_file: Path to game state file
        
    Returns:
        GameState instance
    """
    game_state = None
    
    # Check for existing game
    if os.path.exists(state_file):
        try:
            game_state = load_saved_game(state_file)
            print("📁 Found existing game!")
            
            # Show status
            wheel = create_wheel(config, game_state)
            print(wheel.get_game_status())

            choice = input("\nContinue this game? (y/n): ").strip().lower()
            if choice != 'y':
                game_state = None
        except Exception as e:
            print(f"⚠️  Could not load existing game: {e}")
            game_state = None

    # Start new game if needed
    if not game_state:
        game_state = _create_new_game_interactive(config, state_file)
    
    return game_state


def _create_new_game_interactive(config: GameConfig, state_file: str) -> GameState:
    """
    Create a new game through interactive prompts.
    
    Args:
        config: Game configuration
        state_file: Path to game state file
        
    Returns:
        New GameState instance
    """
    print("\n🆕 Starting new game")
    print("-" * 20)

    # Get teams
    teams = _get_team_names()
    
    # Create game
    starting_points = config.get_starting_points()
    game_state = create_new_game(teams, starting_points, state_file=state_file)

    # Pick starting team
    choice = input("Pick random starting team? (y/n): ").strip().lower()
    if choice == 'y':
        starting_team = pick_random_starting_team(teams)
        game_state.set_current_team(starting_team)
        print(f"🎲 Random starting team: {starting_team}")
    
    return game_state


def _get_team_names() -> list[str]:
    """
    Get team names from user input with validation.
    
    Returns:
        List of unique team names
    """
    while True:
        teams_input = input("Enter team names (space-separated): ").strip()
        if not teams_input:
            continue

        teams = teams_input.split()
        if len(teams) < 2:
            print("❌ At least 2 teams required")
            continue

        if len(set(teams)) != len(teams):
            print("❌ Team names must be unique")
            continue

        return teams


def _run_game_loop(wheel: GameWheel, game_state: GameState) -> None:
    """
    Run the main interactive game loop.
    
    Args:
        wheel: GameWheel instance
        game_state: Current game state
    """
    while True:
        print("\n" + "="*50)

        # Check for game over
        if wheel.is_game_over():
            print(wheel.get_game_status())
            break

        # Show current status
        current_team = game_state.get_current_team()
        scores = game_state.get_scores()
        print(f"🎯 Round {game_state.get_current_round()} - {current_team}'s turn")
        print(f"🏆 Scores: {', '.join(f'{team}: {score}' for team, score in scores.items())}")

        # Show menu and handle choice
        choice = _display_menu_and_get_choice()
        
        try:
            if choice == "1":
                _handle_spin_wheel(wheel, current_team)
            elif choice == "2":
                _handle_show_status(wheel)
            elif choice == "3":
                _handle_change_team(game_state)
            elif choice == "4":
                _handle_save_and_quit(game_state)
                break
            elif choice == "5":
                if _handle_quit_without_saving():
                    break
            else:
                print("❌ Invalid choice. Please enter 1-5.")
                input("Press Enter to continue...")

        except KeyboardInterrupt:
            print("\n\n💾 Saving game...")
            game_state.save_state()
            print("👋 Goodbye!")
            break
        except Exception as e:
            print(f"⚠️  Error: {e}")
            input("Press Enter to continue...")


def _display_menu_and_get_choice() -> str:
    """
    Display the main menu and get user choice.
    
    Returns:
        User's menu choice as string
    """
    print("\nOptions:")
    print("1. Spin the wheel")
    print("2. Show full status")
    print("3. Change current team")
    print("4. Save and quit")
    print("5. Quit without saving")
    
    return input("\nChoose an option (1-5): ").strip()


def _handle_spin_wheel(wheel: GameWheel, current_team: str) -> None:
    """
    Handle wheel spinning action.
    
    Args:
        wheel: GameWheel instance
        current_team: Name of current team
    """
    print(f"\n🎰 {current_team} is spinning the wheel...")
    print("-" * 40)

    outcome, team = wheel.spin_and_process()

    # Display results
    print(f"🎯 {outcome.label}")
    print(f"📝 {outcome.description}")

    if outcome.score_changes:
        print("\n📊 Score Changes:")
        for team_name, change in outcome.score_changes.items():
            sign = "+" if change >= 0 else ""
            print(f"   {team_name}: {sign}{change}")

    # Advance turn
    next_team = wheel.advance_turn()
    input(f"\nPress Enter to continue to {next_team}'s turn...")


def _handle_show_status(wheel: GameWheel) -> None:
    """
    Handle showing full game status.
    
    Args:
        wheel: GameWheel instance
    """
    print("\n" + wheel.get_game_status())
    input("\nPress Enter to continue...")


def _handle_change_team(game_state: GameState) -> None:
    """
    Handle changing the current team.
    
    Args:
        game_state: Current game state
    """
    teams = game_state.get_teams()
    print(f"\nAvailable teams: {', '.join(teams)}")
    new_team = input("Enter team name: ").strip()
    
    if new_team in teams:
        game_state.set_current_team(new_team)
        print(f"✅ Current team changed to {new_team}")
    else:
        print("❌ Invalid team name")
    
    input("Press Enter to continue...")


def _handle_save_and_quit(game_state: GameState) -> None:
    """
    Handle saving game and quitting.
    
    Args:
        game_state: Current game state
    """
    game_state.save_state()
    print("💾 Game saved! Goodbye!")


def _handle_quit_without_saving() -> bool:
    """
    Handle quitting without saving.
    
    Returns:
        True if user confirms quit, False otherwise
    """
    confirm = input("Are you sure? Unsaved progress will be lost (y/n): ")
    if confirm.strip().lower() == 'y':
        print("👋 Goodbye!")
        return True
    return False