"""Tests for the AI engine implementations."""

import pytest
import os
from unittest.mock import patch, MagicMock, AsyncMock
from typing import List, Dict, Any, Optional

from py_opencommit.engine.base import AiEngine, AiEngineConfig
from py_opencommit.engine.openai import OpenAiEngine


class TestAiEngineConfig:
    """Tests for the AiEngineConfig class."""
    
    def test_config_initialization(self):
        """Test initializing the AiEngineConfig."""
        config = AiEngineConfig(
            api_key="test-api-key",
            model="gpt-3.5-turbo",
            max_tokens_output=500,
            max_tokens_input=4000
        )
        
        assert config.api_key == "test-api-key"
        assert config.model == "gpt-3.5-turbo"
        assert config.max_tokens_output == 500
        assert config.max_tokens_input == 4000
        assert config.base_url is None
    
    def test_config_with_base_url(self):
        """Test initializing the AiEngineConfig with a base URL."""
        config = AiEngineConfig(
            api_key="test-api-key",
            model="gpt-3.5-turbo",
            max_tokens_output=500,
            max_tokens_input=4000,
            base_url="https://api.example.com/v1"
        )
        
        assert config.api_key == "test-api-key"
        assert config.model == "gpt-3.5-turbo"
        assert config.max_tokens_output == 500
        assert config.max_tokens_input == 4000
        assert config.base_url == "https://api.example.com/v1"


class TestOpenAiEngine:
    """Tests for the OpenAiEngine class."""
    
    def test_initialization(self):
        """Test initializing the OpenAiEngine."""
        with patch('py_opencommit.engine.openai.AsyncOpenAI') as mock_openai:
            config = AiEngineConfig(
                api_key="test-api-key",
                model="gpt-3.5-turbo",
                max_tokens_output=500,
                max_tokens_input=4000
            )
            
            engine = OpenAiEngine(config)
            
            assert engine.config == config
            mock_openai.assert_called_once_with(api_key="test-api-key")
    
    def test_initialization_with_base_url(self):
        """Test initializing the OpenAiEngine with a base URL."""
        with patch('py_opencommit.engine.openai.AsyncOpenAI') as mock_openai:
            config = AiEngineConfig(
                api_key="test-api-key",
                model="gpt-3.5-turbo",
                max_tokens_output=500,
                max_tokens_input=4000,
                base_url="https://api.example.com/v1"
            )
            
            engine = OpenAiEngine(config)
            
            assert engine.config == config
            mock_openai.assert_called_once_with(
                api_key="test-api-key",
                base_url="https://api.example.com/v1"
            )
    
    def test_generate_commit_message_success(self):
        """Test generating a commit message successfully."""
        with patch('py_opencommit.engine.openai.AsyncOpenAI') as mock_openai_class:
            # Create a mock for the AsyncOpenAI instance
            mock_openai = MagicMock()
            mock_openai_class.return_value = mock_openai
            
            # Create a mock for the chat completions create method
            mock_chat = MagicMock()
            mock_openai.chat = mock_chat
            
            # Create a mock for the completions object
            mock_completions = MagicMock()
            mock_chat.completions = mock_completions
            
            # Set up the response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "feat: add new feature"
            
            # Mock the async method with a synchronous one for testing
            async def mock_create(*args, **kwargs):
                return mock_response
                
            mock_completions.create = mock_create
            
            # Create the engine
            config = AiEngineConfig(
                api_key="test-api-key",
                model="gpt-3.5-turbo",
                max_tokens_output=500,
                max_tokens_input=4000
            )
            engine = OpenAiEngine(config)
            
            # Test messages
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Generate a commit message for these changes."}
            ]
            
            # Use pytest's event loop to run the coroutine
            import asyncio
            result = asyncio.run(engine.generate_commit_message(messages))
            
            # Verify the result
            assert result == "feat: add new feature"
    
    def test_generate_commit_message_error(self):
        """Test error handling when generating a commit message."""
        with patch('py_opencommit.engine.openai.AsyncOpenAI') as mock_openai_class, \
             patch('builtins.print') as mock_print:
            # Create a mock for the AsyncOpenAI instance
            mock_openai = MagicMock()
            mock_openai_class.return_value = mock_openai
            
            # Create a mock for the chat completions create method
            mock_chat = MagicMock()
            mock_openai.chat = mock_chat
            
            # Create a mock for the completions object
            mock_completions = MagicMock()
            mock_chat.completions = mock_completions
            
            # Set up the error
            async def mock_create_error(*args, **kwargs):
                raise Exception("API error")
                
            mock_completions.create = mock_create_error
            
            # Create the engine
            config = AiEngineConfig(
                api_key="test-api-key",
                model="gpt-3.5-turbo",
                max_tokens_output=500,
                max_tokens_input=4000
            )
            engine = OpenAiEngine(config)
            
            # Test messages
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Generate a commit message for these changes."}
            ]
            
            # Use pytest's event loop to run the coroutine
            import asyncio
            result = asyncio.run(engine.generate_commit_message(messages))
            
            # Verify the result
            assert result is None
            
            # Verify the error was printed
            mock_print.assert_called_once()
            assert "Error generating commit message" in mock_print.call_args[0][0]