"""Tests for the OpenCommit CLI."""

import pytest
import os
from unittest import mock
from click.testing import CliRunner
from src.python.cli import cli, main
from src.python.i18n import get_text, load_translations


@pytest.fixture
def runner():
    return CliRunner()


def test_cli_help(runner):
    """Test the CLI help output."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    # Updated assertion to match the new CLI description
    assert "PyOC - AI-powered commit message generator" in result.output
    assert "commit" in result.output
    assert "config" in result.output
    assert "githook" in result.output


def test_language_option(runner):
    """Test setting language through CLI option."""
    # Mock load_translations to avoid actual file operations
    with mock.patch('src.python.cli.load_translations') as mock_load:
        with mock.patch('src.python.cli.get_language_from_alias', return_value='es'):
            result = runner.invoke(cli, ["--language", "es", "commit", "--help"])
            assert result.exit_code == 0
            mock_load.assert_called_once_with('es')
            assert 'OCO_LANGUAGE' in os.environ
            assert os.environ['OCO_LANGUAGE'] == 'es'


def test_unknown_language_option(runner):
    """Test setting unknown language through CLI option."""
    with mock.patch('src.python.cli.get_language_from_alias', return_value=None):
        with mock.patch('src.python.cli.console.print') as mock_print:
            result = runner.invoke(cli, ["--language", "unknown", "commit", "--help"])
            assert result.exit_code == 0
            mock_print.assert_called_once()
            assert "Warning: Unknown language" in mock_print.call_args[0][0]


def test_commit_command(runner):
    """Test commit command invocation."""
    # Skip actual execution of commit command
    with mock.patch('src.python.commands.commit.commit') as mock_commit:
        result = runner.invoke(cli, ["commit"])
        assert result.exit_code == 0
        mock_commit.assert_called_once()


def test_commit_command_with_options(runner):
    """Test commit command with options."""
    with mock.patch('src.python.commands.commit.commit') as mock_commit:
        result = runner.invoke(cli, [
            "commit", 
            "--stage-all", 
            "--skip-confirm", 
            "--context", "Testing context", 
            "--", "-a"
        ])
        assert result.exit_code == 0
        # Updated assertion to expect positional arguments as observed in the error
        # click seems to pass them positionally in this test setup
        mock_commit.assert_called_once_with(
            ['-a'],             # extra_args
            'Testing context',  # context
            'true',             # stage_all
            'true'              # skip_confirm
        )


def test_commit_command_error(runner):
    """Test commit command error handling."""
    with mock.patch('src.python.commands.commit.commit', side_effect=Exception("Test error")):
        with mock.patch('src.python.cli.console.print') as mock_print:
            with mock.patch('src.python.cli.get_language_from_alias', return_value=None):
                result = runner.invoke(cli, ["commit"])
                assert result.exit_code == 1
                assert any("Error" in str(call) and "Test error" in str(call) for call in mock_print.call_args_list)


def test_config_get_command(runner):
    """Test config get command."""
    # Mock config function to avoid actual config operations
    with mock.patch('src.python.commands.config.config') as mock_config:
        result = runner.invoke(cli, ["config", "get"])
        assert result.exit_code == 0
        mock_config.assert_called_once_with('get', None, None, False)


def test_config_get_specific_key(runner):
    """Test config get command with specific key."""
    with mock.patch('src.python.commands.config.config') as mock_config:
        result = runner.invoke(cli, ["config", "get", "OCO_API_KEY"])
        assert result.exit_code == 0
        mock_config.assert_called_once_with('get', 'OCO_API_KEY', None, False)


def test_config_set_command(runner):
    """Test config set command."""
    with mock.patch('src.python.commands.config.config') as mock_config:
        result = runner.invoke(cli, ["config", "set", "OCO_API_KEY=test-key"])
        assert result.exit_code == 0
        mock_config.assert_called_once_with('set', 'OCO_API_KEY=test-key', None, False)


def test_config_set_project_command(runner):
    """Test config set command with project flag."""
    with mock.patch('src.python.commands.config.config') as mock_config:
        result = runner.invoke(cli, ["config", "set", "OCO_API_KEY=test-key", "--project"])
        assert result.exit_code == 0
        mock_config.assert_called_once_with('set', 'OCO_API_KEY=test-key', None, True)


def test_config_command_error(runner):
    """Test config command error handling."""
    with mock.patch('src.python.commands.config.config', side_effect=Exception("Test error")):
        with mock.patch('src.python.cli.console.print') as mock_print:
            with mock.patch('src.python.cli.get_language_from_alias', return_value=None):
                result = runner.invoke(cli, ["config", "get"])
                assert result.exit_code == 1
                assert any("Error" in str(call) and "Test error" in str(call) for call in mock_print.call_args_list)


def test_githook_command(runner):
    """Test githook command."""
    with mock.patch('src.python.commands.githook.githook') as mock_githook:
        result = runner.invoke(cli, ["githook"])
        assert result.exit_code == 0
        mock_githook.assert_called_once()


def test_githook_command_error(runner):
    """Test githook command error handling."""
    with mock.patch('src.python.commands.githook.githook', side_effect=Exception("Test error")):
        with mock.patch('src.python.cli.console.print') as mock_print:
            with mock.patch('src.python.cli.get_language_from_alias', return_value=None):
                result = runner.invoke(cli, ["githook"])
                assert result.exit_code == 1
                assert any("Error" in str(call) and "Test error" in str(call) for call in mock_print.call_args_list)


def test_main_function():
    """Test the main entry point with migrations."""
    with mock.patch('src.python.migrations.run_migrations') as mock_migrations:
        with mock.patch('src.python.cli.cli') as mock_cli:
            main()
            mock_migrations.assert_called_once()
            mock_cli.assert_called_once()


def test_main_function_migration_error():
    """Test the main entry point with migration errors."""
    with mock.patch('src.python.migrations.run_migrations', side_effect=Exception("Migration error")):
        with mock.patch('src.python.cli.console.print') as mock_print:
            with mock.patch('src.python.cli.cli') as mock_cli:
                main()
                mock_print.assert_called_once()
                assert "Error running migrations" in mock_print.call_args[0][0]
                mock_cli.assert_called_once()
