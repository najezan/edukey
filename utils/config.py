"""
Configuration utilities.
"""

import os
import json
from typing import Dict, Any, Optional
from utils.logger import logger

class Config:
    """
    Handles configuration loading and saving.
    """
    DEFAULT_CONFIG = {
        "detection_method": "hog",
        "face_recognition_tolerance": 0.45,
        "batch_size": 16,
        "frame_skip": 1,
        "display_fps": True,
        "rfid_port": 8080,
        "rfid_timeout": 30,
        "storage": {
            "type": "file",  # "file" or "mysql"
            "mysql": {
                "host": "localhost",
                "user": "root",
                "password": "",
                "database": "edukey",
                "port": 3306
            }
        }
    }
    
    def __init__(self, config_file: str = "config.json"):
        """
        Initialize configuration.
        
        Args:
            config_file (str): Path to configuration file
        """
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file or create default.
        
        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                logger.info(f"Configuration loaded from {self.config_file}")
                return config
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
                logger.info("Using default configuration")
                return self.DEFAULT_CONFIG.copy()
        else:
            logger.info(f"Configuration file not found, using defaults")
            return self.DEFAULT_CONFIG.copy()
    
    def save_config(self) -> bool:
        """
        Save configuration to file.
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(self.config_file)), exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            logger.info(f"Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
    
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key (str): Configuration key
            default (Any, optional): Default value if key not found
            
        Returns:
            Any: Configuration value
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value.
        
        Args:
            key (str): Configuration key
            value (Any): Configuration value
        """
        self.config[key] = value
    
    def update(self, config_dict: Dict[str, Any]) -> None:
        """
        Update multiple configuration values.
        
        Args:
            config_dict (Dict[str, Any]): Dictionary of configuration values
        """
        self.config.update(config_dict)
