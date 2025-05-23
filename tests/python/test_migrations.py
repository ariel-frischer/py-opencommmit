"""Tests for the migrations module."""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from py_opencommit.migrations.migrate_00_initialize_config import Migration00InitializeConfig
from py_opencommit.commands.config import DEFAULT_CONFIG


class TestMigration00InitializeConfig:
    """Tests for the Migration00InitializeConfig class."""
    
    def test_migration_name(self):
        """Test the migration name."""
        migration = Migration00InitializeConfig()
        assert migration.name == "00_initialize_config"
    
    def test_run_create_new_config(self):
        """Test running the migration when the config file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.ini"
            
            # Mock the config path
            with patch('py_opencommit.migrations.migrate_00_initialize_config.get_global_config_path', 
                       return_value=config_path):
                
                # Run the migration
                migration = Migration00InitializeConfig()
                migration.run()
                
                # Verify the config file was created
                assert config_path.exists()
                
                # Verify the content
                import configparser
                config = configparser.ConfigParser()
                config.read(config_path)
                
                # Check that all default values are present
                for key, value in DEFAULT_CONFIG.items():
                    assert config['DEFAULT'][key.value] == str(value)
    
    def test_run_with_empty_config(self):
        """Test running the migration when the config file exists but is empty."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.ini"
            
            # Create an empty config file
            with open(config_path, 'w') as f:
                f.write("[DEFAULT]\n")
            
            # Mock the config path
            with patch('py_opencommit.migrations.migrate_00_initialize_config.get_global_config_path', 
                       return_value=config_path):
                
                # Run the migration
                migration = Migration00InitializeConfig()
                migration.run()
                
                # Verify the config file was updated
                import configparser
                config = configparser.ConfigParser()
                config.read(config_path)
                
                # Check that all default values are present
                for key, value in DEFAULT_CONFIG.items():
                    assert config['DEFAULT'][key.value] == str(value)
    
    def test_run_with_invalid_config(self):
        """Test running the migration when the config file exists but is invalid."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.ini"
            
            # Create an invalid config file
            with open(config_path, 'w') as f:
                f.write("This is not a valid INI file")
            
            # Mock the config path
            with patch('py_opencommit.migrations.migrate_00_initialize_config.get_global_config_path', 
                       return_value=config_path):
                
                # Run the migration
                migration = Migration00InitializeConfig()
                migration.run()
                
                # Verify the config file was recreated
                import configparser
                config = configparser.ConfigParser()
                config.read(config_path)
                
                # Check that all default values are present
                for key, value in DEFAULT_CONFIG.items():
                    assert config['DEFAULT'][key.value] == str(value)
    
    def test_run_with_valid_config(self):
        """Test running the migration when the config file exists and is valid."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.ini"
            
            # Create a valid config file with custom values
            import configparser
            config = configparser.ConfigParser()
            config['DEFAULT'] = {}
            config['DEFAULT']['OCO_API_KEY'] = 'custom-api-key'
            config['DEFAULT']['OCO_MODEL'] = 'custom-model'
            
            with open(config_path, 'w') as f:
                config.write(f)
            
            # Mock the config path
            with patch('py_opencommit.migrations.migrate_00_initialize_config.get_global_config_path', 
                       return_value=config_path):
                
                # Run the migration
                migration = Migration00InitializeConfig()
                migration.run()
                
                # Verify the config file was not changed
                config = configparser.ConfigParser()
                config.read(config_path)
                
                # Check that the custom values are still there
                assert config['DEFAULT']['OCO_API_KEY'] == 'custom-api-key'
                assert config['DEFAULT']['OCO_MODEL'] == 'custom-model'
    
    def test_run_with_write_error(self):
        """Test running the migration when there's an error writing the config file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.ini"
            
            # Mock the config path
            with patch('py_opencommit.migrations.migrate_00_initialize_config.get_global_config_path', 
                       return_value=config_path), \
                 patch('builtins.open', side_effect=PermissionError("Permission denied")):
                
                # Run the migration and expect an exception
                migration = Migration00InitializeConfig()
                with pytest.raises(PermissionError):
                    migration.run()