# OpenHands Scripts

This directory contains scripts and configurations for OpenHands microagents.

## Pre-commit Script

The `pre-commit.sh` script runs linting tools and the test suite before committing changes. It performs the following checks:

1. Formats Python code with `black`
2. Sorts imports with `isort`
3. Lints code with `flake8`
4. Type checks with `mypy`
5. Performs comprehensive linting with `pylint`
6. Runs the test suite with `pytest`

### Usage

To use this script as a git pre-commit hook, run:

```bash
ln -sf ../../.openhands/pre-commit.sh .git/hooks/pre-commit
```

This will create a symbolic link to the pre-commit script in the git hooks directory.

### Requirements

The script requires the following Python packages to be installed:

- black
- isort
- flake8
- mypy
- pylint
- pytest

You can install these packages with:

```bash
pip install -e ".[dev]"
```

or

```bash
python -m pip install black isort flake8 mypy pylint pytest
```