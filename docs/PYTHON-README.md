## Using PyOC as a Library

You can also use PyOC's commit generation logic directly within your Python scripts or applications.

**Importing the `commit` function:**

```python
# Assuming your project structure allows importing from py_opencommit
# You might need to adjust the import based on how py_opencommit is installed
# or added to your PYTHONPATH.
# If installed via pip:
from py_opencommit.commands.commit import commit as pyoc_commit
from py_opencommit.utils.git import is_git_repository, has_staged_changes, stage_files, stage_all_changes
```

**Example Usage:**

```python
import sys
import os

# Ensure the script is run from the root of a Git repository for simplicity
# or handle paths appropriately.

# Example function to generate and commit
def generate_and_commit():
    # Ensure you are in a git repository
    if not is_git_repository():
        print("Error: Not inside a git repository.")
        sys.exit(1)

    # Check for staged changes (or use stage_all=True)
    if not has_staged_changes():
        print("Warning: No changes staged for commit.")
        # Example: Stage all changes if none are staged
        print("Staging all changes...")
        try:
            stage_all_changes()
            if not has_staged_changes():
                 print("No changes found to stage. Exiting.")
                 sys.exit(0)
        except Exception as e:
            print(f"Error staging changes: {e}")
            sys.exit(1)

    try:
        # Call the commit function programmatically
        # Note: stage_all and skip_confirm are typically False when called as a library,
        # unless you specifically want to replicate the CLI behavior.
        # extra_args are passed directly to 'git commit'
        # The function expects string representations for boolean flags from CLI context,
        # but direct boolean values might work depending on internal handling.
        # Let's use booleans directly for clarity when calling as a library.
        pyoc_commit(
            extra_args=[],          # e.g., ['--no-verify']
            context="Generated via script", # Optional context for the AI
            stage_all=False,        # Already handled staging above
            skip_confirm=True       # Set to False to require interactive confirmation (might block script)
        )
        print("Commit generated and executed successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Example: Create a dummy file and stage it if running this script directly
    # In a real scenario, you'd have actual changes.
    if not os.path.exists("dummy_change.txt"):
        with open("dummy_change.txt", "w") as f:
            f.write("This is a dummy change.\n")
        try:
            print("Staging dummy_change.txt...")
            stage_files(["dummy_change.txt"])
        except Exception as e:
            print(f"Error staging dummy file: {e}")
            sys.exit(1)

    generate_and_commit()

    # Clean up dummy file
    if os.path.exists("dummy_change.txt"):
        os.remove("dummy_change.txt")
        print("Cleaned up dummy file.")

```

**Important Considerations:**

*   **Installation:** The Python environment running your script must have `py-opencommit` installed (e.g., via `pip install py-opencommit` or `pip install -e .` if running from source).
*   **Environment:** Ensure the script is run within a Git repository. The utility functions rely on `git` commands.
*   **Staging:** The `commit` function expects changes to be staged *before* it's called, unless you set `stage_all=True`. You can use utility functions like `stage_files` or `stage_all_changes` from `py_opencommit.utils.git` if needed.
*   **Configuration:** The function relies on the same configuration mechanisms as the CLI (environment variables, `.env` file, global `~/.pyoc` file). Ensure your API key and other settings are accessible to the environment running the script.
*   **Error Handling:** Wrap the call in a `try...except` block to handle potential errors during diff generation, AI communication, or the final `git commit` execution.
*   **Interactivity:** Setting `skip_confirm=False` will trigger interactive prompts (like asking for confirmation), which might not be suitable for non-interactive scripts. The `commit` function might need adjustments to handle programmatic confirmation if `skip_confirm=False` is desired in a library context.
*   **Function Signature:** The `commit` function in `commands/commit.py` is decorated with `@click.command`. When calling it programmatically, you pass arguments directly, not through Click's context. Be mindful of the expected types (e.g., `extra_args` should be a list, `context` a string, `stage_all` and `skip_confirm` likely booleans when called directly, though the CLI passes strings).
