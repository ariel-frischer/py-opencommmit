"""Configuration management for OpenCommit."""

import os
import json
import configparser
import logging
from enum import Enum, auto
from pathlib import Path
from typing import Dict, Optional, Any, Union, List, Callable, TypeVar, cast
from rich.console import Console

console = Console()
logger = logging.getLogger("opencommit")

T = TypeVar('T')


class ConfigKeys(str, Enum):
    """Configuration keys used by OpenCommit."""
    OCO_API_KEY = 'OCO_API_KEY'
    OCO_TOKENS_MAX_INPUT = 'OCO_TOKENS_MAX_INPUT'
    OCO_TOKENS_MAX_OUTPUT = 'OCO_TOKENS_MAX_OUTPUT'
    OCO_DESCRIPTION = 'OCO_DESCRIPTION'
    OCO_EMOJI = 'OCO_EMOJI'
    OCO_MODEL = 'OCO_MODEL'
    OCO_LANGUAGE = 'OCO_LANGUAGE'
    OCO_WHY = 'OCO_WHY'
    OCO_API_URL = 'OCO_API_URL'
    OCO_AI_PROVIDER = 'OCO_AI_PROVIDER'
    OCO_MESSAGE_TEMPLATE_PLACEHOLDER = 'OCO_MESSAGE_TEMPLATE_PLACEHOLDER'
    OCO_PROMPT_MODULE = 'OCO_PROMPT_MODULE'
    OCO_ONE_LINE_COMMIT = 'OCO_ONE_LINE_COMMIT'
    OCO_TEST_MOCK_TYPE = 'OCO_TEST_MOCK_TYPE'
    OCO_OMIT_SCOPE = 'OCO_OMIT_SCOPE'
    OCO_GITPUSH = 'OCO_GITPUSH'  # deprecated


class ConfigModes(str, Enum):
    """Configuration modes."""
    GET = 'get'
    SET = 'set'


class DefaultTokenLimits(int, Enum):
    """Default token limits."""
    DEFAULT_MAX_TOKENS_INPUT = 40960
    DEFAULT_MAX_TOKENS_OUTPUT = 4096


class AiProvider(str, Enum):
    """Supported AI providers."""
    OPENAI = 'openai'
    ANTHROPIC = 'anthropic'
    GEMINI = 'gemini'
    GROQ = 'groq'
    MISTRAL = 'mistral'
    DEEPSEEK = 'deepseek'
    AZURE = 'azure'
    OLLAMA = 'ollama'
    MLX = 'mlx'
    FLOWISE = 'flowise'
    TEST = 'test'


class PromptModule(str, Enum):
    """Supported prompt modules."""
    CONVENTIONAL_COMMIT = 'conventional-commit'
    COMMITLINT = '@commitlint'


class ModelList:
    """List of supported models for different providers."""
    OPENAI = [
        'gpt-4o-mini',
        'gpt-3.5-turbo',
        'gpt-3.5-turbo-instruct',
        'gpt-3.5-turbo-0613',
        'gpt-3.5-turbo-0301',
        'gpt-3.5-turbo-1106',
        'gpt-3.5-turbo-0125',
        'gpt-3.5-turbo-16k',
        'gpt-3.5-turbo-16k-0613',
        'gpt-3.5-turbo-16k-0301',
        'gpt-4',
        'gpt-4-0314',
        'gpt-4-0613',
        'gpt-4-1106-preview',
        'gpt-4-0125-preview',
        'gpt-4-turbo-preview',
        'gpt-4-vision-preview',
        'gpt-4-1106-vision-preview',
        'gpt-4-turbo',
        'gpt-4-turbo-2024-04-09',
        'gpt-4-32k',
        'gpt-4-32k-0314',
        'gpt-4-32k-0613',
        'gpt-4o',
        'gpt-4o-2024-05-13',
        'gpt-4o-mini-2024-07-18'
    ]

    ANTHROPIC = [
        'claude-3-5-sonnet-20240620',
        'claude-3-opus-20240229',
        'claude-3-sonnet-20240229',
        'claude-3-haiku-20240307'
    ]

    GEMINI = [
        'gemini-1.5-flash',
        'gemini-1.5-pro',
        'gemini-1.0-pro',
        'gemini-pro-vision',
        'text-embedding-004'
    ]

    GROQ = [
        'llama3-70b-8192',
        'llama3-8b-8192',
        'llama-guard-3-8b',
        'llama-3.1-8b-instant',
        'llama-3.1-70b-versatile',
        'gemma-7b-it',
        'gemma2-9b-it'
    ]

    MISTRAL = [
        'ministral-3b-2410',
        'ministral-3b-latest',
        'ministral-8b-2410',
        'ministral-8b-latest',
        'open-mistral-7b',
        'mistral-tiny',
        'mistral-tiny-2312',
        'open-mistral-nemo',
        'open-mistral-nemo-2407',
        'mistral-tiny-2407',
        'mistral-tiny-latest',
        'open-mixtral-8x7b',
        'mistral-small',
        'mistral-small-2312',
        'open-mixtral-8x22b',
        'open-mixtral-8x22b-2404',
        'mistral-small-2402',
        'mistral-small-2409',
        'mistral-small-latest',
        'mistral-medium-2312',
        'mistral-medium',
        'mistral-medium-latest',
        'mistral-large-2402',
        'mistral-large-2407',
        'mistral-large-2411',
        'mistral-large-latest',
        'pixtral-large-2411',
        'pixtral-large-latest',
        'codestral-2405',
        'codestral-latest',
        'codestral-mamba-2407',
        'open-codestral-mamba',
        'codestral-mamba-latest',
        'pixtral-12b-2409',
        'pixtral-12b',
        'pixtral-12b-latest',
        'mistral-embed',
        'mistral-moderation-2411',
        'mistral-moderation-latest'
    ]

    DEEPSEEK = ['deepseek-chat', 'deepseek-reasoner']

    @classmethod
    def get_default_model(cls, provider: Optional[str]) -> str:
        """Get the default model for a given provider."""
        if not provider:
            return cls.OPENAI[0]

        provider_lower = provider.lower()
        if provider_lower == AiProvider.OLLAMA.value or provider_lower == AiProvider.MLX.value:
            return ''
        elif provider_lower == AiProvider.ANTHROPIC.value:
            return cls.ANTHROPIC[0]
        elif provider_lower == AiProvider.GEMINI.value:
            return cls.GEMINI[0]
        elif provider_lower == AiProvider.GROQ.value:
            return cls.GROQ[0]
        elif provider_lower == AiProvider.MISTRAL.value:
            return cls.MISTRAL[0]
        elif provider_lower == AiProvider.DEEPSEEK.value:
            return cls.DEEPSEEK[0]
        else:
            return cls.OPENAI[0]

    @classmethod
    def get_all_models(cls) -> List[str]:
        """Get all supported models."""
        return (
            cls.OPENAI +
            cls.ANTHROPIC +
            cls.GEMINI +
            cls.GROQ +
            cls.MISTRAL +
            cls.DEEPSEEK
        )


# Type validator functions
def validate_config(key: str, condition: bool, validation_message: str) -> None:
    """Validate a config value."""
    if not condition:
        error_message = f"Invalid value for {key}: {validation_message}"
        console.print(f"[bold red]Error:[/bold red] {error_message}")
        raise ValueError(error_message)


# Type validation functions for different config options
def validate_api_key(value: Any, config: Dict[str, Any] = None) -> Optional[str]:
    """Validate API key."""
    if not config:
        config = {}
    
    if config.get(ConfigKeys.OCO_AI_PROVIDER) != AiProvider.OPENAI.value:
        return value
    
    validate_config(
        ConfigKeys.OCO_API_KEY,
        isinstance(value, str) and len(value) > 0,
        "Empty value is not allowed"
    )
    
    validate_config(
        ConfigKeys.OCO_API_KEY,
        bool(value),
        "You need to provide the OCO_API_KEY when OCO_AI_PROVIDER set to 'openai' (default) or 'ollama' or 'mlx' or 'azure' or 'gemini' or 'flowise' or 'anthropic' or 'deepseek'"
    )
    
    return value


def validate_boolean(key: str, value: Any) -> bool:
    """Validate boolean value."""
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        if value.lower() in ('true', 'yes', '1', 'y'):
            return True
        if value.lower() in ('false', 'no', '0', 'n'):
            return False
    
    validate_config(
        key,
        False,
        "Must be boolean: true or false"
    )
    return False  # For type checking, not reached


def validate_integer(key: str, value: Any) -> int:
    """Validate integer value."""
    try:
        int_value = int(value)
        return int_value
    except (ValueError, TypeError):
        validate_config(
            key,
            False,
            "Must be a number"
        )
        return 0  # For type checking, not reached


def validate_language(value: Any) -> str:
    """Validate language value."""
    # TODO: Import i18n module and check language availability
    # For now, just return the value
    return value


def validate_api_url(value: Any) -> str:
    """Validate API URL."""
    validate_config(
        ConfigKeys.OCO_API_URL,
        isinstance(value, str),
        f"{value} is not a valid URL. It should start with 'http://' or 'https://'"
    )
    return value


def validate_model(value: Any, config: Dict[str, Any] = None) -> str:
    """Validate model value."""
    if not value:
        if config and ConfigKeys.OCO_AI_PROVIDER in config:
            return ModelList.get_default_model(config[ConfigKeys.OCO_AI_PROVIDER])
        return ModelList.OPENAI[0]
    
    validate_config(
        ConfigKeys.OCO_MODEL,
        isinstance(value, str),
        f"{value} is not a valid model"
    )
    
    return value


def validate_message_template_placeholder(value: Any) -> str:
    """Validate message template placeholder."""
    validate_config(
        ConfigKeys.OCO_MESSAGE_TEMPLATE_PLACEHOLDER,
        isinstance(value, str) and value.startswith('$'),
        f"{value} must start with $, for example: '$msg'"
    )
    return value


def validate_prompt_module(value: Any) -> str:
    """Validate prompt module."""
    valid_modules = [PromptModule.CONVENTIONAL_COMMIT.value, PromptModule.COMMITLINT.value]
    validate_config(
        ConfigKeys.OCO_PROMPT_MODULE,
        value in valid_modules,
        f"{value} is not supported yet, use '@commitlint' or 'conventional-commit' (default)"
    )
    return value


def validate_ai_provider(value: Any) -> str:
    """Validate AI provider."""
    if not value:
        return AiProvider.OPENAI.value
    
    is_ollama = value.startswith(AiProvider.OLLAMA.value) if isinstance(value, str) else False
    
    providers = [
        AiProvider.OPENAI.value,
        AiProvider.MISTRAL.value,
        AiProvider.ANTHROPIC.value,
        AiProvider.GEMINI.value,
        AiProvider.AZURE.value,
        AiProvider.TEST.value,
        AiProvider.FLOWISE.value,
        AiProvider.GROQ.value,
        AiProvider.DEEPSEEK.value
    ]
    
    validate_config(
        ConfigKeys.OCO_AI_PROVIDER,
        value in providers or is_ollama,
        f"{value} is not supported yet, use 'ollama', 'mlx', 'anthropic', 'azure', 'gemini', 'flowise', 'mistral', 'deepseek' or 'openai' (default)"
    )
    
    return value


def validate_test_mock_type(value: Any) -> str:
    """Validate test mock type."""
    # TODO: Define test mock types
    test_mock_types = ["commit-message"]
    validate_config(
        ConfigKeys.OCO_TEST_MOCK_TYPE,
        value in test_mock_types,
        f"{value} is not a valid test mock type"
    )
    return value


# Map of config keys to validation functions
config_validators = {
    ConfigKeys.OCO_API_KEY: validate_api_key,
    ConfigKeys.OCO_DESCRIPTION: lambda v, _=None: validate_boolean(ConfigKeys.OCO_DESCRIPTION, v),
    ConfigKeys.OCO_TOKENS_MAX_INPUT: lambda v, _=None: validate_integer(ConfigKeys.OCO_TOKENS_MAX_INPUT, v),
    ConfigKeys.OCO_TOKENS_MAX_OUTPUT: lambda v, _=None: validate_integer(ConfigKeys.OCO_TOKENS_MAX_OUTPUT, v),
    ConfigKeys.OCO_EMOJI: lambda v, _=None: validate_boolean(ConfigKeys.OCO_EMOJI, v),
    ConfigKeys.OCO_OMIT_SCOPE: lambda v, _=None: validate_boolean(ConfigKeys.OCO_OMIT_SCOPE, v),
    ConfigKeys.OCO_LANGUAGE: lambda v, _=None: validate_language(v),
    ConfigKeys.OCO_API_URL: lambda v, _=None: validate_api_url(v),
    ConfigKeys.OCO_MODEL: validate_model,
    ConfigKeys.OCO_MESSAGE_TEMPLATE_PLACEHOLDER: lambda v, _=None: validate_message_template_placeholder(v),
    ConfigKeys.OCO_PROMPT_MODULE: lambda v, _=None: validate_prompt_module(v),
    ConfigKeys.OCO_GITPUSH: lambda v, _=None: validate_boolean(ConfigKeys.OCO_GITPUSH, v),
    ConfigKeys.OCO_AI_PROVIDER: lambda v, _=None: validate_ai_provider(v),
    ConfigKeys.OCO_ONE_LINE_COMMIT: lambda v, _=None: validate_boolean(ConfigKeys.OCO_ONE_LINE_COMMIT, v),
    ConfigKeys.OCO_TEST_MOCK_TYPE: lambda v, _=None: validate_test_mock_type(v),
    ConfigKeys.OCO_WHY: lambda v, _=None: validate_boolean(ConfigKeys.OCO_WHY, v),
}


# Default configuration
DEFAULT_CONFIG = {
    ConfigKeys.OCO_TOKENS_MAX_INPUT: DefaultTokenLimits.DEFAULT_MAX_TOKENS_INPUT,
    ConfigKeys.OCO_TOKENS_MAX_OUTPUT: DefaultTokenLimits.DEFAULT_MAX_TOKENS_OUTPUT,
    ConfigKeys.OCO_DESCRIPTION: False,
    ConfigKeys.OCO_EMOJI: False,
    ConfigKeys.OCO_MODEL: ModelList.get_default_model(AiProvider.OPENAI.value),
    ConfigKeys.OCO_LANGUAGE: 'en',
    ConfigKeys.OCO_MESSAGE_TEMPLATE_PLACEHOLDER: '$msg',
    ConfigKeys.OCO_PROMPT_MODULE: PromptModule.CONVENTIONAL_COMMIT,
    ConfigKeys.OCO_AI_PROVIDER: AiProvider.OPENAI,
    ConfigKeys.OCO_ONE_LINE_COMMIT: False,
    ConfigKeys.OCO_TEST_MOCK_TYPE: 'commit-message',
    ConfigKeys.OCO_WHY: False,
    ConfigKeys.OCO_OMIT_SCOPE: False,
    ConfigKeys.OCO_GITPUSH: True  # deprecated
}


def get_global_config_path() -> Path:
    """Get the path to the global config file."""
    home_dir = Path.home()
    return home_dir / '.pyoc'


def get_project_config_path() -> Optional[Path]:
    """Get the path to the project config file (.env)."""
    cwd = Path.cwd()
    project_config = cwd / '.env'
    return project_config if project_config.exists() else None


def parse_config_value(value: Any) -> Any:
    """Parse config value to appropriate type."""
    if value is None:
        return None
        
    if isinstance(value, (bool, int, float)):
        return value
        
    if not isinstance(value, str):
        return value
        
    # Handle string values
    if value.lower() == 'true':
        return True
    elif value.lower() == 'false':
        return False
    elif value.lower() in ('null', 'undefined'):
        return None
        
    # Try to parse as JSON
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        # If it's not valid JSON, return as is
        return value


def get_global_config() -> Dict[str, Any]:
    """Get the global configuration."""
    config_path = get_global_config_path()
    if not config_path.exists():
        return DEFAULT_CONFIG.copy()
    
    try:
        # First try to read as INI file with configparser
        try:
            config_file = config_path.read_text(encoding='utf-8')
            config_parser = configparser.ConfigParser()
            config_parser.read_string(config_file)
            
            # Extract values
            result = {}
            if 'DEFAULT' in config_parser:
                for key, value in config_parser['DEFAULT'].items():
                    if key.upper() in ConfigKeys.__members__:
                        result[key.upper()] = parse_config_value(value)
            
            return result
        except configparser.MissingSectionHeaderError:
            # If no section headers, read as key=value pairs like .env
            result = {}
            with open(config_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        if key.upper() in ConfigKeys.__members__:
                            result[key.upper()] = parse_config_value(value)
            
            return result
    except Exception as e:
        logger.error(f"Error reading global config: {e}")
        return DEFAULT_CONFIG.copy()


def get_project_config() -> Dict[str, Any]:
    """Get the project configuration from .env file."""
    project_config_path = get_project_config_path()
    if not project_config_path:
        return {}
    
    try:
        env_config = {}
        with open(project_config_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    if key.upper() in ConfigKeys.__members__:
                        env_config[key.upper()] = parse_config_value(value)
        
        return env_config
    except Exception as e:
        logger.error(f"Error reading project config: {e}")
        return {}


def get_env_config() -> Dict[str, Any]:
    """Get configuration from environment variables."""
    env_config = {}
    for key in ConfigKeys:
        value = os.environ.get(key.value)
        if value is not None:
            env_config[key.value] = parse_config_value(value)
    
    return env_config


def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple configs with later configs taking precedence."""
    result = {}
    for config in configs:
        for key, value in config.items():
            if value is not None:
                result[key] = value
    
    return result


def validate_configs(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate all config values."""
    validated_config = {}
    
    for key, value in config.items():
        if value is None:
            continue
            
        if key not in ConfigKeys.__members__:
            logger.warning(f"Unknown configuration key: {key}")
            continue
            
        try:
            validator = config_validators.get(key)
            if validator:
                validated_config[key] = validator(value, config)
            else:
                validated_config[key] = value
        except ValueError as e:
            logger.error(f"Validation error for {key}: {e}")
            # Use default value
            if key in DEFAULT_CONFIG:
                validated_config[key] = DEFAULT_CONFIG[key]
    
    # Ensure all default values are set
    for key, default_value in DEFAULT_CONFIG.items():
        if key not in validated_config:
            validated_config[key] = default_value
    
    return validated_config


def get_config() -> Dict[str, Any]:
    """Get the combined and validated configuration."""
    # Load configs in order of precedence: default < global < project < env
    global_config = get_global_config()
    project_config = get_project_config()
    env_config = get_env_config()
    
    # Merge configs with environment variables taking highest precedence
    merged_config = merge_configs(DEFAULT_CONFIG, global_config, project_config, env_config)
    
    # Validate the merged config
    validated_config = validate_configs(merged_config)
    
    return validated_config


def set_global_config(key: str, value: str) -> None:
    """Set a configuration value in the global config file."""
    config_path = get_global_config_path()
    
    # Check if file exists and determine its format
    use_ini_format = True
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # If file has content but no [section] headers, use key=value format
                if content.strip() and not any(line.strip().startswith('[') and line.strip().endswith(']') 
                                              for line in content.splitlines()):
                    use_ini_format = False
        except Exception as e:
            logger.error(f"Error checking config file format: {e}")
    
    if use_ini_format:
        # Use INI format with configparser
        config_parser = configparser.ConfigParser()
        if config_path.exists():
            try:
                config_parser.read(config_path)
            except Exception as e:
                logger.error(f"Error reading global config: {e}")
        
        # Ensure DEFAULT section exists
        if 'DEFAULT' not in config_parser:
            config_parser['DEFAULT'] = {}
        
        # Set the value
        config_parser['DEFAULT'][key] = value
        
        # Write config
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                config_parser.write(f)
        except Exception as e:
            logger.error(f"Error writing global config: {e}")
            console.print(f"[bold red]Error:[/bold red] Could not write to config file: {e}")
            raise
    else:
        # Use key=value format like .env
        config_lines = []
        key_exists = False
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip() and '=' in line:
                            line_key, _ = line.split('=', 1)
                            if line_key.strip() == key:
                                config_lines.append(f"{key}={value}\n")
                                key_exists = True
                            else:
                                config_lines.append(line)
                        else:
                            config_lines.append(line)
            except Exception as e:
                logger.error(f"Error reading config file: {e}")
        
        # Append key if it doesn't exist
        if not key_exists:
            config_lines.append(f"{key}={value}\n")
        
        # Write config
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                f.writelines(config_lines)
        except Exception as e:
            logger.error(f"Error writing config file: {e}")
            console.print(f"[bold red]Error:[/bold red] Could not write to config file: {e}")
            raise


def set_project_config(key: str, value: str) -> None:
    """Set a configuration value in the project .env file."""
    env_path = Path.cwd() / '.env'
    
    # Read existing .env
    env_lines = []
    key_exists = False
    
    if env_path.exists():
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip() and '=' in line:
                        line_key, _ = line.split('=', 1)
                        if line_key.strip() == key:
                            env_lines.append(f"{key}={value}\n")
                            key_exists = True
                        else:
                            env_lines.append(line)
                    else:
                        env_lines.append(line)
        except Exception as e:
            logger.error(f"Error reading .env file: {e}")
    
    # Append key if it doesn't exist
    if not key_exists:
        env_lines.append(f"{key}={value}\n")
    
    # Write .env
    try:
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(env_lines)
    except Exception as e:
        logger.error(f"Error writing .env file: {e}")
        console.print(f"[bold red]Error:[/bold red] Could not write to .env file: {e}")
        raise


def config(mode: str, key: Optional[str] = None, value: Optional[str] = None, use_project_config: bool = False) -> None:
    """Get or set configuration values."""
    if mode == ConfigModes.GET:
        if key:
            if key.upper() not in ConfigKeys.__members__:
                console.print(f"[bold red]Error:[/bold red] Unknown configuration key: {key}")
                console.print(f"Available keys: {', '.join([k.value for k in ConfigKeys])}")
                return
            
            config_value = get_config().get(key.upper())
            console.print(f"{key} = {config_value}")
        else:
            config_values = get_config()
            for k, v in config_values.items():
                console.print(f"{k} = {v}")
    
    elif mode == ConfigModes.SET:
        # Handle key=value format
        if key and '=' in key:
            key_value = key
            key, value = key_value.split('=', 1)
        
        if not key or not value:
            console.print("[bold red]Error:[/bold red] Both key and value are required for set mode")
            return
        
        key = key.upper()
        if key not in ConfigKeys.__members__:
            console.print(f"[bold red]Error:[/bold red] Unknown configuration key: {key}")
            console.print(f"Available keys: {', '.join([k.value for k in ConfigKeys])}")
            return
        
        try:
            # Validate the value before setting
            validator = config_validators.get(key)
            if validator:
                config_copy = get_config()
                validated_value = validator(value, config_copy)
            
            # Set the value in appropriate config file
            if use_project_config:
                set_project_config(key, value)
                console.print(f"[bold green]Success:[/bold green] Set {key} to {value} in project config")
            else:
                set_global_config(key, value)
                console.print(f"[bold green]Success:[/bold green] Set {key} to {value} in global config")
                
        except ValueError as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")


# Migration utilities
def get_migrations_file_path() -> Path:
    """Get the path to the migrations file."""
    home_dir = Path.home()
    return home_dir / '.pyoc_migrations'


def get_completed_migrations() -> List[str]:
    """Get the list of completed migrations."""
    migrations_file = get_migrations_file_path()
    if not migrations_file.exists():
        return []
    
    try:
        data = migrations_file.read_text(encoding='utf-8')
        return json.loads(data) if data else []
    except Exception as e:
        logger.error(f"Error reading migrations file: {e}")
        return []


def save_completed_migration(migration_name: str) -> None:
    """Save a completed migration."""
    migrations_file = get_migrations_file_path()
    completed_migrations = get_completed_migrations()
    
    if migration_name not in completed_migrations:
        completed_migrations.append(migration_name)
        
        try:
            migrations_file.write_text(
                json.dumps(completed_migrations, indent=2),
                encoding='utf-8'
            )
        except Exception as e:
            logger.error(f"Error writing migrations file: {e}")


class Migration:
    """Base class for migrations."""
    name: str
    
    def run(self) -> None:
        """Run the migration."""
        raise NotImplementedError("Subclasses must implement run()")


class MigrationRunner:
    """Runner for migrations."""
    
    @staticmethod
    def run_migrations(migrations: List[Migration]) -> None:
        """Run all pending migrations."""
        # Skip migrations if no config file exists (new installation)
        global_config_path = get_global_config_path()
        if not global_config_path.exists():
            return
        
        # Skip migrations in test mode
        config = get_config()
        if config.get(ConfigKeys.OCO_AI_PROVIDER) == AiProvider.TEST.value:
            return
        
        completed_migrations = get_completed_migrations()
        has_migrations_run = False
        
        for migration in migrations:
            if migration.name not in completed_migrations:
                try:
                    console.print(f"Applying migration: {migration.name}")
                    migration.run()
                    console.print(f"Migration applied successfully: {migration.name}")
                    save_completed_migration(migration.name)
                    has_migrations_run = True
                except Exception as e:
                    console.print(f"[bold red]Failed to apply migration {migration.name}:[/bold red] {str(e)}")
                    return
        
        if has_migrations_run:
            console.print("[bold green]✔[/bold green] Migrations to your config were applied successfully.")


# CLI Command implementations
def get_command(key: Optional[str] = None) -> None:
    """Get configuration command."""
    config(ConfigModes.GET, key)


def set_command(key_value: str, project: bool = False) -> None:
    """Set configuration command."""
    if '=' not in key_value:
        console.print("[bold red]Error:[/bold red] Key-value must be in format KEY=VALUE")
        return
    
    key, value = key_value.split('=', 1)
    config(ConfigModes.SET, key, value, project)
