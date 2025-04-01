"""Tests for the OpenCommit githook command."""

import os
import stat
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from py_opencommit.commands.githook import githook, HOOK_CONTENT


def test_githook_not_in_git_repo():
    """Test githook command outside git repository."""
    with patch('py_opencommit.commands.githook.get_git_root', return_value=None):
        with patch('py_opencommit.commands.githook.console') as mock_console:
            githook()
            mock_console.print.assert_called_once()
            assert "Error" in mock_console.print.call_args[0][0]
            assert "Not a git repository" in mock_console.print.call_args[0][0]


def test_githook_installation():
    """Test successful githook installation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create fake .git directory
        git_dir = Path(temp_dir) / '.git'
        hooks_dir = git_dir / 'hooks'
        hooks_dir.mkdir(parents=True, exist_ok=True)
        
        # Run the githook function with mocked git_root
        with patch('py_opencommit.commands.githook.get_git_root', return_value=temp_dir):
            with patch('py_opencommit.commands.githook.console') as mock_console:
                githook()
                
                # Verify hook file was created
                hook_path = hooks_dir / 'prepare-commit-msg'
                assert hook_path.exists()
                
                # Verify file content
                with open(hook_path, 'r') as f:
                    content = f.read()
                    assert content == HOOK_CONTENT
                
                # Verify file permissions
                mode = os.stat(hook_path).st_mode
                assert bool(mode & stat.S_IEXEC)
                
                # Verify success message was printed
                mock_console.print.assert_any_call("[bold green]Success:[/bold green] Git hook installed successfully!")


def test_hook_content_validity():
    """Test that the hook content is valid Python code."""
    # This is a simple syntax check
    try:
        compile(HOOK_CONTENT, "<string>", "exec")
        is_valid = True
    except SyntaxError:
        is_valid = False
    
    assert is_valid, "The hook content contains invalid Python syntax"
    
    # Check for essential components in the hook
    assert "#!/usr/bin/env python3" in HOOK_CONTENT
    assert "import sys" in HOOK_CONTENT
    assert "import subprocess" in HOOK_CONTENT
    assert "commit_msg_file = sys.argv[1]" in HOOK_CONTENT
    assert "oco" in HOOK_CONTENT
    assert "commit" in HOOK_CONTENT


def test_githook_overwrite_existing():
    """Test githook overwrites existing hook."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create fake .git directory
        git_dir = Path(temp_dir) / '.git'
        hooks_dir = git_dir / 'hooks'
        hooks_dir.mkdir(parents=True, exist_ok=True)
        
        # Create existing hook with different content
        hook_path = hooks_dir / 'prepare-commit-msg'
        with open(hook_path, 'w') as f:
            f.write("#!/bin/sh\necho 'Existing hook'\n")
        
        # Run the githook function with mocked git_root
        with patch('py_opencommit.commands.githook.get_git_root', return_value=temp_dir):
            with patch('py_opencommit.commands.githook.console'):
                githook()
                
                # Verify file was overwritten
                with open(hook_path, 'r') as f:
                    content = f.read()
                    assert content == HOOK_CONTENT
                    assert "Existing hook" not in content


def test_hook_functionality_parsing():
    """Test the hook script's logic and structure instead of execution."""
    # Since executing the hook script is challenging in a test environment,
    # we'll just verify its key components are working as expected

    # Check if the script checks for commit messages first
    assert "with open(commit_msg_file, 'r') as f:" in HOOK_CONTENT
    assert "commit_msg = f.read()" in HOOK_CONTENT
    
    # Check if it handles merge commits
    assert "if commit_msg.startswith('Merge')" in HOOK_CONTENT
    assert "sys.exit(0)" in HOOK_CONTENT
    
    # Check if it executes oco command
    assert "['oco', 'commit'" in HOOK_CONTENT
    assert "subprocess.run" in HOOK_CONTENT
    
    # Check if it writes the result to the commit message file
    assert "with open(commit_msg_file, 'w') as f:" in HOOK_CONTENT
    assert "f.write(commit_msg)" in HOOK_CONTENT
    
    # Basic script structure validation
    assert "import sys" in HOOK_CONTENT
    assert "import subprocess" in HOOK_CONTENT
    assert "import os" in HOOK_CONTENT
    assert "commit_msg_file = sys.argv[1]" in HOOK_CONTENT


def test_hook_script_handles_merge_commit():
    """Test that the hook script handles merge commits correctly."""
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a temporary commit message file
        commit_msg_file = Path(temp_dir) / 'COMMIT_EDITMSG'
        with open(commit_msg_file, 'w') as f:
            f.write("Merge branch 'feature' into 'main'")
        
        # Prepare to execute the hook script
        hook_script = HOOK_CONTENT.replace("#!/usr/bin/env python3", "")
        
        # Create a mock subprocess module
        mock_subprocess = MagicMock()
        mock_run = MagicMock()
        mock_subprocess.run = mock_run
        mock_subprocess.CalledProcessError = Exception

        # Define globals for the exec environment, excluding sys
        hook_globals = {
            'subprocess': mock_subprocess,
            'os': MagicMock(path=MagicMock(exists=MagicMock(return_value=True)))
            # sys will be handled by the patch below
        }

        # Mock open to read merge commit message
        mock_open = MagicMock()
        mock_context = MagicMock()
        mock_context.__enter__.return_value.read.return_value = "Merge branch 'feature' into 'main'"
        mock_open.return_value = mock_context

        # Execute the hook script in our controlled environment
        # Patch sys.argv specifically for the exec call
        with patch('builtins.open', mock_open), \
             patch('sys.argv', ['prepare-commit-msg', str(commit_msg_file)]):
            try:
                # Pass only necessary globals, let exec find the patched sys
                exec(hook_script, hook_globals)
            except SystemExit as e:
                assert e.code == 0  # Expected to exit with success

        # Verify the script did NOT call subprocess.run (should skip for merge commits)
        mock_run.assert_not_called()
