# Python CLI Migration Plan

## Smart File Filtering Feature

The new Python CLI includes a smart file filtering system to improve LLM token efficiency and performance when generating commit messages. Key implementation details:

1. **Default Patterns**: A comprehensive set of default patterns to exclude common binary, generated, and lock files
2. **Size Thresholds**: Files larger than 1MB are automatically filtered from LLM processing
3. **Custom Ignore Support**: Support for user-defined `.opencommitignore` files in the repository root
4. **Seamless Integration**: Files are filtered from LLM processing but still included in the actual git commit

### Implementation Notes

- Implemented in `src/python/utils/git.py` using standard Python libraries
- Uses `fnmatch` for glob pattern matching and handling directory wildcards
- Tests in `tests/python/test_file_filtering.py` cover pattern matching, ignore file parsing, and file filtering logic
- Documentation added to README.md with usage examples and explanations

Your job is to create a mirror python repository in src/python that does most things this repository does.
Do not remove any original js or ts files. For now we will just be editing python code in src/python/ directory.
We have some work already converted but not all lets make sure the basics are working first.
We have some basics set up but will need to convert each js or ts file into python one by one.
Ask the expert frequently for any difficult issues or high level planning.
We do not need to support any github action logic. We only need to support openai provider for now.
Once you are done with most of the work create a new PYTHON-README.md with usage instructions for running the python version.

## CLI Structure
- Replace Node.js shebang with Python shebang
- Mirror existing CLI command structure
- Use Click or Typer for CLI framework

## LiteLLM Integration
- Centralize LLM API calls via LiteLLM Proxy
- Configure via environment variables
- Disable unnecessary logging for production

## UV Usage
- Use UV for dependency management
- Integrate with pyproject.toml
- Ensure compatibility with pip and pip-tools

## Tooling Recommendations
- Use Pipx for system-wide installation
- Implement automated testing with pytest
- Add type checking with mypy
- Include linting via ruff

## Package Conversion Reference

### DevDependencies

| Node.js Package                  | Python Equivalent                          | Description                                                                 |
|----------------------------------|--------------------------------------------|-----------------------------------------------------------------------------|
| `@commitlint/types`              | Not directly applicable                    | Commit linting is less common in Python; you may skip this.                |
| `@types/ini`                     | `configparser`                             | For working with `.ini` configuration files.                               |
| `@types/inquirer`                | `InquirerPy`                               | For interactive CLI prompts in Python.                                     |
| `@types/jest`                    | `pytest`                                   | Popular testing framework for Python.                                      |
| `@types/node`                    | Not applicable                             | Node.js-specific types are unnecessary in Python.                          |
| `@typescript-eslint/eslint-plugin` | `flake8`, `pylint`, or `black`            | For linting and formatting Python code.                                    |
| `@typescript-eslint/parser`      | Not applicable                             | TypeScript-specific; unnecessary for Python.                               |
| `cli-testing-library`            | `pytest-console-scripts`                   | For testing CLI applications in Python.                                    |
| `dotenv`                         | `python-dotenv`                            | For loading environment variables from `.env` files.                       |
| `esbuild`                        | Not directly applicable                    | Use native Python packaging tools like `setuptools`.                       |
| `eslint`                         | `flake8`, `pylint`, or `black`             | For linting and formatting Python code.                                    |
| `jest`                           | `pytest`                                   | For testing in Python.                                                     |
| `prettier`                       | `black`, or `autopep8`                     | Code formatting tools for Python.                                          |
| `ts-jest`, `ts-node`, and `typescript` | Not applicable                        | TypeScript-specific tools are unnecessary for Python.                      |

### Dependencies

| Node.js Package                  | Python Equivalent                          | Description                                                                 |
|----------------------------------|--------------------------------------------|-----------------------------------------------------------------------------|
| `@actions/core`, `@actions/exec`, and others related to GitHub Actions  | Use GitHub Actions YAML configuration directly or libraries like PyGitHub  | For interacting with GitHub Actions workflows.                             |
| `@anthropic-ai/sdk`, and other AI SDKs like OpenAI, Azure, etc.          | Libraries like Anthropic's SDK, OpenAI's SDK (`openai`)                     | For interacting with AI APIs (e.g., ChatGPT).                              |
| `axios`                          | `requests`, or modern async alternatives like `httpx`                        | For making HTTP requests in Python.                                        |
| `chalk`                          | `rich`, or `colorama`                     | For colored terminal output in Python.                                     |
| `crypto`                         | Built-in Python module: `hashlib`, or libraries like PyCryptodome            | For cryptographic operations in Python.                                    |
| `execa`                          | Built-in module: `subprocess`, or libraries like Plumbum                     | For executing shell commands in Python.                                    |
| `ignore`                         | Built-in module: Use `.gitignore-parser`.                                     |
| `ini`                            | Built-in module: Use the standard library's configparser.                 |
| `inquirer`                       | Use the library InquirerPy.                                                |
| OpenAI-related libraries         | Use the official OpenAI library (`openai`).                                   |
