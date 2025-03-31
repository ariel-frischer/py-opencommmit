"""
Enhanced commit command for OpenCommit Python CLI.
Provides AI-generated commit messages using LiteLLM.
"""

import re
import sys
import logging
from typing import List, Optional, Dict, Union

import click
import litellm
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.prompt import Confirm

from ..i18n import get_text
from ..commands.config import get_config, ConfigKeys

from ..utils.git import (
    get_staged_diff,
    stage_all_changes,
    is_git_repository,
    stage_files,
)
from ..utils.token_count import token_count

logger = logging.getLogger("opencommit")
# Initialize rich console
console = Console()

# Initialize config
config = get_config()

# Constants
MAX_TOKENS = int(
    config.get(ConfigKeys.OCO_TOKENS_MAX_OUTPUT, 4000)
)  # Maximum tokens for model input
MODEL_NAME = config.get(ConfigKeys.OCO_MODEL, "gpt-3.5-turbo")  # Get model from config
DEFAULT_TEMPLATE_PLACEHOLDER = config.get(
    ConfigKeys.OCO_MESSAGE_TEMPLATE_PLACEHOLDER, "{message}"
)


def get_staged_files() -> List[str]:
    """
    Get a list of staged files.

    Returns:
        List of staged file paths
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True,
        )
        return [f for f in result.stdout.strip().split("\n") if f]
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to get staged files: {e}")


def get_unstaged_files() -> List[str]:
    """
    Get a list of unstaged files.

    Returns:
        List of unstaged file paths
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only"],
            capture_output=True,
            text=True,
            check=True,
        )
        return [f for f in result.stdout.strip().split("\n") if f]
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get unstaged files: {e}")
        return []


def split_diff_by_files(diff: str) -> Dict[str, str]:
    """
    Split a git diff by individual files.

    Args:
        diff: Full git diff

    Returns:
        Dictionary mapping file paths to their diffs
    """
    file_diffs = {}
    current_file = None
    current_diff = []

    for line in diff.split("\n"):
        if line.startswith("diff --git"):
            if current_file and current_diff:
                file_diffs[current_file] = "\n".join(current_diff)

            # Extract filename from diff header
            match = re.search(r"diff --git a/(.*) b/(.*)", line)
            if match:
                current_file = match.group(2)
                current_diff = [line]
        elif current_file:
            current_diff.append(line)

    # Add the last file
    if current_file and current_diff:
        file_diffs[current_file] = "\n".join(current_diff)

    return file_diffs


def chunk_diff(diff: str, max_tokens: int = MAX_TOKENS) -> List[str]:
    """
    Split a large diff into chunks respecting token limits.

    Args:
        diff: Git diff to split
        max_tokens: Maximum tokens per chunk

    Returns:
        List of diff chunks
    """
    if not diff:
        return []

    # Get model context limit - default to 4000 if we can't determine
    model_context_limit = 4000
    if MODEL_NAME:
        # Approximate context limits for common models
        model_limits = {
            "gpt-3.5-turbo": 4096,
            "gpt-3.5-turbo-16k": 16384,
            "gpt-4": 8192,
            "gpt-4-32k": 32768,
            "gpt-4o": 128000,
            "gpt-4o-mini": 128000,
            "claude-3-opus": 200000,
            "claude-3-sonnet": 200000,
            "claude-3-haiku": 200000,
            "gemini-1.5-pro": 1000000,
            "gemini-1.5-flash": 1000000,
            "gemini-1.0-pro": 32768,
        }
        
        # Find the closest matching model name
        for model_name, limit in model_limits.items():
            if model_name in MODEL_NAME.lower():
                model_context_limit = limit
                break
    
    # Reserve tokens for the prompt and response
    # Use 25% of context for prompt and response, 75% for diff
    safe_token_limit = int(model_context_limit * 0.75)
    
    # Ensure max_tokens doesn't exceed safe limit
    max_tokens = min(max_tokens, safe_token_limit)
    
    # If diff is small enough, return as is
    diff_tokens = token_count(diff)
    if diff_tokens <= max_tokens:
        return [diff]
    
    # Log the token counts if logging is enabled
    if not logger.disabled:
        logger.debug(f"Diff is {diff_tokens} tokens, exceeding limit of {max_tokens}")
        logger.debug(f"Model context limit: {model_context_limit}")
        logger.debug(f"Safe token limit: {safe_token_limit}")

    # Split by files first
    file_diffs = split_diff_by_files(diff)
    chunks = []
    current_chunk = ""
    current_tokens = 0

    for file_path, file_diff in file_diffs.items():
        file_tokens = token_count(file_diff)

        # If a single file diff is too large, split it by hunks or truncate
        if file_tokens > max_tokens:
            # Try to split by hunks (git diff sections starting with @@ markers)
            hunks = re.split(r'(^@@.*?@@.*?$)', file_diff, flags=re.MULTILINE)
            
            # If we have hunks, process them individually
            if len(hunks) > 1:
                # Recombine the split markers with their content
                processed_hunks = []
                for i in range(0, len(hunks)-1, 2):
                    if i+1 < len(hunks):
                        processed_hunks.append(hunks[i] + hunks[i+1])
                    else:
                        processed_hunks.append(hunks[i])
                
                # Process each hunk
                for hunk in processed_hunks:
                    hunk_tokens = token_count(hunk)
                    
                    # If hunk is still too large, truncate it
                    if hunk_tokens > max_tokens:
                        truncated_hunk = hunk[:int(len(hunk) * max_tokens / hunk_tokens)]
                        truncated_hunk += "\n# ... (truncated)"
                        hunk = truncated_hunk
                        hunk_tokens = token_count(hunk)
                    
                    # Add hunk to chunks
                    if current_tokens + hunk_tokens > max_tokens and current_chunk:
                        chunks.append(current_chunk)
                        current_chunk = hunk
                        current_tokens = hunk_tokens
                    else:
                        if current_chunk:
                            current_chunk += "\n"
                        current_chunk += hunk
                        current_tokens += hunk_tokens
            else:
                # No hunks found, truncate the file
                truncation_ratio = max_tokens / file_tokens
                truncated_diff = file_diff[:int(len(file_diff) * truncation_ratio * 0.9)]
                console.print(
                    f"[yellow]Warning:[/yellow] Diff for {file_path} is too large ({file_tokens} tokens), truncating to {max_tokens} tokens..."
                )
                truncated_diff += "\n# ... (truncated)"
                
                # Add truncated diff as its own chunk
                chunks.append(truncated_diff)
        else:
            # If adding this file would exceed the limit, start a new chunk
            if current_tokens + file_tokens > max_tokens and current_chunk:
                chunks.append(current_chunk)
                current_chunk = file_diff
                current_tokens = file_tokens
            else:
                if current_chunk:
                    current_chunk += "\n"
                current_chunk += file_diff
                current_tokens += file_tokens

    # Add the final chunk
    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def create_commit_prompt(diff: str, context: str = "") -> List[Dict[str, str]]:
    """
    Create a well-engineered prompt for commit message generation.

    Args:
        diff: Git diff
        context: Additional context

    Returns:
        List of messages for the LLM
    """
    # Calculate approximate token count for the diff
    diff_tokens = token_count(diff)
    
    # Log token count if logging is enabled
    if not logger.disabled:
        logger.debug(f"Diff token count: {diff_tokens}")
    
    system_prompt = """You are a commit message generator. 
Generate a concise, meaningful commit message following these guidelines:
- Use the imperative mood ("Add feature" not "Added feature")
- Start with a capital letter
- Do not end with a period
- Keep the first line under 50 characters
- Be specific but concise
- Focus on the "why" and "what" not just the "how"
- If the changes involve multiple distinct changes, list them with bullet points

Return ONLY the commit message without any additional explanation or formatting.
"""

    if context:
        system_prompt += f"\nAdditional context from the user: {context}"

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": f"Generate a commit message for the following changes:\n\n{diff}",
        },
    ]

    return messages


def generate_commit_message(diff: str, context: str = "") -> str:
    """
    Generate a commit message using LiteLLM.
    
    Args:
        diff: Git diff
        context: Additional context
        
    Returns:
        Generated commit message
    """
    if not logger.disabled:
        logger.debug("Generating commit message")
        
    if not diff.strip():
        raise ValueError("No changes to commit. The diff is empty.")

    # Split large diffs into manageable chunks
    diff_chunks = chunk_diff(diff)
    if not diff_chunks:
        raise ValueError("Failed to process the diff. Please check your changes.")

    if not logger.disabled:
        logger.debug(f"Split diff into {len(diff_chunks)} chunks")
        for i, chunk in enumerate(diff_chunks):
            logger.debug(f"Chunk {i+1} token count: {token_count(chunk)}")

    # For multiple chunks, generate and combine messages
    if len(diff_chunks) > 1:
        messages = []
        with Progress() as progress:
            task = progress.add_task(
                f"[cyan]{get_text('generatingCommitMessage')}...",
                total=len(diff_chunks),
            )

            for i, chunk in enumerate(diff_chunks):
                progress.update(
                    task,
                    description=f"[cyan]Processing chunk {i+1}/{len(diff_chunks)}...",
                )
                
                # Create prompt for this chunk
                prompt = create_commit_prompt(chunk, context)
                
                try:
                    # Get API key from config
                    api_key = config.get(ConfigKeys.OCO_API_KEY)
                    api_base = config.get(ConfigKeys.OCO_API_URL)

                    # Configure litellm with API key if available
                    completion_kwargs = {
                        "model": MODEL_NAME,
                        "messages": prompt,
                        "temperature": 0.7,
                        "max_tokens": 100,
                    }

                    if api_key:
                        completion_kwargs["api_key"] = api_key
                    if api_base:
                        completion_kwargs["api_base"] = api_base
    
                    # Convert any boolean values in the kwargs (including nested structures)
                    completion_kwargs = convert_bools_to_strings(completion_kwargs)

                    # Ensure temperature is a float
                    if "temperature" in completion_kwargs:
                        completion_kwargs["temperature"] = float(
                            completion_kwargs["temperature"]
                        )

                    # Ensure max_tokens is an int
                    if "max_tokens" in completion_kwargs:
                        completion_kwargs["max_tokens"] = int(
                            completion_kwargs["max_tokens"]
                        )

                    # Log types before calling litellm if logging is enabled
                    if not logger.disabled:
                        logger.debug("Argument types before litellm.completion (chunk loop):")
                        for key, value in completion_kwargs.items():
                            # Special handling for messages list
                            if key == 'messages' and isinstance(value, list):
                                logger.debug(f"  - {key}: list")
                                for idx, msg in enumerate(value):
                                    logger.debug(f"    - message[{idx}]: {type(msg)}")
                                    if isinstance(msg, dict):
                                        for msg_key, msg_val in msg.items():
                                            logger.debug(f"      - {msg_key}: {type(msg_val)}")
                            else:
                                logger.debug(f"  - {key}: {type(value)}")

                    if not logger.disabled:
                        logger.debug(
                            f"Chunk {i} final completion kwargs: {completion_kwargs}"
                        )
                        
                    # Add error handling for context window exceeded
                    try:
                        response = litellm.completion(**completion_kwargs)
                        chunk_message = response.choices[0].message.content.strip()
                        messages.append(chunk_message)
                        progress.update(task, advance=1)
                    except Exception as e:
                        error_str = str(e)
                        if "context length" in error_str.lower() or "context window" in error_str.lower():
                            # Try with a smaller chunk
                            console.print(f"[yellow]Warning: Context window exceeded. Trying with a smaller chunk...[/yellow]")
                            # Reduce chunk size by half and try again
                            half_length = len(chunk) // 2
                            smaller_chunk = chunk[:half_length] + "\n# ... (truncated)"
                            
                            # Update prompt with smaller chunk
                            smaller_prompt = create_commit_prompt(smaller_chunk, context)
                            completion_kwargs["messages"] = smaller_prompt
                            
                            # Try again with smaller chunk
                            response = litellm.completion(**completion_kwargs)
                            chunk_message = response.choices[0].message.content.strip()
                            messages.append(chunk_message)
                            progress.update(task, advance=1)
                        else:
                            # Re-raise other errors
                            raise
                except Exception as e:
                    progress.stop()
                    raise RuntimeError(
                        f"Error generating message for chunk {i+1}: {str(e)}"
                    )

        # Combine messages
        combined = "\n\n".join(messages)
        # Try to generate a summary if needed
        if len(messages) > 1 and token_count(combined) < MAX_TOKENS // 2:
            try:
                summary_prompt = [
                    {
                        "role": "system",
                        "content": "You are a commit message summarizer. Create a concise summary of these individual commit messages, following the same style guidelines.",
                    },
                    {
                        "role": "user",
                        "content": f"Summarize these related commit messages into one cohesive message:\n\n{combined}",
                    },
                ]
    
                # Create completion kwargs
                summary_completion_kwargs = {
                    "model": MODEL_NAME,
                    "messages": summary_prompt,
                    "temperature": 0.7,
                    "max_tokens": 100,
                }

                # Get API key from config
                api_key = config.get(ConfigKeys.OCO_API_KEY)
                api_base = config.get(ConfigKeys.OCO_API_URL)

                if api_key:
                    summary_completion_kwargs["api_key"] = api_key
                if api_base:
                    summary_completion_kwargs["api_base"] = api_base
                    
                # Convert any boolean values in the kwargs (including nested structures)
                summary_completion_kwargs = convert_bools_to_strings(summary_completion_kwargs)
    
                # Ensure temperature is a float
                if "temperature" in summary_completion_kwargs:
                    summary_completion_kwargs["temperature"] = float(
                        summary_completion_kwargs["temperature"]
                    )
    
                # Ensure max_tokens is an int
                if "max_tokens" in summary_completion_kwargs:
                    summary_completion_kwargs["max_tokens"] = int(
                        summary_completion_kwargs["max_tokens"]
                    )
    
                # Log types before calling litellm if logging is enabled
                if not logger.disabled:
                    logger.debug("Argument types before litellm.completion (summary):")
                    for key, value in summary_completion_kwargs.items():
                        # Special handling for messages list
                        if key == 'messages' and isinstance(value, list):
                            logger.debug(f"  - {key}: list")
                            for idx, msg in enumerate(value):
                                logger.debug(f"    - message[{idx}]: {type(msg)}")
                                if isinstance(msg, dict):
                                    for msg_key, msg_val in msg.items():
                                        logger.debug(f"      - {msg_key}: {type(msg_val)}")
                        else:
                            logger.debug(f"  - {key}: {type(value)}")
    
                    logger.debug(f"Summary completion kwargs: {summary_completion_kwargs}")
                response = litellm.completion(**summary_completion_kwargs)
                return response.choices[0].message.content.strip()
            except Exception:
                # Fall back to the combined messages if summarization fails
                pass
        return combined

    # For single chunks, generate directly
    prompt = create_commit_prompt(diff_chunks[0], context)
    try:
        with Progress() as progress:
            task = progress.add_task(
                f"[cyan]{get_text('generatingCommitMessage')}...", total=1
            )

            # Get API key from config
            api_key = config.get(ConfigKeys.OCO_API_KEY)
            api_base = config.get(ConfigKeys.OCO_API_URL)

            if not logger.disabled:
                logger.debug(f"Using model: {MODEL_NAME}")
                logger.debug(f"API base URL: {api_base}")
                logger.debug(f"API key present: {bool(api_key)}")

            # Configure litellm with API key if available
            completion_kwargs = {
                "model": MODEL_NAME,
                "messages": prompt,
                "temperature": 0.7,
                "max_tokens": 100,
            }

            if api_key:
                completion_kwargs["api_key"] = api_key
            if api_base:
                completion_kwargs["api_base"] = api_base
    
            # Debug the messages after conversion if logging is enabled
            if not logger.disabled:
                logger.debug("Messages after conversion:")
                for i, msg in enumerate(completion_kwargs["messages"]):
                    logger.debug(f"Message {i}: {msg}")

            # Make sure all values in the completion_kwargs are properly typed (including nested structures)
            if not logger.disabled:
                logger.debug("Converting any boolean values to strings in completion_kwargs")
            completion_kwargs = convert_bools_to_strings(completion_kwargs)
    
            if not logger.disabled:
                logger.debug(f"Completion kwargs: {completion_kwargs}")
    
            # Ensure temperature is a float
            if "temperature" in completion_kwargs:
                completion_kwargs["temperature"] = float(
                    completion_kwargs["temperature"]
                )

            # Ensure max_tokens is an int
            if "max_tokens" in completion_kwargs:
                completion_kwargs["max_tokens"] = int(completion_kwargs["max_tokens"])

            # Log types before calling litellm if logging is enabled
            if not logger.disabled:
                logger.debug("Argument types before litellm.completion (single chunk):")
                for key, value in completion_kwargs.items():
                    # Special handling for messages list
                    if key == 'messages' and isinstance(value, list):
                        logger.debug(f"  - {key}: list")
                        for idx, msg in enumerate(value):
                            logger.debug(f"    - message[{idx}]: {type(msg)}")
                            if isinstance(msg, dict):
                                for msg_key, msg_val in msg.items():
                                    logger.debug(f"      - {msg_key}: {type(msg_val)}")
                    else:
                        logger.debug(f"  - {key}: {type(value)}")

            if not logger.disabled:
                logger.debug(f"Final completion kwargs: {completion_kwargs}")
            response = litellm.completion(**completion_kwargs)
            if not logger.disabled:
                logger.debug(f"LiteLLM response: {response}")
            progress.update(task, advance=1)

        message = response.choices[0].message.content.strip()
        if not logger.disabled:
            logger.debug(f"Generated message: {message}")
        return message
    except Exception as e:
        raise RuntimeError(f"Failed to generate commit message: {str(e)}")


def check_message_template(
    extra_args: List[str], placeholder: str = DEFAULT_TEMPLATE_PLACEHOLDER
) -> Optional[str]:
    """
    Check if a message template is specified in the extra args.

    Args:
        extra_args: Additional command line arguments
        placeholder: Template placeholder string

    Returns:
        The template string if found, None otherwise
    """
    for arg in extra_args:
        if placeholder in arg:
            return arg
    return None


def convert_bools_to_strings(obj):
    """
    Recursively convert all boolean values to strings in a nested structure.

    Args:
        obj: The object to convert (dict, list, etc.)

    Returns:
        The object with all booleans converted to strings
    """
    if isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            if isinstance(value, bool):
                result[key] = str(value).lower()
            elif isinstance(value, (dict, list)):
                result[key] = convert_bools_to_strings(value)
            else:
                result[key] = value
        return result
    elif isinstance(obj, list):
        result = []
        for item in obj:
            if isinstance(item, bool):
                result.append(str(item).lower())
            elif isinstance(item, (dict, list)):
                result.append(convert_bools_to_strings(item))
            else:
                result.append(item)
        return result
    else:
        return obj


def apply_template(
    message: str, template: str, placeholder: str = DEFAULT_TEMPLATE_PLACEHOLDER
) -> str:
    """
    Apply a template to the commit message.

    Args:
        message: The generated commit message
        template: Template string with placeholder
        placeholder: Placeholder string to replace

    Returns:
        Formatted commit message
    """
    return template.replace(placeholder, message)


def run_git_commit(message: str, extra_args: List[str]) -> bool:
    """
    Execute the git commit command.

    Args:
        message: Commit message
        extra_args: Additional arguments for git commit

    Returns:
        True if successful, False otherwise
    """
    # Filter out any args that might contain message templates
    filtered_args = [
        arg for arg in extra_args if DEFAULT_TEMPLATE_PLACEHOLDER not in arg
    ]

    # Prepare the commit command
    cmd = ["git", "commit", "-m", message] + filtered_args

    logger.debug(f"Running git commit command: {cmd}")

    try:
        result = subprocess.run(cmd, check=True)
        logger.debug(f"Git commit result: {result}")
        return True  # If we get here, the command succeeded
    except subprocess.CalledProcessError as e:
        logger.error(f"Git commit failed: {e}")
        raise RuntimeError(f"Git commit failed: {e}")


@click.command()
@click.argument("extra_args", nargs=-1)
@click.option("--context", "-c", default="", help="Additional context for the AI")
@click.option(
    "--stage-all", "-a", is_flag=True, help="Stage all changes before committing"
)
@click.option("--skip-confirm", is_flag=True, help="Skip commit confirmation")
def commit(
    extra_args: List[str] = None,
    context: str = "",
    stage_all: Union[bool, str] = False,
    skip_confirm: Union[bool, str] = False,
) -> None:
    """Generate an AI commit message from your staged changes."""
    if extra_args is None:
        extra_args = []
    # Output for test compatibility
    click.echo("Running commit command with LiteLLM integration")
    if not logger.disabled:
        logger.debug(
            f"commit() called with: extra_args={extra_args}, context={context}, stage_all={stage_all}, skip_confirm={skip_confirm}"
        )

    try:
        # Check if we're in a git repository
        if not is_git_repository():
            console.print(
                f"[bold red]{get_text('error')}:[/bold red] {get_text('invalidGitRepo')}"
            )
            sys.exit(1)

        # Stage all changes if requested
        # Convert stage_all to boolean if it's a string
        stage_all_bool = stage_all if isinstance(stage_all, bool) else stage_all.lower() in ('true', 'yes', '1', 'y')
        if stage_all_bool:
            console.print("Staging all changes...")
            stage_all_changes()

        # Get the diff of staged changes
        diff = get_staged_diff()
        
        # Get staged and changed files
        staged_files = get_staged_files()
        unstaged_files = get_unstaged_files()
            
        # If no staged files but we have unstaged changes
        if not staged_files and unstaged_files:
            console.print("[yellow]No files are staged[/yellow]")
            
            # Show list of changed files
            console.print("[cyan]Changed files:[/cyan]")
            for file in unstaged_files:
                console.print(f"  - {file}")
            
            # Ask if user wants to stage all files
            if Confirm.ask("Do you want to stage all files and generate commit message?"):
                console.print("Staging all changes...")
                stage_all_changes()
                # Get the diff again after staging
                diff = get_staged_diff()
                staged_files = get_staged_files()
            else:
                # Let user select specific files to stage
                if len(unstaged_files) > 0:
                    from rich.prompt import Prompt
                    
                    console.print(f"[cyan]Select the files you want to add to the commit:[/cyan]")
                    for i, file in enumerate(unstaged_files):
                        console.print(f"  {i+1}. {file}")
                    
                    selected = Prompt.ask("Enter file numbers (comma-separated, or 'all' for all files)")
                    
                    if selected.lower() == 'all':
                        files_to_stage = unstaged_files
                    else:
                        try:
                            indices = [int(idx.strip()) - 1 for idx in selected.split(',')]
                            files_to_stage = [unstaged_files[i] for i in indices if 0 <= i < len(unstaged_files)]
                        except (ValueError, IndexError):
                            console.print("[bold red]Invalid selection. No files staged.[/bold red]")
                            sys.exit(1)
                    
                    if files_to_stage:
                        # Stage selected files
                        stage_files(files_to_stage)
                        
                        # Get the diff again after staging
                        diff = get_staged_diff()
                        staged_files = get_staged_files()
                    else:
                        console.print("[yellow]No files selected for staging. Exiting.[/yellow]")
                        sys.exit(0)
        
        # If we still have no diff after all the staging attempts
        if not diff:
            console.print(
                f"[bold yellow]{get_text('warning')}:[/bold yellow] {get_text('noChangesDetected')}"
            )
            sys.exit(0)

        # Get staged files for display
        staged_files = get_staged_files()
        console.print(f"[green]Found {len(staged_files)} staged files:[/green]")
        for file in staged_files:
            console.print(f"  - {file}")

        # Generate commit message
        try:
            message = generate_commit_message(diff, context)
        except Exception as e:
            console.print(
                f"[bold red]Error generating commit message:[/bold red] {str(e)}"
            )
            sys.exit(1)

        # Check for template
        template = check_message_template(extra_args)
        if template:
            message = apply_template(message, template)

        # Display the generated message
        console.print(
            Panel(
                message, title=get_text("commitMessageGenerated"), border_style="green"
            )
        )

        # Confirm and commit
        # Convert skip_confirm to boolean if it's a string
        skip_confirm_bool = skip_confirm if isinstance(skip_confirm, bool) else skip_confirm.lower() in ('true', 'yes', '1', 'y')
        if not skip_confirm_bool:
            confirmed = Confirm.ask(get_text("confirmCommit"))
            if not confirmed:
                console.print("[yellow]Commit aborted by user.[/yellow]")
                sys.exit(0)

        # Execute git commit
        try:
            logger.debug(f"About to run git commit with message: {message}")
            logger.debug(f"Extra args: {extra_args}")
            success = run_git_commit(message, list(extra_args))
            logger.debug(f"Git commit result: {success}")
            console.print(f"[bold green]✓ {get_text('commitSuccess')}![/bold green]")
        except Exception as e:
            logger.exception("Failed to commit changes")
            console.print(f"[bold red]Failed to commit changes: {str(e)}[/bold red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    commit()
