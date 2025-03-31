
import pytest
from click.testing import CliRunner
from src.python.cli import cli

@pytest.fixture
def runner():
    return CliRunner()

def test_commit_command(runner):
    result = runner.invoke(cli, ["commit"])
    assert result.exit_code == 0
    assert "Running commit command with LiteLLM integration" in result.output

def test_config_command(runner):
    result = runner.invoke(cli, ["config"])
    assert result.exit_code == 0
    assert "Running config command" in result.output

def test_githook_command(runner):
    result = runner.invoke(cli, ["githook"])
    assert result.exit_code == 0
    assert "Running githook command" in result.output
