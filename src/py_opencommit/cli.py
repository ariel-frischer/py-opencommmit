#!/usr/bin/env python3
"""
OpenCommit CLI - AI-powered commit message generator.
"""

import sys
import os
import warnings
import click
import logging

from rich.console import Console
# Use absolute imports now that it's a proper package
from py_opencommit.i18n import get_text, load_translations, get_language_from_alias

# Filter out Pydantic warnings
warnings.filterwarnings("ignore", message="Valid config keys have changed in V2")

console = Console()
logger = logging.getLogger("opencommit")


@click.group()
@click.version_option()
@click.option(
    "--language", "-l", help="Set the language for the CLI", envvar="OCO_LANGUAGE"
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    help="Set the logging level",
)
def cli(language, log_level):
    """PyOC - AI-powered commit message generator."""
    # Configure logging
    if log_level:
        numeric_level = getattr(logging, log_level)
        logging.basicConfig(level=numeric_level)
        logger.setLevel(numeric_level)
    else:
        # Disable all logging by default
        logging.basicConfig(level=logging.CRITICAL)
        logger.disabled = True
        # Also disable litellm logging
        logging.getLogger("litellm").disabled = True

    # Set the language if provided
    if language:
        # Try to get the language code from the alias
        lang_code = get_language_from_alias(language)
        if lang_code:
            # Load the language translations
            load_translations(lang_code)
            # Store the language preference in environment variable for child processes
            os.environ["OCO_LANGUAGE"] = lang_code
        else:
            console.print(
                f"[yellow]Warning: Unknown language '{language}'. Using default language.[/yellow]"
            )


@cli.command()
@click.option("--stage-all", "-a", is_flag=True, help="Stage all changes before commit")
@click.option("--skip-confirm", is_flag=True, help="Skip commit confirmation")
@click.option("--context", "-c", help="Additional context for the AI")
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    help="Set the logging level",
)
@click.argument("extra_args", nargs=-1)
def commit(stage_all, skip_confirm, context, log_level, extra_args):
    """Generate an AI commit message from your staged changes."""
    # Configure logging if specified at command level
    import logging

    if log_level:

        numeric_level = getattr(logging, log_level)
        logging.basicConfig(level=numeric_level)
        logger = logging.getLogger("opencommit")
        logger.setLevel(numeric_level)
        logger.disabled = False
    try:
        # Import here to avoid circular imports
        from py_opencommit.commands.commit import commit as run_commit

        logger = logging.getLogger("opencommit")

        if not logger.disabled:
            logger.debug(
                f"CLI commit command called with: stage_all={stage_all}, skip_confirm={skip_confirm}, context={context}, extra_args={extra_args}"
            )

        # Convert boolean flags to strings to avoid type errors
        stage_all_str = "true" if stage_all else "false"
        skip_confirm_str = "true" if skip_confirm else "false"

        # Call the function directly with the parameters
        run_commit(
            list(extra_args) if extra_args else [],
            context or "",
            stage_all_str,
            skip_confirm_str,
        )
    except TypeError as e:
        console.print(
            f"[bold red]{get_text('error')} (TypeError in commit logic):[/bold red] {str(e)}"
        )
        console.print(
            "[yellow]This likely occurred during commit message generation or processing.[/yellow]"
        )
        sys.exit(1)
    except Exception as e:
        console.print(
            f"[bold red]{get_text('error')} (General error in commit command):[/bold red] {str(e)}"
        )
        sys.exit(1)


@cli.command()
@click.argument(
    "mode", type=click.Choice(["get", "set"]), required=False, default="get"
)
@click.argument("key", required=False)
@click.option(
    "--project", "-p", is_flag=True, help="Use project-level configuration (.env file)"
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    help="Set the logging level",
)
@click.argument("value", required=False)
def config(mode, key, project, log_level, value):
    """Get or set configuration values.

    Configuration Options:
      OCO_API_KEY                     API key for LLM provider
      OCO_TOKENS_MAX_INPUT            Maximum input tokens (default: 40960)
      OCO_TOKENS_MAX_OUTPUT           Maximum output tokens (default: 4096)
      OCO_DESCRIPTION                 Include description in commit (true/false)
      OCO_EMOJI                       Include emoji in commit (true/false)
      OCO_MODEL                       LLM model to use (e.g., gpt-4, gpt-3.5-turbo)
      OCO_LANGUAGE                    Language for messages (en, fr, de, etc.)
      OCO_WHY                         Include reasoning in commit (true/false)
      OCO_AI_PROVIDER                 AI provider (openai, anthropic, etc.)
      OCO_MESSAGE_TEMPLATE_PLACEHOLDER Placeholder in commit template
      OCO_PROMPT_MODULE               Prompt module (conventional-commit, @commitlint)
      OCO_ONE_LINE_COMMIT             Use one-line commits (true/false)
      OCO_OMIT_SCOPE                  Omit scope in commit message (true/false)

    Examples:
      oco config get                   # Get all configuration values
      oco config get OCO_API_KEY       # Get specific configuration value
      oco config set OCO_API_KEY=sk-... # Set global configuration value
      oco config set OCO_MODEL=gpt-4 --project # Set project configuration value
    """
    # Configure logging if specified at command level
    if log_level:
        import logging

        numeric_level = getattr(logging, log_level)
        logging.basicConfig(level=numeric_level)
        logger = logging.getLogger("opencommit")
        logger.setLevel(numeric_level)
        logger.disabled = False
    try:
        # Import here to avoid circular imports
        from py_opencommit.commands.config import config as run_config

        run_config(mode, key, value, project)
    except Exception as e:
        console.print(f"[bold red]{get_text('error')}:[/bold red] {str(e)}")
        sys.exit(1)


@cli.command()
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    help="Set the logging level",
)
def githook(log_level):
    """Install git prepare-commit-msg hook."""
    # Configure logging if specified at command level
    if log_level:
        import logging

        numeric_level = getattr(logging, log_level)
        logging.basicConfig(level=numeric_level)
        logger = logging.getLogger("opencommit")
        logger.setLevel(numeric_level)
        logger.disabled = False
    try:
        # Import here to avoid circular imports
        from py_opencommit.commands.githook import githook as run_githook

        run_githook()
    except Exception as e:
        console.print(f"[bold red]{get_text('error')}:[/bold red] {str(e)}")
        sys.exit(1)


def main():
    """Entry point for the CLI."""
    try:
        # Run migrations before starting the CLI
        from py_opencommit.migrations import run_migrations

        run_migrations()
    except Exception as e:
        console.print(f"[bold red]Error running migrations:[/bold red] {str(e)}")

    cli()


if __name__ == "__main__":
    main()
