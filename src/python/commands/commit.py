
# ... (rest of the code remains the same)

def get_staged_files() -> List[str]:
    """Get a list of staged files with smart filtering."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True,
        )
        all_staged_files = [f for f in result.stdout.strip().split("\n") if f]
        
        # Implement smart filtering
        filtered_files = [
            f for f in all_staged_files 
            if not f.endswith(('.lock', '.lockb'))  # Ignore lock files
            and not f.startswith(('node_modules/', 'dist/', 'build/'))  # Ignore common build directories
            and os.path.getsize(f) < 1024 * 1024  # Ignore files larger than 1MB
        ]
        
        return filtered_files
        
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to get staged files: {e}")
