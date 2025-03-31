"""Base AI engine interface for OpenCommit."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class AiEngineConfig:
    """Configuration for AI engines."""
    api_key: str
    model: str
    max_tokens_output: int
    max_tokens_input: int
    base_url: Optional[str] = None


class AiEngine(ABC):
    """Abstract base class for AI engines."""
    
    @abstractmethod
    async def generate_commit_message(
        self, messages: List[Dict[str, Any]]
    ) -> Optional[str]:
        """Generate a commit message from the given messages."""
        pass
