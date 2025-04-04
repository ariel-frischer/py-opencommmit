"""Git utilities for OpenCommit."""

import subprocess
import os
import platform
import re
import fnmatch
from typing import List, Optional, Dict, Tuple, Set
from pathlib import Path

# Constants
MAX_DIFF_SIZE = 50000  # Characters - when to split the diff
MAX_FILE_SIZE = 1024 * 1024  # 1MB - files larger than this will be filtered
GIT_ERROR_PATTERN = re.compile(r"^fatal:|^error:", re.MULTILINE)

# File patterns that should be excluded from LLM processing
DEFAULT_EXCLUDE_PATTERNS = [
    # Lock files
    "*.lock",
    "*-lock.json",
    "yarn.lock",
    "package-lock.json",
    "poetry.lock",
    "Cargo.lock",
    "Gemfile.lock",
    "composer.lock",
    
    # Binary and large files
    "*.wasm",
    "*.min.js",
    "*.min.css",
    "*.gz",
    "*.zip",
    "*.tar",
    "*.jar",
    "*.war",
    "*.ear",
    "*.class",
    "*.exe",
    "*.dll",
    "*.so",
    "*.dylib",
    "*.o",
    "*.obj",
    
    # Images
    "*.jpg",
    "*.jpeg",
    "*.png",
    "*.gif",
    "*.bmp",
    "*.ico",
    "*.svg",
    "*.webp",
    
    # Generated files/directories
    "dist/*",
    "build/*",
    "node_modules/*",
    "__pycache__/*",
    "*.pyc",
    
    # Other large files
    "*.pdf",
    "*.psd",
    "*.ai",
    "*.mp3",
    "*.mp4",
    "*.mov",
    "*.avi"
]


class GitError(Exception):
    """Custom exception for Git operations."""
    pass


def _run_git_command(args: List[str], check: bool = True) -> subprocess.CompletedProcess:
    """
    Run a git command with proper error handling.
    
    Args:
        args: List of command arguments including 'git' as first element
        check: Whether to check return code
        
    Returns:
        CompletedProcess instance
        
    Raises:
        GitError: If the command fails and check is True
    """
    try:
        # Ensure git is the first argument
        if not args or args[0] != "git":
            args.insert(0, "git")
            
        # Handle Windows vs Unix differences
        shell = platform.system() == "Windows"
        
        # Run the command
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=check,
            shell=shell,
        )
        return result
    except subprocess.CalledProcessError as e:
        # Extract useful error message from git output
        error_msg = e.stderr.strip() if e.stderr else str(e)
        if GIT_ERROR_PATTERN.search(error_msg):
            error_msg = GIT_ERROR_PATTERN.search(error_msg).group(0)
        raise GitError(f"Git command failed: {' '.join(args)}\n{error_msg}")
    except FileNotFoundError:
        raise GitError("Git executable not found. Make sure Git is installed and in your PATH.")


def get_git_root() -> Optional[str]:
    """
    Get the root directory of the git repository.
    
    Returns:
        Path to git root or None if not in a repo
    """
    try:
        result = _run_git_command(["git", "rev-parse", "--show-toplevel"])
        return result.stdout.strip()
    except GitError:
        return None


def is_git_repository() -> bool:
    """Check if the current directory is a git repository."""
    return get_git_root() is not None


def assert_git_repo() -> None:
    """
    Verify we're in a git repository.
    
    Raises:
        GitError: If not in a git repository
    """
    try:
        _run_git_command(["git", "rev-parse", "--is-inside-work-tree"])
    except GitError:
        raise GitError("Not in a git repository. Please run this command inside a git repository.")


def get_staged_files() -> List[str]:
    """
    Get a list of staged files.
    
    Returns:
        List of staged file paths relative to repo root
    """
    result = _run_git_command(["git", "diff", "--name-only", "--cached"])
    return [f for f in result.stdout.strip().split("\n") if f]


def get_changed_files() -> List[str]:
    """
    Get a list of all changed files (staged and unstaged).
    
    Returns:
        List of changed file paths relative to repo root
    """
    staged = _run_git_command(["git", "diff", "--name-only", "--cached"])
    unstaged = _run_git_command(["git", "diff", "--name-only"])
    
    # Combine and deduplicate
    all_files = set()
    for output in [staged.stdout, unstaged.stdout]:
        all_files.update([f for f in output.strip().split("\n") if f])
    
    return sorted(list(all_files))


def get_untracked_files() -> List[str]:
    """
    Get a list of untracked files.

    Returns:
        List of untracked file paths relative to repo root
    """
    # Use --exclude-standard to respect .gitignore
    result = _run_git_command(["git", "ls-files", "--others", "--exclude-standard"])
    return [f for f in result.stdout.strip().split("\n") if f]


def get_staged_diff() -> str:
    """
    Get the diff of staged changes.
    
    Returns:
        Git diff as string
        
    Raises:
        GitError: If getting diff fails
    """
    try:
        result = _run_git_command(["git", "diff", "--cached"])
        return result.stdout
    except GitError as e:
        raise GitError(f"Failed to get staged diff: {e}")


def split_diff_by_files(diff: str) -> Dict[str, str]:
    """
    Split a large diff into separate diffs by file.
    
    Args:
        diff: Complete git diff string
        
    Returns:
        Dictionary mapping filenames to their diffs
    """
    file_diffs = {}
    current_file = None
    current_diff = []
    
    # Pattern to match the start of a new file diff
    file_header_pattern = re.compile(r"^diff --git a/(.*?) b/(.*?)$")
    
    for line in diff.split("\n"):
        match = file_header_pattern.match(line)
        if match:
            # Save previous file diff if exists
            if current_file and current_diff:
                file_diffs[current_file] = "\n".join(current_diff)
                current_diff = []
            
            # Start new file diff
            current_file = match.group(2)  # Use the "b" path as the current file
            current_diff = [line]
        elif current_file:
            current_diff.append(line)
    
    # Add the last file
    if current_file and current_diff:
        file_diffs[current_file] = "\n".join(current_diff)
        
    return file_diffs


def merge_diffs(diffs: List[str], max_size: int = MAX_DIFF_SIZE) -> List[str]:
    """
    Merge multiple diffs into chunks that don't exceed max_size.
    
    Args:
        diffs: List of diff strings to merge
        max_size: Maximum size of each merged diff
        
    Returns:
        List of merged diffs, each under max_size
    """
    merged_diffs = []
    current_diff = ""
    
    for diff in diffs:
        # If adding this diff would exceed max_size, start a new merged diff
        if len(current_diff) + len(diff) > max_size and current_diff:
            merged_diffs.append(current_diff)
            current_diff = diff
        else:
            # Append this diff to current merged diff with separator if needed
            if current_diff:
                current_diff += "\n"
            current_diff += diff
    
    # Add the final merged diff if there's anything left
    if current_diff:
        merged_diffs.append(current_diff)
    
    return merged_diffs


def stage_files(files: List[str]) -> None:
    """
    Stage the specified files.
    
    Args:
        files: List of files to stage
        
    Raises:
        GitError: If staging fails
    """
    if not files:
        return
        
    # Sanitize file paths to prevent command injection
    sanitized_files = [f.strip() for f in files if f.strip()]
    if not sanitized_files:
        return
        
    try:
        _run_git_command(["git", "add"] + sanitized_files)
    except GitError as e:
        raise GitError(f"Failed to stage files: {e}")


def stage_all_changes() -> None:
    """
    Stage all changes in the repository.
    
    Raises:
        GitError: If staging fails
    """
    try:
        _run_git_command(["git", "add", "-A"])
    except GitError as e:
        raise GitError(f"Failed to stage all changes: {e}")


def stage_files(files: List[str]) -> None:
    """
    Stage specific files.
    
    Args:
        files: List of file paths to stage
        
    Raises:
        GitError: If staging fails
    """
    if not files:
        return
        
    try:
        for file in files:
            _run_git_command(["git", "add", file])
    except GitError as e:
        raise GitError(f"Failed to stage files: {e}")


def get_commit_template() -> Optional[str]:
    """
    Get the commit template if one is configured.
    
    Returns:
        Template content or None if no template is configured
    """
    try:
        # First check if a template is configured
        result = _run_git_command(
            ["git", "config", "--get", "commit.template"], 
            check=False
        )
        
        if result.returncode != 0 or not result.stdout.strip():
            return None
            
        template_path = result.stdout.strip()
        # Expand ~ to home directory if needed
        template_path = os.path.expanduser(template_path)
        
        # Read the template file
        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                return f.read()
        return None
    except (GitError, IOError):
        return None


def apply_commit_template(message: str, template: str) -> str:
    """
    Apply a commit template to a message.
    
    Args:
        message: Commit message
        template: Template content
        
    Returns:
        Message with template applied
    """
    # Simple template application: 
    # - Comments (lines starting with #) are preserved
    # - The message is inserted at the top
    
    # Strip whitespace from the message
    message = message.strip()
    
    # If template has comments, keep them
    if '#' in template:
        template_lines = template.split('\n')
        message_lines = [line for line in template_lines if not line.strip().startswith('#')]
        comment_lines = [line for line in template_lines if line.strip().startswith('#')]
        
        # Insert message at the top
        return message + '\n\n' + '\n'.join(comment_lines)
    else:
        # No comments, just use the message
        return message


def commit(message: str, args: List[str] = None) -> Tuple[bool, str]:
    """
    Commit staged changes with the given message.
    
    Args:
        message: Commit message
        args: Additional arguments to pass to git commit
        
    Returns:
        Tuple of (success, output)
        
    Raises:
        GitError: If commit fails
    """
    cmd = ["git", "commit", "-m", message]
    
    # Add any additional arguments
    if args:
        cmd.extend(args)
        
    try:
        result = _run_git_command(cmd)
        return True, result.stdout
    except GitError as e:
        return False, str(e)


def has_staged_changes() -> bool:
    """
    Check if there are any staged changes.
    
    Returns:
        True if there are staged changes, False otherwise
    """
    try:
        result = _run_git_command(["git", "diff", "--cached", "--quiet"], check=False)
        # Return code 0 means no differences, 1 means there are differences
        return result.returncode == 1
    except GitError:
        return False


def has_unstaged_changes() -> bool:
    """
    Check if there are any unstaged changes.
    
    Returns:
        True if there are unstaged changes, False otherwise
    """
    try:
        result = _run_git_command(["git", "diff", "--quiet"], check=False)
        # Return code 0 means no differences, 1 means there are differences
        return result.returncode == 1
    except GitError:
        return False


def get_repo_status() -> Dict[str, bool]:
    """
    Get repository status information.
    
    Returns:
        Dictionary with status flags
    """
    return {
        "has_staged_changes": has_staged_changes(),
        "has_unstaged_changes": has_unstaged_changes(),
        "is_git_repo": get_git_root() is not None,
    }


def get_opencommit_ignore() -> Set[str]:
    """
    Read the .opencommitignore file if it exists and return the patterns.
    Similar to the JavaScript implementation.
    
    Returns:
        Set of patterns to ignore
    """
    ignore_patterns = set(DEFAULT_EXCLUDE_PATTERNS)
    
    try:
        ignore_file_path = Path('.opencommitignore')
        if ignore_file_path.exists():
            with open(ignore_file_path, 'r') as f:
                # Read and add non-empty lines that don't start with #
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        ignore_patterns.add(line)
    except Exception:
        # Silently fail if the file can't be read, similar to JS implementation
        pass
    
    return ignore_patterns


def _matches_pattern(file_path: str, pattern: str) -> bool:
    """
    Check if file path matches a glob pattern using fnmatch.
    Also handles directory paths with trailing /* patterns.
    
    Args:
        file_path: Path to check
        pattern: Glob pattern
    
    Returns:
        True if the path matches the pattern
    """
    # Handle directory wildcards (e.g., "dist/*")
    if pattern.endswith('/*'):
        dir_pattern = pattern[:-2]
        return file_path == dir_pattern or file_path.startswith(f"{dir_pattern}/")
    
    # Use fnmatch for standard glob pattern matching
    return fnmatch.fnmatch(file_path, pattern)


def should_filter_file(file_path: str) -> Tuple[bool, str]:
    """
    Determine if a file should be filtered (excluded) from LLM processing.
    
    Args:
        file_path: Path to the file to check
    
    Returns:
        Tuple of (should_filter: bool, reason: str)
    """
    # Check file existence
    path = Path(file_path)
    if not path.exists():
        return False, "File doesn't exist"
    
    # Check file size
    try:
        if path.stat().st_size > MAX_FILE_SIZE:
            return True, f"File exceeds size limit of {MAX_FILE_SIZE/1024/1024}MB"
    except Exception:
        # If we can't check size, assume it's ok
        pass
    
    # Check against ignore patterns
    ignore_patterns = get_opencommit_ignore()
    
    # Convert file path to forward slashes for consistent pattern matching
    normalized_path = str(path).replace('\\', '/')
    
    for pattern in ignore_patterns:
        # Use pattern matching
        if _matches_pattern(normalized_path, pattern):
            return True, f"Matches ignore pattern: {pattern}"
    
    # File passed all checks
    return False, "File is not filtered"