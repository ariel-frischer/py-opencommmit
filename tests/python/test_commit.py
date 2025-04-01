"""Tests for the OpenCommit commit command."""

import pytest
import sys
import subprocess
from unittest.mock import patch, MagicMock
from rich.console import Console
from py_opencommit.commands.commit import (
    generate_commit_message,
    check_message_template,
    apply_template,
    run_git_commit,
    chunk_diff,
    split_diff_by_files,
    create_commit_prompt,
    DEFAULT_TEMPLATE_PLACEHOLDER
)


def test_check_message_template():
    """Test check_message_template function."""
    # Test finding template
    extra_args = ["-a", "--no-verify", f"--template-msg={DEFAULT_TEMPLATE_PLACEHOLDER}"]
    result = check_message_template(extra_args)
    assert result == f"--template-msg={DEFAULT_TEMPLATE_PLACEHOLDER}"
    
    # Test with custom placeholder
    placeholder = "$custom"
    extra_args = ["-a", "--no-verify", f"--template-msg={placeholder}"]
    result = check_message_template(extra_args, placeholder)
    assert result == f"--template-msg={placeholder}"
    
    # Test no template found
    extra_args = ["-a", "--no-verify"]
    result = check_message_template(extra_args)
    assert result is None


def test_apply_template():
    """Test apply_template function."""
    message = "Test commit message"
    template = "Subject: {message}\n\nDetails go here"
    
    result = apply_template(message, template, "{message}")
    assert result == "Subject: Test commit message\n\nDetails go here"
    
    # Test with default placeholder
    template = f"Subject: {DEFAULT_TEMPLATE_PLACEHOLDER}\n\nDetails go here"
    result = apply_template(message, template)
    assert result == "Subject: Test commit message\n\nDetails go here"


def test_run_git_commit():
    """Test run_git_commit function."""
    with patch('subprocess.run') as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        # Test successful commit
        result = run_git_commit("Test message", ["-a", "--no-verify"])
        assert result is True
        mock_run.assert_called_once()
        assert mock_run.call_args[0][0][0:3] == ["git", "commit", "-m"]
        assert mock_run.call_args[0][0][3] == "Test message"
        assert "-a" in mock_run.call_args[0][0]
        assert "--no-verify" in mock_run.call_args[0][0]
        
        # Test filtering template args
        mock_run.reset_mock()
        mock_run.return_value = mock_result
        result = run_git_commit("Test message", ["-a", f"--template-msg={DEFAULT_TEMPLATE_PLACEHOLDER}"])
        assert result is True
        mock_run.assert_called_once()
        assert mock_run.call_args[0][0][0:3] == ["git", "commit", "-m"]
        assert mock_run.call_args[0][0][3] == "Test message"
        assert "-a" in mock_run.call_args[0][0]
        assert f"--template-msg={DEFAULT_TEMPLATE_PLACEHOLDER}" not in mock_run.call_args[0][0]
        
        # Test commit failure
        mock_run.reset_mock()
        mock_run.side_effect = subprocess.CalledProcessError(1, "git commit", stderr="Git error")
        with pytest.raises(RuntimeError):
            run_git_commit("Test message", [])


def test_split_diff_by_files():
    """Test split_diff_by_files function."""
    diff = """diff --git a/file1.txt b/file1.txt
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
    
    result = split_diff_by_files(diff)
    assert len(result) == 2
    assert "file1.txt" in result
    assert "file2.txt" in result
    assert "+line3" in result["file1.txt"]
    assert "-line1" in result["file2.txt"]


def test_chunk_diff(mock_staged_diff):
    """Test chunk_diff function."""
    with patch('py_opencommit.commands.commit.token_count', return_value=100):
        # Test single chunk (small diff)
        chunks = chunk_diff(mock_staged_diff)
        assert len(chunks) == 1
        assert chunks[0] == mock_staged_diff
    
    with patch('py_opencommit.commands.commit.token_count') as mock_token_count:
        # Simulate large diff requiring chunking
        mock_token_count.side_effect = lambda text: 5000 if text == mock_staged_diff else 1000
        
        with patch('py_opencommit.commands.commit.split_diff_by_files') as mock_split:
            file_diffs = {
                "file1.txt": "diff for file1",
                "file2.txt": "diff for file2"
            }
            mock_split.return_value = file_diffs
            
            # Updated keyword argument from max_tokens to max_tokens_per_chunk
            chunks = chunk_diff(mock_staged_diff, max_tokens_per_chunk=1500)
            assert len(chunks) == 2
            assert chunks[0] == "diff for file1"
            assert chunks[1] == "diff for file2"


def test_create_commit_prompt():
    """Test create_commit_prompt function."""
    diff = "Test diff content"
    
    # Test without context
    messages = create_commit_prompt(diff)
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    # Updated assertion to match the new prompt identity
    assert "You are an AI assistant specialized" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert diff in messages[1]["content"]
    
    # Test with context
    context = "Feature related to user authentication"
    messages = create_commit_prompt(diff, context)
    assert len(messages) == 2
    assert context in messages[0]["content"]


def test_generate_commit_message(mock_litellm):
    """Test generate_commit_message function."""
    diff = "Test diff content"
    
    # Test successful generation
    message = generate_commit_message(diff)
    assert message == "Add feature: implement new functionality"
    
    # Test with empty diff
    with pytest.raises(ValueError, match="No changes to commit"):
        generate_commit_message("   ")
    
    # Test with API error
    with patch('litellm.completion', side_effect=Exception("API error")):
        with pytest.raises(RuntimeError, match="Failed to generate commit message"):
            generate_commit_message(diff)


def test_commit_command_components(mock_git_repo, mock_staged_diff, mock_staged_files, mock_litellm):
    """Test components of the commit command."""
    # Test message generation
    message = generate_commit_message(mock_staged_diff)
    assert message is not None
    
    # Test template handling
    template_arg = check_message_template([f"--template={DEFAULT_TEMPLATE_PLACEHOLDER}"])
    assert template_arg == f"--template={DEFAULT_TEMPLATE_PLACEHOLDER}"
    
    # Test template application
    formatted_message = apply_template(message, template_arg, DEFAULT_TEMPLATE_PLACEHOLDER)
    assert formatted_message is not None
    
    # Test commit execution with mocks
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        result = run_git_commit(message, [])
        assert result is True
