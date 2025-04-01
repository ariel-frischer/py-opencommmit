"""Prompt templates for commitlint integration."""

import logging
import os
import json
from typing import Dict, List, Any, Tuple, Optional, Union

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

class CommitLintConfig:
    """Class to handle commitlint configuration and rule processing."""
    
    def __init__(self, config_data: Dict[str, Any]):
        """Initialize with configuration data."""
        self.config = config_data
        self.translation = self.get_translation(config_data.get("OCO_LANGUAGE", "en"))
        
        # Type descriptions for conventional commits
        self.type_descriptions = {
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

    def get_translation(self, language: str) -> Dict[str, str]:
        """Get translation for the specified language."""
        translations = {
            "en": {"localLanguage": "English"},
            # Add other language mappings as needed
        }
        return translations.get(language, translations["en"])

    def get_type_rule_extra_description(self, type_value: str, prompt: Dict[str, Any]) -> Optional[str]:
        """Get extra description for a type rule."""
        return (prompt.get("questions", {})
                .get("type", {})
                .get("enum", {})
                .get(type_value, {})
                .get("description"))

    def llm_readable_rules(self) -> Dict[str, callable]:
        """Get dictionary of functions to generate LLM-readable rules."""
        return {
            "blankline": lambda key, applicable, *_: 
                f"There should {applicable} be a blank line at the beginning of the {key}.",
                
            "caseRule": lambda key, applicable, value, *_: 
                f"The {key} should {applicable} be in {self._format_case_value(value)} case.",
                
            "emptyRule": lambda key, applicable, *_: 
                f"The {key} should {applicable} be empty.",
                
            "enumRule": lambda key, applicable, value, *_: 
                f"The {key} should {applicable} be one of the following values:\n  - " + 
                "\n  - ".join(value) if isinstance(value, list) else 
                f"The {key} should {applicable} be one of the following values: {value}",
                
            "enumTypeRule": lambda key, applicable, value, prompt: 
                f"The {key} should {applicable} be one of the following values:\n  - " + 
                "\n  - ".join([f"{v} ({self.get_type_rule_extra_description(v, prompt) or self.type_descriptions.get(v, '')})" 
                              if (self.get_type_rule_extra_description(v, prompt) or self.type_descriptions.get(v, '')) 
                              else v 
                              for v in value]) if isinstance(value, list) else 
                f"The {key} should {applicable} be one of the following values: {value}",
                
            "fullStopRule": lambda key, applicable, value, *_: 
                f"The {key} should {applicable} end with '{value}'.",
                
            "maxLengthRule": lambda key, applicable, value, *_: 
                f"The {key} should {applicable} have {value} characters or less.",
                
            "minLengthRule": lambda key, applicable, value, *_: 
                f"The {key} should {applicable} have {value} characters or more.",
        }
    
    def _format_case_value(self, value: Union[str, List[str]]) -> str:
        """Format case value for display in rules."""
        if isinstance(value, list):
            return "one of the following cases: " + ", ".join(value)
        return f"{value}"

    def rules_prompts(self) -> Dict[str, callable]:
        """Get dictionary of functions to generate rule prompts."""
        readable_rules = self.llm_readable_rules()
        
        return {
            "body-case": lambda applicable, value, prompt=None: 
                readable_rules["caseRule"]("body", applicable, value),
                
            "body-empty": lambda applicable, *_: 
                readable_rules["emptyRule"]("body", applicable),
                
            "body-full-stop": lambda applicable, value, *_: 
                readable_rules["fullStopRule"]("body", applicable, value),
                
            "body-leading-blank": lambda applicable, *_: 
                readable_rules["blankline"]("body", applicable),
                
            "body-max-length": lambda applicable, value, *_: 
                readable_rules["maxLengthRule"]("body", applicable, value),
                
            "body-max-line-length": lambda applicable, value, *_: 
                f"Each line of the body should {applicable} have {value} characters or less.",
                
            "body-min-length": lambda applicable, value, *_: 
                readable_rules["minLengthRule"]("body", applicable, value),
                
            "footer-case": lambda applicable, value, *_: 
                readable_rules["caseRule"]("footer", applicable, value),
                
            "footer-empty": lambda applicable, *_: 
                readable_rules["emptyRule"]("footer", applicable),
                
            "footer-leading-blank": lambda applicable, *_: 
                readable_rules["blankline"]("footer", applicable),
                
            "footer-max-length": lambda applicable, value, *_: 
                readable_rules["maxLengthRule"]("footer", applicable, value),
                
            "footer-max-line-length": lambda applicable, value, *_: 
                f"Each line of the footer should {applicable} have {value} characters or less.",
                
            "footer-min-length": lambda applicable, value, *_: 
                readable_rules["minLengthRule"]("footer", applicable, value),
                
            "header-case": lambda applicable, value, *_: 
                readable_rules["caseRule"]("header", applicable, value),
                
            "header-full-stop": lambda applicable, value, *_: 
                readable_rules["fullStopRule"]("header", applicable, value),
                
            "header-max-length": lambda applicable, value, *_: 
                readable_rules["maxLengthRule"]("header", applicable, value),
                
            "header-min-length": lambda applicable, value, *_: 
                readable_rules["minLengthRule"]("header", applicable, value),
                
            "references-empty": lambda applicable, *_: 
                readable_rules["emptyRule"]("references section", applicable),
                
            "scope-case": lambda applicable, value, *_: 
                readable_rules["caseRule"]("scope", applicable, value),
                
            "scope-empty": lambda applicable, *_: 
                readable_rules["emptyRule"]("scope", applicable),
                
            "scope-enum": lambda applicable, value, *_: 
                readable_rules["enumRule"]("scope", applicable, value),
                
            "scope-max-length": lambda applicable, value, *_: 
                readable_rules["maxLengthRule"]("scope", applicable, value),
                
            "scope-min-length": lambda applicable, value, *_: 
                readable_rules["minLengthRule"]("scope", applicable, value),
                
            "signed-off-by": lambda applicable, value, *_: 
                f"The commit message should {applicable} have a \"Signed-off-by\" line with the value \"{value}\".",
                
            "subject-case": lambda applicable, value, *_: 
                readable_rules["caseRule"]("subject", applicable, value),
                
            "subject-empty": lambda applicable, *_: 
                readable_rules["emptyRule"]("subject", applicable),
                
            "subject-full-stop": lambda applicable, value, *_: 
                readable_rules["fullStopRule"]("subject", applicable, value),
                
            "subject-max-length": lambda applicable, value, *_: 
                readable_rules["maxLengthRule"]("subject", applicable, value),
                
            "subject-min-length": lambda applicable, value, *_: 
                readable_rules["minLengthRule"]("subject", applicable, value),
                
            "type-case": lambda applicable, value, *_: 
                readable_rules["caseRule"]("type", applicable, value),
                
            "type-empty": lambda applicable, *_: 
                readable_rules["emptyRule"]("type", applicable),
                
            "type-enum": lambda applicable, value, prompt=None: 
                readable_rules["enumTypeRule"]("type", applicable, value, prompt),
                
            "type-max-length": lambda applicable, value, *_: 
                readable_rules["maxLengthRule"]("type", applicable, value),
                
            "type-min-length": lambda applicable, value, *_: 
                readable_rules["minLengthRule"]("type", applicable, value),
        }

    def get_prompt(self, rule_name: str, rule_config_tuple: Tuple, prompt: Dict[str, Any]) -> Optional[str]:
        """Get prompt for a rule."""
        severity, applicable, value = rule_config_tuple
        
        # Skip disabled rules
        if severity == 0:  # RuleConfigSeverity.Disabled
            return None

        prompt_fn = self.rules_prompts().get(rule_name)
        if prompt_fn:
            return prompt_fn(applicable, value, prompt)
        
        # Handle custom rules or missing handlers
        if not logger.disabled:
            logger.warning(f"No prompt handler for rule '{rule_name}'.")
        return f"The {rule_name} should {applicable} follow the rule with value: {value}"

    def infer_prompts_from_commitlint_config(self, commitlint_config: Dict[str, Any]) -> List[str]:
        """Infer prompts from commitlint configuration."""
        rules = commitlint_config.get("rules", {})
        prompt_config = commitlint_config.get("prompt", {})
        
        if not logger.disabled:
            logger.debug(f"Processing {len(rules)} commitlint rules")
            
        prompts = []
        for rule_name, rule_config in rules.items():
            inferred_prompt = self.get_prompt(rule_name, rule_config, prompt_config)
            if inferred_prompt:
                prompts.append(inferred_prompt)
                
        return prompts

# Initialize CommitLintConfig with the current configuration
commitlint_config = CommitLintConfig(config)


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
    if not logger.disabled:
        logger.debug(f"File names from diff: {file_names}")
    
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

        # More direct instructions for scope determination using filenames
        system_content += "The scope MUST contain the filename(s) changed for that specific commit line.\n"
        system_content += "If a commit line addresses changes in multiple files, list them comma-separated in the scope (e.g., `file1.py, file2.ts`).\n"
        system_content += "If a single file is changed, use just that filename (e.g., `main.py`).\n"

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

Single Change (Single File):
feat(auth.py): implement OAuth2 authentication flow

Add OAuth2 authentication support with Google and GitHub providers.
This improves security by using industry-standard protocols and allows users
to log in with existing accounts, reducing onboarding friction.

Multiple Distinct Changes (Multiple Files):
refactor(auth.py, user.py): simplify login logic and database schema

Streamline the authentication process and update user table structure for clarity.

feat(profile.html): add user profile editing feature

Allow users to update their display name and profile picture.

NEVER generate a commit message {'with a scope in parentheses' if omit_scope else 'without a scope in parentheses containing the relevant filename(s)'}. The scope MUST contain the filename(s) affected by the change described in that line.
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
    
    # Pattern to match file names in git diff - use word boundary to avoid capturing quotes
    pattern = r"diff --git a/(.*?) b/(.*?)(?:\s|$)"
    
    # Find all matches
    matches = re.findall(pattern, diff, re.MULTILINE)
    
    # Extract the 'b' file names (current version)
    file_names = []
    for match in matches:
        if match[1]:
            # Remove any trailing whitespace or special characters
            clean_name = match[1].strip()
            # Skip any entries that look like regex patterns (containing special chars)
            if any(c in clean_name for c in '*?()[]{}^$+\\'):
                continue
            file_names.append(clean_name)
    
    # Debug output
    if logger and not logger.disabled:
        logger.debug(f"Extracted file names: {file_names}")
    
    return file_names


def infer_prompts_from_commitlint_config(config_data: Dict[str, Any]) -> List[str]:
    """
    Infer prompts from commitlint configuration.
    
    Args:
        config_data: Commitlint configuration data
        
    Returns:
        List of prompt strings
    """
    # Use the CommitLintConfig class to process the config
    config_processor = CommitLintConfig(config)
    return config_processor.infer_prompts_from_commitlint_config(config_data)


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
    system_content += "{\n"
    system_content += f'  "localLanguage": "{local_language}",\n'
    system_content += '  "commitFix": "<Header of commit for bug fix with scope>",\n'
    system_content += '  "commitFeat": "<Header of commit for feature with scope>",\n'
    system_content += '  "commitFixOmitScope": "<Header of commit for bug fix without scope>",\n'
    system_content += '  "commitFeatOmitScope": "<Header of commit for feature without scope>",\n'
    system_content += '  "commitDescription": "<Description of commit for both the bug fix and the feature>"\n'
    system_content += "}\n\n"
    
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
