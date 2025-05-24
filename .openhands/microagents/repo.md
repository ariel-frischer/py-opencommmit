# PyOpenCommit Microagents Documentation

This document provides comprehensive information about the PyOpenCommit repository for OpenHands microagents, including setup instructions, usage guidelines, repository structure, and implementation details.

## Repository Overview

PyOpenCommit (PyOC) is a Python port of the OpenCommit tool, designed to generate AI-powered git commit messages. It provides similar functionality to the original Node.js implementation but with a clean, Pythonic interface. The repository is currently in a beta/experimental stage.

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Git (installed and configured)
- OpenAI API key or compatible LLM API key

### Installation Methods

#### Using pipx (Recommended)

```bash
pipx install py-opencommit
```

#### Using pip

```bash
pip install py-opencommit
```

#### Using UV

```bash
uv pip install py-opencommit
```

#### From Source

```bash
git clone https://github.com/ariel-frischer/py-opencommmit.git
cd py-opencommmit
pip install -e .
```

### Configuration

After installation, configure PyOC with your API key:

```bash
pyoc config set OPENAI_API_KEY=your_api_key_here
```

## Usage Guidelines

### Basic Usage

Generate a commit message based on staged changes:

```bash
pyoc
```

Generate a commit message and automatically commit:

```bash
pyoc -a
```

### Advanced Usage

Generate a commit message with a specific message type:

```bash
pyoc --type feat
```

Available types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert

Generate a commit message in a specific language:

```bash
pyoc --locale es
```

### Microagent Integration

When integrating with OpenHands microagents:

1. Import the PyOC module in your agent code:
   ```python
   from py_opencommit import generate_commit_message
   ```

2. Generate commit messages programmatically:
   ```python
   message = generate_commit_message(diff_text, config)
   ```

3. Use the generated message in your git operations:
   ```python
   import subprocess
   subprocess.run(["git", "commit", "-m", message])
   ```

## Repository Structure

```
py-opencommmit/
├── .github/                # GitHub workflows and CI configuration
├── .openhands/             # OpenHands microagent configuration
│   └── microagents/        # Microagent documentation and configs
├── docs/                   # Documentation files
├── src/                    # Source code
│   ├── py_opencommit/      # Main Python package
│   │   ├── __init__.py     # Package initialization
│   │   ├── cli.py          # Command-line interface
│   │   ├── commands/       # Command implementations
│   │   ├── config.py       # Configuration handling
│   │   ├── engine/         # Core message generation engine
│   │   ├── i18n/           # Internationalization
│   │   ├── migrations/     # Configuration migrations
│   │   ├── modules/        # Functional modules
│   │   └── utils/          # Utility functions
│   └── ...                 # TypeScript source (original port)
├── tests/                  # Test suite
├── pyproject.toml          # Python project configuration
└── README.md               # Project documentation
```

## Implementation Details

### Core Components

1. **CLI Module**: Handles command-line arguments and user interaction.
2. **Engine**: Core logic for generating commit messages using AI.
3. **Git Integration**: Utilities for interacting with git repositories.
4. **Configuration Management**: Handles user preferences and API keys.

### Workflow

1. The tool extracts the git diff from staged changes.
2. The diff is processed and formatted for the AI prompt.
3. The formatted prompt is sent to the configured LLM (OpenAI by default).
4. The response is parsed and formatted according to conventional commit standards.
5. The formatted commit message is returned to the user or used directly for committing.

### API Integration

PyOC supports multiple LLM providers:

- OpenAI (default)
- Azure OpenAI
- Anthropic
- Custom API endpoints

### Microagent Implementation

When implementing a microagent that uses PyOC:

1. **Authentication**: Handle API key management securely.
2. **Error Handling**: Implement robust error handling for API failures.
3. **Customization**: Allow customization of prompts and output formats.
4. **Caching**: Consider implementing caching to reduce API calls.

### Example Microagent Code

```python
from py_opencommit.engine import generate_message
from py_opencommit.utils.git import get_staged_diff

class CommitMessageAgent:
    def __init__(self, api_key=None, config=None):
        self.config = config or {}
        if api_key:
            self.config["OPENAI_API_KEY"] = api_key
            
    async def generate_commit_message(self, repo_path="."):
        # Get the git diff
        diff = get_staged_diff(repo_path)
        if not diff:
            return "No staged changes found"
            
        # Generate the commit message
        try:
            message = await generate_message(diff, self.config)
            return message
        except Exception as e:
            return f"Error generating commit message: {str(e)}"
```

## Best Practices

1. **API Key Security**: Never hardcode API keys; use environment variables or secure storage.
2. **Error Handling**: Implement robust error handling for network issues and API rate limits.
3. **User Feedback**: Provide clear feedback during the commit message generation process.
4. **Customization**: Allow users to customize prompts and output formats.
5. **Testing**: Thoroughly test with various types of git diffs to ensure quality output.

## Troubleshooting

### Common Issues

1. **API Key Issues**: Ensure your API key is correctly configured.
2. **No Staged Changes**: Make sure you have staged changes before generating a commit message.
3. **Network Problems**: Check your internet connection if API calls fail.
4. **Rate Limiting**: Handle API rate limits gracefully with exponential backoff.

### Debugging

Enable debug mode for verbose logging:

```bash
pyoc --debug
```

## Contributing to Microagents

When developing new microagents that integrate with PyOC:

1. Follow the repository's code style and conventions.
2. Add comprehensive tests for your microagent functionality.
3. Document your microagent's usage and configuration options.
4. Consider performance implications, especially for large repositories.

## Resources

- [PyOpenCommit GitHub Repository](https://github.com/ariel-frischer/py-opencommmit)
- [Original OpenCommit Repository](https://github.com/di-sukharev/opencommit)
- [Conventional Commits Specification](https://www.conventionalcommits.org/)