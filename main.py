"""
Main entry point for the Unfair Review Game.

A CLI-based educational review game for classrooms.
"""

import argparse
import sys

from game.config import GameConfig
from game.interactive import run_interactive_mode, run_auto_spin_mode, run_simple_mode
from game.commands import (
    handle_start_command,
    handle_spin_command,
    handle_load_command,
    handle_config_command,
    handle_status_command
)


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
  python main.py simple                        # Simple mode (press Enter to spin)
  python main.py simple --verbose              # Simple mode with details
  python main.py auto-spin                     # Auto-spin mode (continuous)
  python main.py auto-spin --delay 1.5         # Auto-spin with custom delay
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
    
    # Auto-spin command
    auto_spin_parser = subparsers.add_parser("auto-spin", help="Auto-spin mode (continuous spinning with auto-save)")
    auto_spin_parser.add_argument(
        "--delay", "-d",
        type=float,
        default=2.0,
        help="Delay between spins in seconds (default: 2.0)"
    )
    
    # Simple command
    simple_parser = subparsers.add_parser("simple", help="Simple mode (press Enter to spin, minimal display)")
    simple_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed outcome information"
    )

    # Config command
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_subparsers = config_parser.add_subparsers(dest="config_action")
    config_subparsers.add_parser("show", help="Show current configuration")
    config_subparsers.add_parser("edit", help="Edit configuration interactively")

    # Status command
    subparsers.add_parser("status", help="Show current game status")

    return parser


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
            run_interactive_mode(config, args.state)

        elif args.command == "auto-spin":
            run_auto_spin_mode(config, args.state, args.delay)

        elif args.command == "simple":
            run_simple_mode(config, args.state, args.verbose)

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
