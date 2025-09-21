# Copilot Instructions - Unfair Review Game

## Project Overview
This is an educational CLI-based review game for classrooms. The game allows teachers to run interactive review sessions with teams competing through a "wheel of fortune" style system with various outcomes (points, steals, swaps, etc.).

## Target Audience
- **Primary**: Teachers running classroom review games
- **Secondary**: Students learning Python (new to programming)

## Core Design Principles

### 1. Clean Code & Readability
- **Primary Goal**: Keep code clean, readable, and well-documented
- Code should be understandable by Python beginners
- Use descriptive variable names and clear function signatures
- Include docstrings for all modules, classes, and functions
- Prefer explicit over implicit where it aids readability

### 2. Separation of Concerns
Maintain clear file organization with distinct responsibilities:

```
main.py          # Entry point, argument parsing, orchestration
game/            # Game package containing core functionality
  __init__.py    # Package initialization
  config.py      # Configuration management (load/save/edit)
  state.py       # Game state management and persistence
  wheel.py       # Wheel mechanics and outcome processing (future)
  interactive.py # Interactive menu system (future)
  utils.py       # Shared utilities and helpers (future)
tests/           # Test directory with pytest tests
```

### 3. Dual Mode Architecture
Support both command-line and interactive modes:
- **Direct Mode**: `python main.py spin Blue` - for quick operations
- **Interactive Mode**: `python main.py --interactive` - for full sessions
- **Configuration**: `python main.py config edit` - for setup

### 4. Dependency Management
- **Minimize Dependencies**: Prefer Python standard library when possible
- **Allow Dependencies**: When they significantly improve code quality or user experience
- **Document**: All dependencies must be in requirements.txt with version constraints
- **Justify**: External dependencies should have clear benefits over built-in alternatives

## Technical Standards

### CLI Framework
- **Use argparse**: Python's built-in argument parsing
- **Subcommands**: Organize functionality with clear command structure
- **Help System**: Leverage argparse's automatic help generation
- **Validation**: Use argparse choices and validation features

### Configuration Management
- **Format**: JSON for human-readability and ease of editing
- **Default Config**: Include sensible defaults that work out-of-the-box
- **Flexibility**: Allow runtime configuration changes
- **Persistence**: Save user customizations automatically
- **Structure**: Separate game settings, teams, and wheel configuration

### File Organization
Each file should have a single, clear responsibility:
- Import only what's needed
- Keep functions focused and small
- Use consistent naming conventions
- Group related functionality together

### Error Handling
- Graceful degradation when possible
- Clear error messages for users (not just developers)
- Input validation at appropriate boundaries
- Handle common edge cases (empty teams, invalid configurations, etc.)

## Development Workflow

### Environment Setup
- Python 3.12+ with virtual environment (.venv)
- Comprehensive .gitignore for Python projects
- requirements.txt for dependency tracking

### Code Style
- Follow PEP 8 guidelines
- Use meaningful variable names
- Keep functions under 20 lines when possible
- Document complex logic with comments
- Use flake8 for linting (configured in CI)

### Testing Strategy
- **Framework**: Use pytest for all automated testing
- **Coverage**: Aim for good test coverage, especially core game logic
- **Test Types**: Unit tests for individual functions, integration tests for CLI commands
- **Test-Driven Development**: Write tests alongside new features when possible
- **Manual Testing**: Focus on user experience and edge cases
- **CLI Testing**: Test both direct commands and interactive modes
- **Config Testing**: Validate configuration loading/saving/editing
- **Continuous Integration**: GitHub Actions workflow runs tests on all Python versions (3.10, 3.11, 3.12)

## Implementation History & Context

### Starting Point
- Had a monolithic `main.py` with all game logic
- Decided to start fresh with clean architecture
- Preserved original as `to_replace_main.py` for reference

### Key Decisions Made
1. **CLI Framework**: Chose argparse over click/rich for minimal dependencies
2. **Config Format**: JSON over YAML/TOML for simplicity and built-in support
3. **Architecture**: Modular design over monolithic for maintainability
4. **Dual Mode**: Both CLI and interactive to support different use cases

### Current Status
- Basic project structure established
- Virtual environment configured
- Starting with clean slate in main.py
- Ready to implement modular architecture

## Future Considerations
- Consider rich library for better CLI output if complexity grows
- Evaluate adding preset configurations for different grade levels
- Potential web interface as separate project
- Plugin system for custom wheel outcomes

## Questions for Implementation
When implementing new features, consider:
1. Does this maintain separation of concerns?
2. Is this readable by a Python beginner?
3. Can this be done with standard library?
4. Does this improve the teacher/student experience?
5. Is the CLI interface intuitive?
6. Are there tests for this functionality?
7. Do all tests pass after changes?

## Notes for Copilot
- Always check current file structure before making changes
- Prefer creating new files over modifying existing when adding major features
- Test CLI commands after implementation
- Keep educational context in mind - this code will be read by students
- Document any non-obvious design decisions
- Maintain consistency with established patterns