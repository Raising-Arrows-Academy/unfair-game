"""
Main entry point for the Unfair Review Game.

A CLI-based educational review game for classrooms.
"""

import argparse
import sys
import os
from typing import Optional

from game.config import GameConfig
from game.state import GameState, create_new_game, load_saved_game
from game.wheel import GameWheel, create_wheel, pick_random_starting_team


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Unfair Review Game - Interactive classroom review game",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py start Red Blue Green          # Start new game with teams
  python main.py spin Blue                     # Spin wheel for Blue team
  python main.py load game.json                # Load saved game
  python main.py interactive                   # Start interactive mode
  python main.py config edit                   # Edit configuration
  python main.py config show                   # Show current configuration
        """
    )

    # Add global options
    parser.add_argument(
        "--config", "-c",
        default="config.json",
        help="Configuration file to use (default: config.json)"
    )
    parser.add_argument(
        "--state", "-s",
        default="game_state.json",
        help="Game state file to use (default: game_state.json)"
    )

    # Create subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Start command
    start_parser = subparsers.add_parser("start", help="Start a new game")
    start_parser.add_argument(
        "teams",
        nargs="+",
        help="Team names (e.g., Red Blue Green)"
    )
    start_parser.add_argument(
        "--points", "-p",
        type=int,
        help="Starting points for each team (uses config default if not specified)"
    )
    start_parser.add_argument(
        "--random-start", "-r",
        action="store_true",
        help="Pick random starting team"
    )

    # Spin command
    spin_parser = subparsers.add_parser("spin", help="Spin the wheel")
    spin_parser.add_argument(
        "team",
        nargs="?",
        help="Team name to spin for (uses current team if not specified)"
    )

    # Load command
    load_parser = subparsers.add_parser("load", help="Load a saved game")
    load_parser.add_argument(
        "file",
        help="Game state file to load"
    )

    # Interactive command
    subparsers.add_parser("interactive", help="Start interactive mode")

    # Config command
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_subparsers = config_parser.add_subparsers(dest="config_action")
    config_subparsers.add_parser("show", help="Show current configuration")
    config_subparsers.add_parser("edit", help="Edit configuration interactively")

    # Status command
    subparsers.add_parser("status", help="Show current game status")

    return parser


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

    # Create wheel and show initial status
    wheel = create_wheel(config, game_state)
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


def handle_interactive_mode(config: GameConfig, state_file: str) -> None:
    """Handle interactive mode."""
    print("🎯 Welcome to Unfair Review Game - Interactive Mode")
    print("=" * 50)

    # Check for existing game
    game_state = None
    if os.path.exists(state_file):
        try:
            game_state = load_saved_game(state_file)
            print("📁 Found existing game!")
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
        print("\n🆕 Starting new game")
        print("-" * 20)

        # Get teams
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

            break

        # Create game
        starting_points = config.get_starting_points()
        game_state = create_new_game(teams, starting_points, state_file=state_file)

        # Pick starting team
        choice = input("Pick random starting team? (y/n): ").strip().lower()
        if choice == 'y':
            starting_team = pick_random_starting_team(teams)
            game_state.set_current_team(starting_team)
            print(f"🎲 Random starting team: {starting_team}")

    # Main game loop
    wheel = create_wheel(config, game_state)

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

        # Menu options
        print("\nOptions:")
        print("1. Spin the wheel")
        print("2. Show full status")
        print("3. Change current team")
        print("4. Save and quit")
        print("5. Quit without saving")

        try:
            choice = input("\nChoose an option (1-5): ").strip()

            if choice == "1":
                # Spin the wheel
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

            elif choice == "2":
                # Show status
                print("\n" + wheel.get_game_status())
                input("\nPress Enter to continue...")

            elif choice == "3":
                # Change team
                teams = game_state.get_teams()
                print(f"\nAvailable teams: {', '.join(teams)}")
                new_team = input("Enter team name: ").strip()
                if new_team in teams:
                    game_state.set_current_team(new_team)
                    print(f"✅ Current team changed to {new_team}")
                else:
                    print("❌ Invalid team name")
                input("Press Enter to continue...")

            elif choice == "4":
                # Save and quit
                game_state.save_state()
                print("💾 Game saved! Goodbye!")
                break

            elif choice == "5":
                # Quit without saving
                confirm = input("Are you sure? Unsaved progress will be lost (y/n): ")
                if confirm.strip().lower() == 'y':
                    print("👋 Goodbye!")
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


def main():
    """Main entry point for the application."""
    parser = create_parser()
    args = parser.parse_args()

    # Load configuration
    try:
        config = GameConfig(args.config)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)

    # Handle commands
    try:
        if args.command == "start":
            handle_start_command(args, config)

        elif args.command == "spin":
            handle_spin_command(args, config)

        elif args.command == "load":
            handle_load_command(args, config)

        elif args.command == "config":
            handle_config_command(args, config)

        elif args.command == "status":
            handle_status_command(args, config)

        elif args.command == "interactive":
            handle_interactive_mode(config, args.state)

        else:
            # No command provided - show help or start interactive mode
            if len(sys.argv) == 1:
                print("🎯 Unfair Review Game")
                print("Use --help for command options or try interactive mode:")
                print("python main.py interactive")
            else:
                parser.print_help()

    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
