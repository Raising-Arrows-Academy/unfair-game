"""
CLI command handlers for the Unfair Review Game.

Contains handlers for different CLI commands to keep main.py clean.
"""

import sys
import os

from .config import GameConfig
from .state import create_new_game, load_saved_game
from .wheel import create_wheel, pick_random_starting_team


def handle_start_command(args, config: GameConfig) -> None:
    """Handle the start command."""
    # Validate team names
    if len(args.teams) < 2:
        print("Error: At least 2 teams are required")
        sys.exit(1)

    if len(set(args.teams)) != len(args.teams):
        print("Error: Team names must be unique")
        sys.exit(1)

    # Create new game
    starting_points = args.points if args.points is not None else config.get_starting_points()
    game_state = create_new_game(args.teams, starting_points, state_file=args.state)

    # Pick starting team
    if args.random_start:
        starting_team = pick_random_starting_team(args.teams)
        game_state.set_current_team(starting_team)
        print(f"Random starting team selected: {starting_team}")

    # Show initial status
    print(f"New game started with teams: {', '.join(args.teams)}")
    print(f"Starting points: {starting_points}")
    print(f"Current team: {game_state.get_current_team()}")
    print("\nUse 'python main.py spin' to spin the wheel!")


def handle_spin_command(args, config: GameConfig) -> None:
    """Handle the spin command."""
    # Load existing game
    if not os.path.exists(args.state):
        print(f"Error: No saved game found at {args.state}")
        print("Use 'python main.py start' to create a new game")
        sys.exit(1)

    game_state = load_saved_game(args.state)
    wheel = create_wheel(config, game_state)

    # Check if game is over
    if wheel.is_game_over():
        print(wheel.get_game_status())
        return

    # Determine which team is spinning
    spinning_team = args.team if args.team else game_state.get_current_team()

    # Validate team name
    if spinning_team not in game_state.get_teams():
        print(f"Error: Team '{spinning_team}' not found")
        print(f"Available teams: {', '.join(game_state.get_teams())}")
        sys.exit(1)

    # Spin the wheel!
    print(f"\n{spinning_team} is spinning the wheel...")
    print("-" * 40)

    outcome, team = wheel.spin_and_process(spinning_team)

    # Display results
    print(f"🎯 {outcome.label}")
    print(f"📝 {outcome.description}")

    if outcome.score_changes:
        print("\n📊 Score Changes:")
        for team_name, change in outcome.score_changes.items():
            sign = "+" if change >= 0 else ""
            print(f"   {team_name}: {sign}{change}")

    # Show current scores
    print("\n🏆 Current Scores:")
    scores = game_state.get_scores()
    sorted_teams = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    for i, (team_name, score) in enumerate(sorted_teams, 1):
        marker = "👑 " if i == 1 else "   "
        print(f"{marker}{team_name}: {score}")

    # If team wasn't specified, advance to next turn
    if not args.team:
        next_team = wheel.advance_turn()
        print(f"\nNext turn: {next_team}")

    # Check for game over
    if wheel.is_game_over():
        print("\n" + "="*40)
        print(wheel.get_game_status())


def handle_load_command(args, config: GameConfig) -> None:
    """Handle the load command."""
    if not os.path.exists(args.file):
        print(f"Error: File '{args.file}' not found")
        sys.exit(1)

    try:
        game_state = load_saved_game(args.file)
        wheel = create_wheel(config, game_state)

        # Copy to default state file
        if args.file != args.state:
            game_state.state_file = args.state
            game_state.save_state()

        print(f"Game loaded from {args.file}")
        print(wheel.get_game_status())

    except Exception as e:
        print(f"Error loading game: {e}")
        sys.exit(1)


def handle_config_command(args, config: GameConfig) -> None:
    """Handle config subcommands."""
    if args.config_action == "show":
        print("Current Configuration:")
        print("=" * 40)
        print(config.display_config())

    elif args.config_action == "edit":
        print("Interactive Configuration Editor")
        print("=" * 40)
        print("Press Enter to keep current value")
        print()

        # Edit basic settings
        try:
            new_starting = input(f"Starting points ({config.get_starting_points()}): ").strip()
            if new_starting:
                config.update_starting_points(int(new_starting))

            new_max = input(f"Max points ({config.get_max_points() or 'unlimited'}): ").strip()
            if new_max:
                config.update_max_points(int(new_max))

            new_rounds = input(f"Max rounds ({config.get_max_rounds() or 'unlimited'}): ").strip()
            if new_rounds:
                config.update_max_rounds(int(new_rounds))

            config.save_config()
            print("\nConfiguration saved!")

        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
        except KeyboardInterrupt:
            print("\nConfiguration editing cancelled")

    else:
        print("Error: Use 'show' or 'edit' with config command")
        sys.exit(1)


def handle_status_command(args, config: GameConfig) -> None:
    """Handle the status command."""
    if not os.path.exists(args.state):
        print("No active game found")
        print("Use 'python main.py start' to create a new game")
        return

    try:
        game_state = load_saved_game(args.state)
        wheel = create_wheel(config, game_state)
        print(wheel.get_game_status())
    except Exception as e:
        print(f"Error loading game status: {e}")