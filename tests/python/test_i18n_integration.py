"""
Tests for the i18n integration with CLI commands.
"""

import pytest
from unittest.mock import patch
import os
from click.testing import CliRunner
from py_opencommit.cli import cli
from py_opencommit.i18n import get_text, load_translations

@pytest.fixture
def runner():
    return CliRunner()

@patch('py_opencommit.commands.commit.commit')
def test_cli_with_language_option(mock_commit, runner):
    """Test that the CLI correctly handles the language option."""
    # Mock the commit command to prevent actual execution
    mock_commit.return_value = None
    
    # Test with English language
    result = runner.invoke(cli, ["--language", "en", "commit"])
    assert result.exit_code == 0
    
    # Test with invalid language (should fallback to default)
    result = runner.invoke(cli, ["--language", "invalid", "commit"])
    assert result.exit_code == 0
    # Output contains ANSI color codes, so just check for part of the message
    assert "invalid" in result.output and "Using default language" in result.output

@patch('py_opencommit.commands.commit.commit')
def test_language_environment_variable(mock_commit, runner):
    """Test that the language can be set via environment variable."""
    # Mock the commit command to prevent actual execution
    mock_commit.return_value = None
    
    with runner.isolated_filesystem():
        env = {"OCO_LANGUAGE": "en"}
        result = runner.invoke(cli, ["commit"], env=env)
        assert result.exit_code == 0

def test_i18n_in_error_messages():
    """Test that error messages use i18n."""
    # Load English translations
    load_translations("en")
    
    # Check error message
    error_text = get_text("error")
    assert error_text == "Error"
    
    # Check success message
    success_text = get_text("success")
    assert success_text == "Success"
