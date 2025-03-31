
import click
import litellm
import subprocess
from typing import List, Optional

def get_git_remotes() -> List[str]:
    result = subprocess.run(['git', 'remote'], capture_output=True, text=True)
    return [remote for remote in result.stdout.split('\n') if remote.strip()]

def check_message_template(extra_args: List[str], placeholder: str) -> Optional[str]:
    for arg in extra_args:
        if placeholder in arg:
            return arg
    return None

def generate_commit_message(diff: str, context: str = '') -> str:
    try:
        response = litellm.completion(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "system",
                "content": "Generate a commit message based on the following diff:\n" + diff
            }]
        )
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"Failed to generate commit message: {str(e)}")

@click.command()
@click.argument('extra_args', nargs=-1)
@click.option('--context', default='', help='Additional context for commit message')
@click.option('--stage-all', is_flag=True, help='Stage all changes before committing')
@click.option('--skip-confirm', is_flag=True, help='Skip commit confirmation')
def commit(extra_args: List[str], context: str, stage_all: bool, skip_confirm: bool) -> None:
    """Generate and commit changes using LiteLLM"""
    
    # Stage files if requested
    if stage_all:
        subprocess.run(['git', 'add', '.'])

    # Get staged files
    result = subprocess.run(['git', 'diff', '--cached', '--name-only'], capture_output=True, text=True)
    staged_files = [f.strip() for f in result.stdout.split('\n') if f.strip()]
    
    if not staged_files:
        click.echo('No staged changes to commit', err=True)
        return

    # Get diff
    diff_result = subprocess.run(['git', 'diff', '--cached'], capture_output=True, text=True)
    diff = diff_result.stdout

    # Generate commit message
    try:
        commit_message = generate_commit_message(diff, context)
        click.echo(f'Generated commit message:\n{commit_message}')
        
        if not skip_confirm:
            if not click.confirm('Commit with this message?'):
                click.echo('Commit cancelled')
                return

        # Perform commit
        commit_cmd = ['git', 'commit', '-m', commit_message, *extra_args]
        subprocess.run(commit_cmd)

        # Push if configured
        remotes = get_git_remotes()
        if remotes:
            if len(remotes) == 1:
                if click.confirm(f'Push to {remotes[0]}?'):
                    subprocess.run(['git', 'push', remotes[0]])
            else:
                remote = click.prompt('Select remote to push to', type=click.Choice(remotes))
                if remote:
                    subprocess.run(['git', 'push', remote])
                    
    except Exception as e:
        click.echo(f'Error: {str(e)}', err=True)
        return

if __name__ == '__main__':
    commit()
