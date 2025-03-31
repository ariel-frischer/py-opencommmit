"""Token counting utilities for OpenCommit."""

import tiktoken


def token_count(content: str) -> int:
    """Count the number of tokens in the given content."""
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(content)
    return len(tokens)
