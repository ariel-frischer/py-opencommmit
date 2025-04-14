
import pytest
import subprocess
from unittest.mock import patch, MagicMock
from src.python.utils.git import get_staged_files, get_untracked_files

def test_get_staged_files_success():
    mock_run = MagicMock()
    mock_run.stdout = 'file1.txt\nfile2.txt'
    with patch('subprocess.run', return_value=mock_run):
        result = get_staged_files()
    assert result == ['file1.txt', 'file2.txt']

def test_get_staged_files_error():
    with patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'git')):
        with pytest.raises(RuntimeError, match="Failed to get staged files"):
            get_staged_files()

def test_get_untracked_files_success():
    mock_run = MagicMock()
    mock_run.stdout = 'file5.txt\nfile6.txt'
    with patch('subprocess.run', return_value=mock_run):
        result = get_untracked_files()
    assert result == ['file5.txt', 'file6.txt']

def test_get_untracked_files_error(caplog):
    mock_error = subprocess.CalledProcessError(1, 'git')
    mock_error.stderr = 'fatal: not a git repository'
    with patch('subprocess.run', side_effect=mock_error):
        result = get_untracked_files()
    assert result == []
    assert "Failed to get untracked files" in caplog.text
