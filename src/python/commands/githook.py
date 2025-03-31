"""Githook command implementation for OpenCommit."""

import os
import stat
from pathlib import Path
from rich.console import Console

from src.python.utils.git import get_git_root

console = Console()

HOOK_CONTENT = """#!/usr/bin/env python3
import sys
import subprocess
import os

# Get the commit message file path
commit_msg_file = sys.argv[1]

# Check if this is an amended commit or a merge commit
if os.path.exists(commit_msg_file):
    with open(commit_msg_file, 'r') as f:
        commit_msg = f.read()
    
    # Skip if it's a merge commit or already has a message
    if commit_msg.startswith('Merge') or len(commit_msg.strip()) > 0:
        sys.exit(0)

# Run opencommit to generate the commit message
try:
    result = subprocess.run(
        ['oco', 'commit', '--skip-confirmation'],
        capture_output=True,
        text=True,
        check=True
    )
    
    # Extract the generated commit message
    commit_msg = result.stdout.strip()
    
    # Write the commit message to the file
    with open(commit_msg_file, 'w') as f:
        f.write(commit_msg)
    
    sys.exit(0)
except subprocess.CalledProcessError:
    # If opencommit fails, just continue with the normal commit process
    sys.exit(0)
"""


def githook() -> None:
    """Install the prepare-commit-msg git hook."""
    git_root = get_git_root()
    if not git_root:
        console.print("[bold red]Error:[/bold red] Not a git repository")
        return
    
    hooks_dir = Path(git_root) / '.git' / 'hooks'
    hook_path = hooks_dir / 'prepare-commit-msg'
    
    # Create the hook file
    with open(hook_path, 'w') as f:
        f.write(HOOK_CONTENT)
    
    # Make it executable
    os.chmod(hook_path, os.stat(hook_path).st_mode | stat.S_IEXEC)
    
    console.print("[bold green]Success:[/bold green] Git hook installed successfully!")
    console.print("The hook will automatically generate commit messages when you run 'git commit'.")
