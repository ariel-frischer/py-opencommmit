"""Tests for Git utilities."""

import os
import sys
import tempfile
import shutil
import subprocess
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, call


from src.python.utils.git import (
    GitError,
    _run_git_command,
    get_git_root,
    assert_git_repo,
    get_staged_files,
    get_changed_files,
    get_staged_diff,
    split_diff_by_files,
    merge_diffs,
    stage_files,
    stage_all_changes,
    get_commit_template,
    apply_commit_template,
    commit,
    has_staged_changes,
    has_unstaged_changes,
    get_repo_status,
    is_git_repository
)


class TestGitUtils:
    
    def test_git_error_class(self):
        """Test the GitError exception class."""
        error = GitError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
    
    def test_run_git_command(self):
        """Test the _run_git_command helper with mocked subprocess."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "test output"
            mock_run.return_value = mock_result
            
            result = _run_git_command(["git", "status"])
            assert result.stdout == "test output"
            mock_run.assert_called_once()
    
    def test_run_git_command_error(self):
        """Test _run_git_command error handling."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "git", stderr="fatal: not a git repository")
            
            with pytest.raises(GitError) as excinfo:
                _run_git_command(["git", "status"])
            
            # Just check that the error message contains the command and the word "fatal"
            assert "Git command failed" in str(excinfo.value)
            assert "git status" in str(excinfo.value)
            assert "fatal" in str(excinfo.value)
    
    def test_run_git_command_file_not_found(self):
        """Test _run_git_command with file not found error."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("No such file or directory: 'git'")
            
            with pytest.raises(GitError) as excinfo:
                _run_git_command(["git", "status"])
            
            assert "Git executable not found" in str(excinfo.value)
    
    def test_run_git_command_auto_adds_git(self):
        """Test that _run_git_command automatically adds 'git' as first argument if missing."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_run.return_value = mock_result
            
            _run_git_command(["status"])  # No 'git' prefix
            mock_run.assert_called_once()
            assert mock_run.call_args[0][0][0] == "git"
            assert mock_run.call_args[0][0][1] == "status"
    
    def test_get_git_root(self):
        """Test getting git repository root."""
        with patch('src.python.utils.git._run_git_command') as mock_cmd:
            mock_result = MagicMock()
            mock_result.stdout = "/path/to/repo\n"
            mock_cmd.return_value = mock_result
            
            result = get_git_root()
            assert result == "/path/to/repo"
            mock_cmd.assert_called_once_with(["git", "rev-parse", "--show-toplevel"])
    
    def test_get_git_root_error(self):
        """Test get_git_root error handling."""
        with patch('src.python.utils.git._run_git_command') as mock_cmd:
            mock_cmd.side_effect = GitError("Not a git repository")
            
            result = get_git_root()
            assert result is None
    
    def test_is_git_repository(self):
        """Test checking if current directory is a git repository."""
        with patch('src.python.utils.git.get_git_root') as mock_get_root:
            # Test with git repo
            mock_get_root.return_value = "/path/to/repo"
            assert is_git_repository() is True
            
            # Test without git repo
            mock_get_root.return_value = None
            assert is_git_repository() is False
    
    def test_assert_git_repo(self):
        """Test asserting that we're in a git repository."""
        with patch('src.python.utils.git._run_git_command') as mock_cmd:
            # Test success case
            assert_git_repo()  # Should not raise exception
            mock_cmd.assert_called_once_with(["git", "rev-parse", "--is-inside-work-tree"])
            
            # Test failure case
            mock_cmd.side_effect = GitError("Not a git repository")
            with pytest.raises(GitError) as excinfo:
                assert_git_repo()
            assert "Not in a git repository" in str(excinfo.value)
    
    def test_get_staged_files(self):
        """Test getting staged files."""
        with patch('src.python.utils.git._run_git_command') as mock_cmd:
            mock_result = MagicMock()
            mock_result.stdout = "file1.txt\nfile2.txt\ndir/file3.txt\n"
            mock_cmd.return_value = mock_result
            
            result = get_staged_files()
            assert result == ["file1.txt", "file2.txt", "dir/file3.txt"]
            mock_cmd.assert_called_once_with(["git", "diff", "--name-only", "--cached"])
    
    def test_get_changed_files(self):
        """Test getting all changed files (staged and unstaged)."""
        with patch('src.python.utils.git._run_git_command') as mock_cmd:
            # Mock two different calls for staged and unstaged files
            mock_cmd.side_effect = [
                MagicMock(stdout="file1.txt\nfile2.txt\n"),  # staged
                MagicMock(stdout="file2.txt\nfile3.txt\n")   # unstaged
            ]
            
            result = get_changed_files()
            # Should combine and deduplicate
            assert sorted(result) == ["file1.txt", "file2.txt", "file3.txt"]
            assert mock_cmd.call_count == 2
    
    def test_get_staged_diff(self):
        """Test getting staged diff."""
        with patch('src.python.utils.git._run_git_command') as mock_cmd:
            mock_result = MagicMock()
            mock_result.stdout = "diff --git a/file1.txt b/file1.txt\nindex 123..456 100644\n--- a/file1.txt\n+++ b/file1.txt\n"
            mock_cmd.return_value = mock_result
            
            result = get_staged_diff()
            assert result == mock_result.stdout
            mock_cmd.assert_called_once_with(["git", "diff", "--cached"])
    
    def test_get_staged_diff_error(self):
        """Test error handling in get_staged_diff."""
        with patch('src.python.utils.git._run_git_command') as mock_cmd:
            mock_cmd.side_effect = GitError("Command failed")
            
            with pytest.raises(GitError) as excinfo:
                get_staged_diff()
            assert "Failed to get staged diff" in str(excinfo.value)
    
    def test_split_diff_by_files(self):
        """Test splitting a diff by files."""
        test_diff = """diff --git a/file1.txt b/file1.txt
index 1234567..abcdef 100644
--- a/file1.txt
+++ b/file1.txt
@@ -1,3 +1,4 @@
 line1
 line2
+line3
diff --git a/file2.txt b/file2.txt
index 9876543..fedcba 100644
--- a/file2.txt
+++ b/file2.txt
@@ -1,2 +1 @@
-line1
 line2"""
        
        result = split_diff_by_files(test_diff)
        assert len(result) == 2
        assert "file1.txt" in result
        assert "file2.txt" in result
        assert "+line3" in result["file1.txt"]
        assert "-line1" in result["file2.txt"]
    
    def test_merge_diffs(self):
        """Test merging diffs with size limits."""
        diffs = [
            "a" * 500,
            "b" * 300,
            "c" * 400,
        ]
        
        # Test with a size limit that allows all diffs in one chunk
        result = merge_diffs(diffs, 1500)
        assert len(result) == 1
        assert len(result[0]) == 1200 + 2  # 1200 chars + 2 newlines
        
        # Test with a size limit that forces splitting
        result = merge_diffs(diffs, 600)
        assert len(result) == 3
        assert result[0] == "a" * 500
        assert result[1] == "b" * 300
        assert result[2] == "c" * 400
    
    def test_stage_files(self):
        """Test staging files."""
        with patch('src.python.utils.git._run_git_command') as mock_cmd:
            files = ["file1.txt", "file2.txt", "path/to/file3.txt"]
            stage_files(files)
            
            mock_cmd.assert_called_once()
            assert mock_cmd.call_args[0][0] == ["git", "add"] + files
    
    def test_stage_files_empty(self):
        """Test staging with empty file list."""
        with patch('src.python.utils.git._run_git_command') as mock_cmd:
            # Empty list should be a no-op
            stage_files([])
            mock_cmd.assert_not_called()
            
            # List with only empty strings should be a no-op
            stage_files(["", "  "])
            mock_cmd.assert_not_called()
    
    def test_stage_files_error(self):
        """Test error handling when staging files."""
        with patch('src.python.utils.git._run_git_command') as mock_cmd:
            mock_cmd.side_effect = GitError("Command failed")
            
            with pytest.raises(GitError) as excinfo:
                stage_files(["file1.txt"])
            
            assert "Failed to stage files" in str(excinfo.value)
    
    def test_stage_all_changes(self):
        """Test staging all changes."""
        with patch('src.python.utils.git._run_git_command') as mock_cmd:
            stage_all_changes()
            
            mock_cmd.assert_called_once_with(["git", "add", "-A"])
    
    def test_stage_all_changes_error(self):
        """Test error handling when staging all changes."""
        with patch('src.python.utils.git._run_git_command') as mock_cmd:
            mock_cmd.side_effect = GitError("Command failed")
            
            with pytest.raises(GitError) as excinfo:
                stage_all_changes()
            
            assert "Failed to stage all changes" in str(excinfo.value)
    
    def test_get_commit_template(self):
        """Test getting commit template."""
        with patch('src.python.utils.git._run_git_command') as mock_cmd, \
             patch('os.path.exists', return_value=True), \
             patch('builtins.open', MagicMock()):
            
            # Mock commit.template configuration
            mock_cmd.return_value = MagicMock(returncode=0, stdout="/path/to/template\n")
            
            # Mock file reading
            mock_file = MagicMock()
            mock_file.__enter__.return_value.read.return_value = "Template content"
            with patch('builtins.open', return_value=mock_file):
                template = get_commit_template()
                assert template == "Template content"
    
    def test_get_commit_template_not_configured(self):
        """Test getting commit template when none is configured."""
        with patch('src.python.utils.git._run_git_command') as mock_cmd:
            # Mock no commit.template configuration
            mock_cmd.return_value = MagicMock(returncode=1, stdout="")
            
            template = get_commit_template()
            assert template is None
    
    def test_apply_commit_template(self):
        """Test applying a commit template to a message."""
        message = "Test commit message"
        
        # Template with comments
        template = """

# Please enter the commit message for your changes. Lines starting
# with '#' will be ignored.
#
# On branch main
# Changes to be committed:
#   modified:   file.txt
#
        """
        
        result = apply_commit_template(message, template)
        assert result.startswith("Test commit message")
        assert "# Please enter" in result
        assert "# Changes to be committed" in result
        
        # Template without comments
        template = "Signed-off-by: User <user@example.com>"
        result = apply_commit_template(message, template)
        assert result == "Test commit message"

    @pytest.mark.parametrize("returncode,expected", [
        (0, False),  # No changes
        (1, True),   # Has changes
    ])
    def test_has_staged_changes(self, returncode, expected):
        """Test checking for staged changes."""
        with patch('src.python.utils.git._run_git_command') as mock_cmd:
            mock_result = MagicMock()
            mock_result.returncode = returncode
            mock_cmd.return_value = mock_result
            
            assert has_staged_changes() == expected
    
    @pytest.mark.parametrize("returncode,expected", [
        (0, False),  # No changes
        (1, True),   # Has changes
    ])
    def test_has_unstaged_changes(self, returncode, expected):
        """Test checking for unstaged changes."""
        with patch('src.python.utils.git._run_git_command') as mock_cmd:
            mock_result = MagicMock()
            mock_result.returncode = returncode
            mock_cmd.return_value = mock_result
            
            assert has_unstaged_changes() == expected
    
    def test_get_repo_status(self):
        """Test getting repository status."""
        with patch('src.python.utils.git.has_staged_changes', return_value=True), \
             patch('src.python.utils.git.has_unstaged_changes', return_value=False), \
             patch('src.python.utils.git.get_git_root', return_value="/path/to/repo"):
            
            status = get_repo_status()
            assert status["has_staged_changes"] is True
            assert status["has_unstaged_changes"] is False
            assert status["is_git_repo"] is True
    
    def test_commit(self):
        """Test committing changes."""
        with patch('src.python.utils.git._run_git_command') as mock_cmd:
            mock_result = MagicMock()
            mock_result.stdout = "1 file changed, 2 insertions(+)"
            mock_cmd.return_value = mock_result
            
            success, output = commit("Test commit message")
            assert success is True
            assert output == "1 file changed, 2 insertions(+)"
            mock_cmd.assert_called_once_with(["git", "commit", "-m", "Test commit message"])
    
    def test_commit_with_args(self):
        """Test committing changes with additional args."""
        with patch('src.python.utils.git._run_git_command') as mock_cmd:
            mock_result = MagicMock()
            mock_result.stdout = "1 file changed, 2 insertions(+)"
            mock_cmd.return_value = mock_result
            
            success, output = commit("Test commit message", ["--no-verify", "--allow-empty"])
            assert success is True
            assert output == "1 file changed, 2 insertions(+)"
            mock_cmd.assert_called_once_with(
                ["git", "commit", "-m", "Test commit message", "--no-verify", "--allow-empty"]
            )
    
    def test_commit_error(self):
        """Test error handling when committing changes."""
        with patch('src.python.utils.git._run_git_command') as mock_cmd:
            mock_cmd.side_effect = GitError("Command failed")
            
            success, output = commit("Test commit message")
            assert success is False
            assert "Command failed" in output