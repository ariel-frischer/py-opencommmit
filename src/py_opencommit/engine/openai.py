"""OpenAI engine implementation for OpenCommit."""

import os
from typing import List, Dict, Any, Optional
import openai
from openai import AsyncOpenAI

from py_opencommit.engine.base import AiEngine, AiEngineConfig


class OpenAiEngine(AiEngine):
    """OpenAI engine implementation."""
    
    def __init__(self, config: AiEngineConfig):
        """Initialize the OpenAI engine."""
        self.config = config
        
        if not config.base_url:
            self.client = AsyncOpenAI(api_key=config.api_key)
        else:
            self.client = AsyncOpenAI(api_key=config.api_key, base_url=config.base_url)
    
    async def generate_commit_message(
        self, messages: List[Dict[str, Any]]
    ) -> Optional[str]:
        """Generate a commit message using the OpenAI API."""
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                max_tokens=self.config.max_tokens_output
            )
            return response.choices[0].message.content
        except Exception as error:
            print(f"Error generating commit message: {error}")
            return None
