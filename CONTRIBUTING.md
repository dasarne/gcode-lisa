# Contributing to GCode Lisa

Thank you for contributing to GCode Lisa.

## Development Setup

```bash
git clone https://github.com/dasarne/gcode-lisa.git
cd gcode-lisa

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
pip install -e ".[dev]"
```

## Before Submitting Changes

Please ensure that:

```bash
pytest tests/
mypy src/
black src/ tests/
```

run successfully before opening a pull request.

## Pull Requests

- Keep pull requests focused and small where possible
- Add or update tests for new functionality
- Update documentation when behavior changes
- Use descriptive commit messages

## Code Style

- Python 3.10+
- PEP 8
- Type annotations preferred
- Line length: 100 characters

## Reporting Bugs

Please include:
- Steps to reproduce
- Expected behavior
- Actual behavior
- Example G-Code file if relevant
- Screenshots if UI-related
- Python and OS version

## Feature Requests

Feature requests should describe:
- The CNC/GCode workflow problem
- Expected UX behavior
- Dialect-specific constraints if applicable