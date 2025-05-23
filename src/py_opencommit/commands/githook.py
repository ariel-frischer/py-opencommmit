import os
import stat
import sys
from pathlib import Path

from py_opencommit.config import get_config
from py_opencommit.i18n import get_text
from rich.console import Console

console = Console()

# Define the hook content as a constant
HOOK_CONTENT = """#!/usr/bin/env python3
# PyOC Git Hook
# This hook is installed by py-opencommit

import sys
import subprocess
import os

# Get the commit message file path from the arguments
commit_msg_file = sys.argv[1]

# Read the current commit message
with open(commit_msg_file, 'r') as f:
    commit_msg = f.read()

# Skip for merge commits
if commit_msg.startswith('Merge'):
    sys.exit(0)

# Skip if environment variable is set
if os.environ.get('SKIP_OC'):
    sys.exit(0)

try:
    # Run oco command
    result = subprocess.run(['oco', 'commit', '--skip-confirmation'], 
                          capture_output=True, text=True, check=True)
    
    # Get the output
    commit_msg = result.stdout.strip()
    
    # Write the new commit message
    with open(commit_msg_file, 'w') as f:
        f.write(commit_msg)
        
except subprocess.CalledProcessError as e:
    print(f"Error running oco: {e.stderr}")
    sys.exit(1)
except Exception as e:
    print(f"Error: {str(e)}")
    sys.exit(1)
"""


def get_git_root():
    """Get the root directory of the git repository."""
    git_dir = Path(".git")
    if git_dir.exists():
        return os.getcwd()
    return None


def githook():
    """
    Set up the git hook for the current repository.
    """
    git_root = get_git_root()
    if not git_root:
        console.print(f"[bold red]Error:[/bold red] Not a git repository")
        return False

    try:
        # Create hooks directory if it doesn't exist
        hooks_dir = Path(git_root) / ".git" / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)

        # Create the hook file
        hook_path = hooks_dir / "prepare-commit-msg"
        with open(hook_path, "w") as f:
            f.write(HOOK_CONTENT)

        # Set executable permissions
        os.chmod(hook_path, stat.S_IEXEC | stat.S_IREAD | stat.S_IWRITE)

        console.print("[bold green]Success:[/bold green] Git hook installed successfully!")
        return True
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        return False


def remove_githook():
    """
    Remove the git hook from the current repository.
    """
    git_root = get_git_root()
    if not git_root:
        console.print(f"[bold red]Error:[/bold red] Not a git repository")
        return False

    try:
        hook_path = Path(git_root) / ".git" / "hooks" / "prepare-commit-msg"
        if hook_path.exists():
            hook_path.unlink()
            console.print("[bold green]Success:[/bold green] Git hook removed successfully!")
            return True
        else:
            console.print("[bold yellow]Warning:[/bold yellow] Git hook not found")
            return False
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        return False
