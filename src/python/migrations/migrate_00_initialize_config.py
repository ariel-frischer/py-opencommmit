"""Initialize config migration."""

from pathlib import Path
import logging
import configparser
from ..commands.config import Migration, get_global_config_path, DEFAULT_CONFIG, set_global_config

logger = logging.getLogger("opencommit")

class Migration00InitializeConfig(Migration):
    """Initialize configuration with default values if missing."""
    
    name = "00_initialize_config"
    
    def run(self) -> None:
        """Run the migration."""
        config_path = get_global_config_path()
        
        # If config file doesn't exist or is not a valid INI file, recreate it
        recreate_file = False
        
        if not config_path.exists():
            logger.info("Creating initial configuration file")
            recreate_file = True
        else:
            # Check if it's a valid INI file
            try:
                config_parser = configparser.ConfigParser()
                config_parser.read(config_path)
                
                # If we got here, it's a valid INI file, but might be empty
                if len(config_parser.sections()) == 0 and len(config_parser.defaults()) == 0:
                    logger.info("Config file exists but is empty, initializing with defaults")
                    recreate_file = True
            except Exception as e:
                logger.error(f"Error reading config file, will recreate it: {e}")
                recreate_file = True
        
        if recreate_file:
            # Create a fresh config file with default values
            config_parser = configparser.ConfigParser()
            config_parser['DEFAULT'] = {}
            
            for key, value in DEFAULT_CONFIG.items():
                config_parser['DEFAULT'][key.value] = str(value)
            
            # Write the file
            try:
                with open(config_path, 'w', encoding='utf-8') as f:
                    config_parser.write(f)
                logger.info("Created new configuration file with default values")
            except Exception as e:
                logger.error(f"Failed to create config file: {e}")
                raise