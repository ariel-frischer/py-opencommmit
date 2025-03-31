"""Configuration for pytest."""

import sys
import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.python.commands.config import ConfigKeys, DEFAULT_CONFIG


@pytest.fixture
def runner():
    """Return a Click test runner."""
    return CliRunner()


@pytest.fixture
def mock_git_repo():
    """Mock being in a git repository."""
    with patch('src.python.utils.git.get_git_root', return_value='/fake/git/repo'):
        with patch('src.python.utils.git.is_git_repository', return_value=True):
            yield


@pytest.fixture
def mock_staged_diff():
    """Mock git diff output for staged changes."""
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
    with patch('src.python.utils.git.get_staged_diff', return_value=diff):
        yield diff


@pytest.fixture
def mock_staged_files():
    """Mock list of staged files."""
    files = ['file1.txt', 'file2.txt']
    with patch('src.python.utils.git.get_staged_files', return_value=files):
        with patch('src.python.commands.commit.get_staged_files', return_value=files):
            yield files


@pytest.fixture
def mock_litellm():
    """Mock LiteLLM API response."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Add feature: implement new functionality"
    
    with patch('litellm.completion', return_value=mock_response):
        yield mock_response


@pytest.fixture
def temp_global_config_file():
    """Create a temporary global config file."""
    with tempfile.NamedTemporaryFile(delete=False, mode='w+') as f:
        f.write("[DEFAULT]\n")
        f.write("OCO_API_KEY = test-api-key\n")
        f.write("OCO_MODEL = gpt-3.5-turbo\n")
        f.write("OCO_EMOJI = true\n")
        temp_path = f.name
    
    with patch('src.python.commands.config.get_global_config_path', return_value=Path(temp_path)):
        yield temp_path
    
    # Clean up
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_project_config_file():
    """Create a temporary project config file (.env)."""
    with tempfile.NamedTemporaryFile(delete=False, mode='w+') as f:
        f.write("OCO_API_KEY=project-api-key\n")
        f.write("OCO_MODEL=gpt-4\n")
        f.write("OCO_WHY=true\n")
        temp_path = f.name
    
    with patch('src.python.commands.config.get_project_config_path', return_value=Path(temp_path)):
        yield temp_path
    
    # Clean up
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for config."""
    original_environ = os.environ.copy()
    os.environ[ConfigKeys.OCO_API_KEY.value] = "test-api-key"
    os.environ[ConfigKeys.OCO_MODEL.value] = "gpt-4"
    os.environ[ConfigKeys.OCO_DESCRIPTION.value] = "true"
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_environ)