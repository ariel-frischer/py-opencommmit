"""Prompt templates for commitlint integration."""

import logging
import os
from typing import Dict, List, Any

from ...commands.config import get_config, ConfigKeys
from ...i18n import get_text

logger = logging.getLogger("opencommit")

# Get configuration
config = get_config()
language = config.get(ConfigKeys.OCO_LANGUAGE, "en")

# System identity prompt
IDENTITY = "You are an AI assistant specialized in generating high-quality git commit messages."

# Initial diff prompt
INIT_DIFF_PROMPT = {
    "role": "user",
    "content": "Here's the git diff output that needs a commit message:"
}

# Type descriptions for conventional commits
TYPE_DESCRIPTIONS = {
    "feat": "A new feature",
    "fix": "A bug fix",
    "docs": "Documentation only changes",
    "style": "Changes that do not affect the meaning of the code (white-space, formatting, etc)",
    "refactor": "A code change that neither fixes a bug nor adds a feature",
    "perf": "A code change that improves performance",
    "test": "Adding missing tests or correcting existing tests",
    "build": "Changes that affect the build system or external dependencies",
    "ci": "Changes to CI configuration files and scripts",
    "chore": "Other changes that don't modify src or test files",
    "revert": "Reverts a previous commit"
}

# LLM-readable rule descriptions
def get_llm_readable_rules(key: str, applicable: str, value: Any = None, prompt: Dict = None) -> str:
    """Generate LLM-readable rule descriptions."""
    
    # Case rule
    if key.endswith("-case"):
        return f"The {key.split('-')[0]} should {applicable} be in {value if isinstance(value, str) else ', '.join(value) if isinstance(value, list) else 'proper'} case."
    
    # Empty rule
    elif key.endswith("-empty"):
        return f"The {key.split('-')[0]} should {applicable} be empty."
    
    # Blank line rule
    elif key.endswith("-leading-blank"):
        return f"There should {applicable} be a blank line at the beginning of the {key.split('-')[0]}."
    
    # Max length rule
    elif key.endswith("-max-length"):
        return f"The {key.split('-')[0]} should {applicable} have {value} characters or less."
    
    # Min length rule
    elif key.endswith("-min-length"):
        return f"The {key.split('-')[0]} should {applicable} have {value} characters or more."
    
    # Full stop rule
    elif key.endswith("-full-stop"):
        return f"The {key.split('-')[0]} should {applicable} end with '{value}'."
    
    # Enum rule for types
    elif key == "type-enum":
        if isinstance(value, list):
            type_items = []
            for v in value:
                description = TYPE_DESCRIPTIONS.get(v, "")
                if description:
                    type_items.append(f"{v} ({description})")
                else:
                    type_items.append(v)
            return f"The type should {applicable} be one of the following values:\n  - " + "\n  - ".join(type_items)
        return f"The type should {applicable} be one of the following values: {value}"
    
    # Enum rule for other fields
    elif key.endswith("-enum"):
        if isinstance(value, list):
            return f"The {key.split('-')[0]} should {applicable} be one of the following values:\n  - " + "\n  - ".join(value)
        return f"The {key.split('-')[0]} should {applicable} be one of the following values: {value}"
    
    # Default case
    return f"The {key} should {applicable} follow the rule with value: {value}"


def create_commit_prompt(diff: str, context: str = "") -> List[Dict[str, str]]:
    """
    Create a well-engineered prompt for commit message generation using commitlint rules.
    
    Args:
        diff: Git diff
        context: Additional context
        
    Returns:
        List of messages for the LLM
    """
    # Get configuration values
    omit_scope = config.get(ConfigKeys.OCO_OMIT_SCOPE, False)
    use_emoji = config.get(ConfigKeys.OCO_EMOJI, False)
    add_description = config.get(ConfigKeys.OCO_DESCRIPTION, True)  # Default to True for better messages
    add_why = config.get(ConfigKeys.OCO_WHY, True)  # Default to True for better messages
    one_line_commit = config.get(ConfigKeys.OCO_ONE_LINE_COMMIT, False)
    
    # Extract file names from diff
    file_names = extract_file_names_from_diff(diff)
    
    # Get appropriate scope for these files
    scope = get_scope_for_files(file_names)
    
    # For display in the prompt
    file_names_str = ", ".join(file_names) if file_names else "unknown"
    
    # Define commit structure based on config
    structure_of_commit = (
        "- Header of commit is composed of type and subject: <type-of-commit>: <subject-of-commit>\n"
        "- Description of commit is composed of body and footer (optional): <body-of-commit>\n<footer(s)-of-commit>"
    ) if omit_scope else (
        "- Header of commit is composed of type, scope, subject: <type-of-commit>(<scope-of-commit>): <subject-of-commit>\n"
        "- Description of commit is composed of body and footer (optional): <body-of-commit>\n<footer(s)-of-commit>"
    )
    
    # Build the system prompt
    system_content = f"{IDENTITY} Your mission is to create clean and comprehensive commit messages in the conventional commit format."
    
    if add_why:
        system_content += " Explain WHAT were the changes and WHY they were done."
    else:
        system_content += " Explain WHAT were the changes."
        
    system_content += " I'll send you an output of 'git diff --staged' command, and you convert it into a commit message.\n"
    
    if use_emoji:
        system_content += "Use GitMoji convention to preface the commit.\n"
    else:
        system_content += "Do not preface the commit with anything.\n"
    
    if add_description:
        system_content += "Add a detailed description of the changes after the commit message header. Start the description on a new line after a blank line. Don't start it with 'This commit', just describe the changes and their purpose.\n"
    else:
        system_content += "Don't add any descriptions to the commit, only the commit message header (type, scope, subject).\n"
    
    system_content += f"Use the present tense. Use {language} to answer.\n"
    
    if one_line_commit:
        system_content += "Craft a concise commit message header that encapsulates all changes made, with an emphasis on the primary updates. "
        system_content += "If the modifications share a common theme or scope, mention it succinctly; otherwise, leave the scope out to maintain focus. "
        system_content += "The goal is to provide a clear and unified overview of the changes in a one single message header, without diverging into a list of commit per file change.\n"
    
    # Define commit structure and scope rules
    if omit_scope:
        system_content += "Do not include a scope in the commit message format. Use the format: <type>: <subject>\n"
        structure_of_commit = (
            "- Header: <type>: <subject>\n"
            "- Body/Footer (Optional): <description>"
        )
    else:
        system_content += "ALWAYS include a scope in the commit message format. Use the format: <type>(<scope>): <subject>\n"
        system_content += f"The files changed in this commit are: {file_names_str}.\n"
        system_content += f"Based on the files changed, the suggested scope is: '{scope}'. Use this suggested scope or a more specific one if appropriate.\n"
        
        if len(file_names) > 3:
            system_content += "When multiple files are changed, group them by functionality (e.g., 'cli', 'config', 'docs', 'auth', 'api') rather than listing all filenames.\n"
        
        structure_of_commit = (
            "- Header: <type>(<scope>): <subject>\n"
            "- Body/Footer (Optional): <description>"
        )

    # Add explicit instructions for conventional commit format with detailed examples
    system_content += f"""
Your commit message MUST follow the conventional commit format.

Structure:
{structure_of_commit}

Header Rules:
- Type: Must be lowercase. Choose from: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert.
- Scope: { 'Should be omitted.' if omit_scope else 'MUST be included in parentheses. Use the suggested scope or a meaningful name reflecting the changed component/files.'}
- Subject: Concise description of the change in imperative mood (e.g., 'add', 'fix', 'update'). Do not end with a period. Keep the header line under 72 characters.

Body/Footer Rules (only if OCO_DESCRIPTION=true):
- Separate header from body with a blank line.
- Explain WHAT changed and WHY for *all* changes.
- Keep lines under 72 characters.

IMPORTANT: If the provided diff contains multiple distinct logical changes (e.g., a refactoring AND a new feature, or documentation updates AND a bug fix), you MUST generate a separate conventional commit header line for EACH distinct change. Follow each header line with its corresponding description if OCO_DESCRIPTION is true, or list all headers first followed by a combined description.

Examples (assuming OCO_OMIT_SCOPE=false):

Single Change:
```
feat(auth): implement OAuth2 authentication flow

Add OAuth2 authentication support with Google and GitHub providers.
This improves security by using industry-standard protocols and allows users
to log in with existing accounts, reducing onboarding friction.
```

Multiple Distinct Changes (Example):
```
refactor(auth, user): simplify login logic and database schema

Streamline the authentication process and update user table structure for clarity.

feat(profile): add user profile editing feature

Allow users to update their display name and profile picture.
```

NEVER generate a commit message {'with a scope in parentheses' if omit_scope else 'without a scope in parentheses'}. The scope should be meaningful and reflect the changed files/components for that specific line item.
"""
    
    if context:
        system_content += f"\nAdditional context from the user: {context}"
    
    # Create the messages array
    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": f"Generate a commit message for the following git diff:\n\n{diff}"}
    ]
    
    return messages


def extract_file_names_from_diff(diff: str) -> List[str]:
    """
    Extract file names from a git diff.
    
    Args:
        diff: Git diff string
        
    Returns:
        List of file names
    """
    import re
    
    # Pattern to match file names in git diff
    pattern = r"diff --git a/(.*?) b/(.*?)$"
    
    # Find all matches
    matches = re.findall(pattern, diff, re.MULTILINE)
    
    # Extract the 'b' file names (current version)
    file_names = [match[1] for match in matches if match[1]]
    
    return file_names


def group_files_by_type(files: List[str]) -> Dict[str, List[str]]:
    """
    Group files by their type/purpose to create meaningful scopes.
    
    Args:
        files: List of file paths
        
    Returns:
        Dictionary mapping scope names to lists of files
    """
    # Initialize groups
    groups = {
        "docs": [],
        "config": [],
        "cli": [],
        "core": [],
        "utils": [],
        "commands": [],
        "modules": [],
        "tests": [],
    }
    
    for file in files:
        # Documentation files
        if file.endswith(('.md', '.rst', '.txt')) or 'docs/' in file or 'README' in file:
            groups["docs"].append(file)
        
        # Configuration files
        elif file.endswith(('.toml', '.json', '.yaml', '.yml', '.ini')) or 'config' in file:
            groups["config"].append(file)
        
        # CLI files
        elif 'cli.py' in file or 'cli/' in file:
            groups["cli"].append(file)
        
        # Command files
        elif 'commands/' in file or 'cmd/' in file:
            groups["commands"].append(file)
        
        # Module files
        elif 'modules/' in file:
            groups["modules"].append(file)
        
        # Test files
        elif 'test' in file or 'tests/' in file:
            groups["tests"].append(file)
        
        # Utility files
        elif 'utils/' in file or 'util/' in file or 'helpers/' in file:
            groups["utils"].append(file)
        
        # Core files (everything else)
        else:
            groups["core"].append(file)
    
    # Remove empty groups
    return {k: v for k, v in groups.items() if v}


def get_scope_for_files(files: List[str]) -> str:
    """
    Generate an appropriate scope string for the given files.
    
    Args:
        files: List of file paths
        
    Returns:
        Scope string for commit message
    """
    if not files:
        return "unknown"
    
    # If only one file, use its name (or relevant part) as scope
    if len(files) == 1:
        # Optionally clean up the filename (e.g., remove path)
        # For now, return the full path as provided
        return files[0]

    # If 2-3 files, list them all
    elif len(files) <= 3:
        return ", ".join(files)
    
    # For more files, try to group them
    groups = group_files_by_type(files)
    
    # If all files are in the same group, use that group name
    if len(groups) == 1:
        group_name, group_files = next(iter(groups.items()))
        
        # If the group has a clear common directory, use that
        common_prefix = os.path.commonprefix(group_files)
        if common_prefix and '/' in common_prefix:
            return common_prefix.rstrip('/')
        
        return group_name
    
    # If multiple groups, list the group names
    return ", ".join(groups.keys())


def create_consistency_prompt(prompts: List[str]) -> List[Dict[str, str]]:
    """
    Create a prompt to generate LLM-readable rules based on commitlint rules.
    
    Args:
        prompts: List of prompt strings
        
    Returns:
        List of messages for the LLM
    """
    # Get configuration
    omit_scope = config.get(ConfigKeys.OCO_OMIT_SCOPE, False)
    
    # Get translation
    local_language = get_text("localLanguage")
    
    system_content = f"{IDENTITY} Your mission is to create clean and comprehensive commit messages for two different changes in a single codebase and output them in the provided JSON format: one for a bug fix and another for a new feature.\n\n"
    
    system_content += "Here are the specific requirements and conventions that should be strictly followed:\n\n"
    
    system_content += "Commit Message Conventions:\n"
    system_content += "- The commit message consists of three parts: Header, Body, and Footer.\n"
    system_content += f"- Header: \n  - Format: {('`<type>: <subject>`') if omit_scope else ('`<type>(<scope>): <subject>`')}\n"
    system_content += "- " + "\n- ".join(prompts) + "\n\n"
    
    system_content += "JSON Output Format:\n"
    system_content += "- The JSON output should contain the commit messages for a bug fix and a new feature in the following format:\n"
    system_content += "```json\n"
    system_content += "{\n"
    system_content += f'  "localLanguage": "{local_language}",\n'
    system_content += '  "commitFix": "<Header of commit for bug fix with scope>",\n'
    system_content += '  "commitFeat": "<Header of commit for feature with scope>",\n'
    system_content += '  "commitFixOmitScope": "<Header of commit for bug fix without scope>",\n'
    system_content += '  "commitFeatOmitScope": "<Header of commit for feature without scope>",\n'
    system_content += '  "commitDescription": "<Description of commit for both the bug fix and the feature>"\n'
    system_content += "}\n"
    system_content += "```\n\n"
    
    system_content += "- The \"commitDescription\" should not include the commit message's header, only the description.\n"
    system_content += "- Description should not be more than 74 characters.\n\n"
    
    system_content += "Additional Details:\n"
    system_content += "- Changing the variable 'port' to uppercase 'PORT' is considered a bug fix.\n"
    system_content += "- Allowing the server to listen on a port specified through the environment variable is considered a new feature.\n\n"
    
    system_content += "Example Git Diff is to follow:"
    
    # Create the messages array
    messages = [
        {"role": "system", "content": system_content},
        INIT_DIFF_PROMPT
    ]
    
    return messages
