#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Running pre-commit checks...${NC}"

# Get staged Python files
STAGED_PY_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.py$' || true)

if [ -z "$STAGED_PY_FILES" ]; then
    echo -e "${YELLOW}No Python files to check.${NC}"
else
    echo -e "${YELLOW}Checking Python files:${NC}"
    echo "$STAGED_PY_FILES"
    
    # Format with black
    echo -e "\n${YELLOW}Running black...${NC}"
    python -m black $STAGED_PY_FILES
    
    # Sort imports with isort
    echo -e "\n${YELLOW}Running isort...${NC}"
    python -m isort $STAGED_PY_FILES
    
    # Lint with flake8
    echo -e "\n${YELLOW}Running flake8...${NC}"
    python -m flake8 $STAGED_PY_FILES
    
    # Type check with mypy
    echo -e "\n${YELLOW}Running mypy...${NC}"
    python -m mypy $STAGED_PY_FILES
    
    # Lint with pylint
    echo -e "\n${YELLOW}Running pylint...${NC}"
    python -m pylint $STAGED_PY_FILES
    
    # Add back the formatted files to staging
    git add $STAGED_PY_FILES
fi

# Run the test suite
echo -e "\n${YELLOW}Running test suite...${NC}"
python -m pytest

echo -e "\n${GREEN}All checks passed!${NC}"