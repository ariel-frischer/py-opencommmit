# OpenCommit Python CLI

OpenCommit is an AI-powered git commit message generator. This Python implementation provides the same functionality as the original Node.js CLI tool with a clean, Pythonic interface.

## Table of Contents

- [Installation](#installation)
  - [Using pipx (Recommended)](#using-pipx-recommended)
  - [Using pip](#using-pip)
  - [Using UV](#using-uv)
  - [From Source](#from-source)
- [Usage](#usage)
  - [Generate Commit Messages](#generate-commit-messages)
  - [Configure OpenCommit](#configure-opencommit)
  - [Setup Git Hooks](#setup-git-hooks)
  - [Using the Python Module Directly](#using-the-python-module-directly)
- [Configuration](#configuration)
  - [Available Options](#available-options)
  - [Configuration File](#configuration-file)
  - [Environment Variables](#environment-variables)
- [Differences from Node.js Version](#differences-from-nodejs-version)
- [Troubleshooting](#troubleshooting)

## Installation

### Using pipx (Recommended)

[pipx](https://pypa.github.io/pipx/) is the recommended installation method for CLI tools as it installs the package in an isolated environment but makes it available globally.

```bash
pipx install opencommit
```

### Using pip

You can install OpenCommit using pip:

```bash
pip install opencommit
```

### Using UV

[UV](https://github.com/astral-sh/uv) is a fast Python package installer and resolver.

```bash
uv install opencommit
```

### From Source

```bash
git clone https://github.com/di-sukharev/opencommit.git
cd opencommit
uv venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv install -e .
```

## Usage

Once installed, OpenCommit CLI can be accessed with the `oco` command.

### Generate Commit Messages

Generate an AI-powered commit message from your staged changes:

```bash
# Generate commit message from staged changes
oco commit

# Generate commit message and automatically stage all changes
oco commit --stage-all

# Generate commit message with additional context
oco commit --context "This commit fixes the bug in the login form"

# Skip confirmation prompt
oco commit --skip-confirmation

# Pass additional arguments to git commit
oco commit -- -m "Custom message" --no-verify
```

#### Example Workflow

```
$ git add src/feature.py
$ oco commit
✨ Analyzing your changes...
📝 Generated commit message:
   feat: implement user authentication in login form

? Use this commit message? [Y/n] y
🎉 Commit successful!
```

### Configure OpenCommit

Configure the CLI settings:

```bash
# Show current configuration
oco config

# Set OpenAI API key
oco config --set api_key=sk-your-api-key

# Set preferred language
oco config --set language=en

# Set model
oco config --set model=gpt-3.5-turbo
```

### Setup Git Hooks

Set up git hooks for automatic commit message generation:

```bash
# Install git hooks in the current repository
oco githook --install

# Uninstall git hooks
oco githook --uninstall

# Show current hook status
oco githook --status
```

### Using the Python Module Directly

You can also run OpenCommit directly as a Python module without installing it globally. This is useful for:

- Using the tool without installing it globally
- Development and testing
- Running from source code

```bash
# Generate commit message from staged changes
python -m src.python.cli commit

# Generate commit message and automatically stage all changes
python -m src.python.cli commit --stage-all

# Generate commit message with additional context
python -m src.python.cli commit --context "This commit fixes the bug in the login form"

# Configure OpenCommit
python -m src.python.cli config --set api_key=sk-your-api-key

# Install git hooks
python -m src.python.cli githook --install
```

#### Example Workflow Using Python Module

```
$ git add src/feature.py
$ python -m src.python.cli commit
✨ Analyzing your changes...
📝 Generated commit message:
   feat: implement user authentication in login form

? Use this commit message? [Y/n] y
🎉 Commit successful!
```

## Configuration

OpenCommit can be configured through the CLI, a configuration file, or environment variables.

### Available Options

| Option | Description | Default |
|--------|-------------|---------|
| `api_key` | The API key for the LLM provider (e.g., OpenAI) | None |
| `model` | The LLM model to use | gpt-3.5-turbo |
| `language` | The language for commit messages | en |
| `message_template` | Template for commit messages | None |
| `emoji` | Whether to include emoji in commit messages | true |
| `prompt_template` | Custom prompt template for the AI | Default template |

### Configuration File

The configuration file is located at:
- Linux/macOS: `~/.config/opencommit/config`
- Windows: `%USERPROFILE%\.config\opencommit\config`

Example configuration file:

```ini
[opencommit]
api_key = sk-your-api-key
model = gpt-3.5-turbo
language = en
emoji = true
```

### Environment Variables

You can also use environment variables to configure OpenCommit:

```bash
# Set API key
export OCO_API_KEY=sk-your-api-key

# Set model
export OCO_MODEL=gpt-3.5-turbo

# Set language
export OCO_LANGUAGE=en
```

## LiteLLM Integration

OpenCommit Python CLI uses [LiteLLM](https://github.com/BerriAI/litellm) for interfacing with AI providers:

```
┌─────────────┐     ┌───────────┐     ┌─────────────┐
│ OpenCommit  │────▶│  LiteLLM  │────▶│  OpenAI API │
└─────────────┘     └───────────┘     └─────────────┘
```

Benefits of using LiteLLM:
- Unified interface to multiple LLM providers
- Error handling and retries
- Token counting and cost tracking
- Potential for future provider expansion

## Differences from Node.js Version

The Python CLI implementation aims to provide the same functionality as the Node.js version with some differences:

1. **LLM Provider Support**: Initially, only OpenAI is supported (via LiteLLM)
2. **Configuration Structure**: Uses INI format instead of JSON
3. **Command Structure**: Uses Click instead of Commander.js
4. **Package Management**: Uses UV instead of npm
5. **Performance**: May have different performance characteristics

## Troubleshooting

### Common Issues

#### API Key Issues

```
Error: Invalid API key
```

Solution: Set your API key using:
```bash
oco config --set api_key=sk-your-api-key
```

Or set it as an environment variable:
```bash
export OCO_API_KEY=sk-your-api-key
```

#### Git Repository Issues

```
Error: Not a git repository
```

Solution: Make sure you're in a valid git repository. Run:
```bash
git init
```

#### No Staged Changes

```
Error: No staged changes to commit
```

Solution: Stage your changes before generating a commit message:
```bash
git add <files>
```

Or use the `--stage-all` option:
```bash
oco commit --stage-all
```

#### Large Diffs

```
Error: Diff too large for token limit
```

Solution: Commit changes in smaller batches or use a model with a larger context window:
```bash
oco config --set model=gpt-4-turbo
```

#### Configuration Errors

```
Error: Cannot read configuration file
```

Solution: Reinitialize the configuration:
```bash
oco config --init
```

### Debugging

For advanced debugging, set the debug environment variable:

```bash
OCO_DEBUG=1 oco commit
```

This will provide verbose output to help troubleshoot issues.

### Getting Help

If you encounter issues not covered here, please:

1. Check the [GitHub issues](https://github.com/di-sukharev/opencommit/issues)
2. Run commands with verbose logging as shown above
3. Report issues on GitHub with the full debug output