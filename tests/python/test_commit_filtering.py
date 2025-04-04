"""Tests for the file filtering integration with commit process."""

import pytest
from unittest.mock import patch, MagicMock, call

from src.python.commands.commit import (
    split_diff_by_files,
    generate_commit_message,
)

from src.python.utils.git import (
    should_filter_file,
)


class TestCommitFiltering:
    
    def test_split_diff_by_files(self):
        """Test splitting diff by files and filtering out files that should be excluded."""
        # Create a test diff with multiple files
        test_diff = """diff --git a/file1.txt b/file1.txt
index 1234567..abcdef 100644
--- a/file1.txt
+++ b/file1.txt
@@ -1,3 +1,4 @@
line1
line2
+line3
diff --git a/package-lock.json b/package-lock.json
index 9876543..fedcba 100644
--- a/package-lock.json
+++ b/package-lock.json
@@ -1,1000 +1,1001 @@
 {
   "dependencies": {
-    "lib1": "1.0.0",
+    "lib1": "1.0.1",
   }
 }
diff --git a/image.jpg b/image.jpg
Binary files /dev/null and b/image.jpg differ
diff --git a/file2.py b/file2.py
index aaaaaa..bbbbbb 100644
--- a/file2.py
+++ b/file2.py
@@ -1,2 +1,3 @@
 def hello():
     print("hello")
+    return True
"""
        
        # Mock should_filter_file to return True for package-lock.json and image.jpg
        def mock_filter(file_path):
            if file_path in ["package-lock.json", "image.jpg"]:
                return True, f"Filtered: {file_path}"
            return False, "Not filtered"
        
        with patch('src.python.commands.commit.should_filter_file', side_effect=mock_filter):
            included_diffs, filtered_diffs = split_diff_by_files(test_diff)
            
            # Verify included files
            assert len(included_diffs) == 2
            assert "file1.txt" in included_diffs
            assert "file2.py" in included_diffs
            assert "+line3" in included_diffs["file1.txt"]
            assert "+    return True" in included_diffs["file2.py"]
            
            # Verify filtered files
            assert len(filtered_diffs) == 2
            assert "package-lock.json" in filtered_diffs
            assert "image.jpg" in filtered_diffs
            assert filtered_diffs["package-lock.json"] == "Filtered: package-lock.json"
            assert filtered_diffs["image.jpg"] == "Filtered: image.jpg"
    
    def test_generate_commit_message_with_filtering(self, mock_litellm):
        """Test generate_commit_message correctly filters files but includes them in context."""
        # Create a test diff with files that should be filtered and included
        test_diff = """diff --git a/src/main.py b/src/main.py
index 1234567..abcdef 100644
--- a/src/main.py
+++ b/src/main.py
@@-1,3 +1,4 @@
def main():
    print("Hello")
+    return True
diff --git a/package-lock.json b/package-lock.json
index 9876543..fedcba 100644
--- a/package-lock.json
+++ b/package-lock.json
@@-1,2 +1,3 @@
 {
   "name": "test",
+  "version": "1.0.1"
 }"""
        
        # List of staged files (should match both filtered and included files)
        staged_files = ["src/main.py", "package-lock.json"]
        
        # Mock filtering function to filter package-lock.json
        def mock_filter(file_path):
            if file_path == "package-lock.json":
                return True, "Lock file"
            return False, "Not filtered"
        
        # Set up mocks
        with patch('src.python.commands.commit.get_staged_diff', return_value=test_diff), \
             patch('src.python.commands.commit.get_staged_files', return_value=staged_files), \
             patch('src.python.commands.commit.should_filter_file', side_effect=mock_filter), \
             patch('rich.console.Console.print') as mock_print:
            
            # Call generate_commit_message
            result = generate_commit_message(test_diff)
            
            # Verify result is from the mock LiteLLM response
            assert result == "Add feature: implement new functionality"
            
            # Verify the console output shows filtered files
            assert any("excluded from LLM processing" in str(call_args) for call_args in mock_print.call_args_list)
            assert any("package-lock.json" in str(call_args) for call_args in mock_print.call_args_list)
            
            # Verify LiteLLM was called with only the unfiltered file's diff
            import litellm
            # Extract all the calls to litellm.completion
            completion_calls = [call for call in litellm.completion.call_args_list]
            assert len(completion_calls) > 0
            
            # Check that the diff passed to LiteLLM does not contain package-lock.json diff content
            for call_args in completion_calls:
                messages = call_args[1]['messages']
                # Look at the content of the user message, which contains the diff
                user_messages = [m for m in messages if isinstance(m, dict) and m.get('role') == 'user']
                if user_messages:
                    user_content = user_messages[0].get('content', '')
                    # Check if the python file is in the diff sent to LiteLLM
                    assert "src/main.py" in user_content
                    assert "+    return True" in user_content
                    # Check that the package-lock.json diff content is not there
                    assert "package-lock.json" not in user_content.split("\n--- a/")[1:]
    
    def test_filtered_files_still_committed(self, runner, mock_git_repo, mock_litellm):
        """Test that filtered files are still included in the commit."""
        # Mock staged files and diff
        staged_files = ["src/main.py", "package-lock.json", "image.jpg"]
        
        test_diff = """diff --git a/src/main.py b/src/main.py
index 1234567..abcdef 100644
--- a/src/main.py
+++ b/src/main.py
@@ -1,3 +1,4 @@
def main():
    print("Hello")
+    return True
diff --git a/package-lock.json b/package-lock.json
index 9876543..fedcba 100644
--- a/package-lock.json
+++ b/package-lock.json
@@-1,2 +1,3 @@
 {
   "name": "test",
+  "version": "1.0.1"
 }
diff --git a/image.jpg b/image.jpg
Binary files /dev/null and b/image.jpg differ"""
        
        # Mock git filter and commit
        def mock_filter(file_path):
            if file_path in ["package-lock.json", "image.jpg"]:
                return True, f"Filtered: {file_path}"
            return False, "Not filtered"
        
        # Mock subprocess for git commit to check the command
        mock_subprocess = MagicMock()
        mock_subprocess.run.return_value = MagicMock(returncode=0)
        
        with patch('src.python.commands.commit.get_staged_diff', return_value=test_diff), \
             patch('src.python.commands.commit.get_staged_files', return_value=staged_files), \
             patch('src.python.commands.commit.should_filter_file', side_effect=mock_filter), \
             patch('src.python.commands.commit.subprocess', mock_subprocess), \
             patch('src.python.commands.commit.Confirm.ask', return_value=True), \
             patch('rich.console.Console.print'):
            
            # Import the command directly
            from src.python.commands.commit import commit as commit_command
            
            # Run the commit command with --skip-confirm to avoid interactive prompts
            result = runner.invoke(commit_command, ["--skip-confirm"])
            
            # Check the commit was successful
            assert result.exit_code == 0
            
            # Verify subprocess.run was called with all files
            mock_subprocess.run.assert_called()
            # Extract the commit command
            commit_calls = [
                call_args for call_args in mock_subprocess.run.call_args_list 
                if len(call_args[0][0]) > 1 and call_args[0][0][0] == "git" and call_args[0][0][1] == "commit"
            ]
            assert len(commit_calls) > 0
            
            # Make sure the commit includes the message
            commit_cmd = commit_calls[0][0][0]
            assert "git" in commit_cmd
            assert "commit" in commit_cmd