"""
Configuration service implementation.
"""

from typing import Dict, Any, List, Callable
from dataclasses import dataclass
from utils.config import Config
from utils.logger import logger


@dataclass
class FaceRecognitionConfig:
    """Configuration for face recognition settings."""
    tolerance: float = 0.45
    detection_method: str = "hog"
    batch_size: int = 16
    model: str = "small"
    num_jitters: int = 1


@dataclass
class AntiSpoofingConfig:
    """Configuration for anti-spoofing settings."""
    enabled: bool = True
    threshold: float = 0.5
    liveness_detection: bool = True
    max_frame_buffer: int = 10


@dataclass
class PerformanceConfig:
    """Configuration for performance settings."""
    frame_skip: int = 1
    display_fps: bool = True
    max_workers: int = 4
    use_gpu: bool = False


@dataclass
class RFIDConfig:
    """Configuration for RFID settings."""
    port: int = 8080
    timeout: int = 30
    enabled: bool = True


class ConfigurationService:
    """
    Centralized configuration management service.
    """
    
    def __init__(self, config_file: str = "config.json"):
        """
        Initialize configuration service.
        
        Args:
            config_file: Path to configuration file
        """
        self._config = Config(config_file)
        self._observers: List[Callable[[Dict[str, Any]], None]] = []
        logger.info("ConfigurationService initialized")
    
    def get_face_recognition_config(self) -> FaceRecognitionConfig:
        """
        Get face recognition configuration.
        
        Returns:
            FaceRecognitionConfig object
        """
        return FaceRecognitionConfig(
            tolerance=self._config.get("face_recognition_tolerance", 0.45),
            detection_method=self._config.get("detection_method", "hog"),
            batch_size=self._config.get("batch_size", 16),
            model=self._config.get("face_model", "small"),
            num_jitters=self._config.get("num_jitters", 1)
        )
    
    def get_anti_spoofing_config(self) -> AntiSpoofingConfig:
        """
        Get anti-spoofing configuration.
        
        Returns:
            AntiSpoofingConfig object
        """
        return AntiSpoofingConfig(
            enabled=self._config.get("enable_anti_spoofing", True),
            threshold=self._config.get("spoofing_detection_threshold", 0.5),
            liveness_detection=self._config.get("liveness_detection", True),
            max_frame_buffer=self._config.get("max_frame_buffer", 10)
        )
    
    def get_performance_config(self) -> PerformanceConfig:
        """
        Get performance configuration.
        
        Returns:
            PerformanceConfig object
        """
        return PerformanceConfig(
            frame_skip=self._config.get("frame_skip", 1),
            display_fps=self._config.get("display_fps", True),
            max_workers=self._config.get("max_workers", 4),
            use_gpu=self._config.get("use_gpu", False)
        )
    
    def get_rfid_config(self) -> RFIDConfig:
        """
        Get RFID configuration.
        
        Returns:
            RFIDConfig object
        """
        return RFIDConfig(
            port=self._config.get("rfid_port", 8080),
            timeout=self._config.get("rfid_timeout", 30),
            enabled=self._config.get("rfid_enabled", True)
        )
    
    def update_face_recognition_config(self, config: FaceRecognitionConfig) -> None:
        """
        Update face recognition configuration.
        
        Args:
            config: New face recognition configuration
        """
        updates = {
            "face_recognition_tolerance": config.tolerance,
            "detection_method": config.detection_method,
            "batch_size": config.batch_size,
            "face_model": config.model,
            "num_jitters": config.num_jitters
        }
        self._update_config(updates)
    
    def update_anti_spoofing_config(self, config: AntiSpoofingConfig) -> None:
        """
        Update anti-spoofing configuration.
        
        Args:
            config: New anti-spoofing configuration
        """
        updates = {
            "enable_anti_spoofing": config.enabled,
            "spoofing_detection_threshold": config.threshold,
            "liveness_detection": config.liveness_detection,
            "max_frame_buffer": config.max_frame_buffer
        }
        self._update_config(updates)
    
    def update_performance_config(self, config: PerformanceConfig) -> None:
        """
        Update performance configuration.
        
        Args:
            config: New performance configuration
        """
        updates = {
            "frame_skip": config.frame_skip,
            "display_fps": config.display_fps,
            "max_workers": config.max_workers,
            "use_gpu": config.use_gpu
        }
        self._update_config(updates)
    
    def update_rfid_config(self, config: RFIDConfig) -> None:
        """
        Update RFID configuration.
        
        Args:
            config: New RFID configuration
        """
        updates = {
            "rfid_port": config.port,
            "rfid_timeout": config.timeout,
            "rfid_enabled": config.enabled
        }
        self._update_config(updates)
    
    def _update_config(self, updates: Dict[str, Any]) -> None:
        """
        Update configuration and notify observers.
        
        Args:
            updates: Dictionary of configuration updates
        """
        self._config.update(updates)
        success = self._config.save_config()
        
        if success:
            self._notify_observers(updates)
            logger.info(f"Configuration updated: {list(updates.keys())}")
        else:
            logger.error("Failed to save configuration updates")
    
    def add_observer(self, observer: Callable[[Dict[str, Any]], None]) -> None:
        """
        Add configuration change observer.
        
        Args:
            observer: Callback function to notify on configuration changes
        """
        self._observers.append(observer)
    
    def remove_observer(self, observer: Callable[[Dict[str, Any]], None]) -> None:
        """
        Remove configuration change observer.
        
        Args:
            observer: Observer to remove
        """
        if observer in self._observers:
            self._observers.remove(observer)
    
    def _notify_observers(self, changes: Dict[str, Any]) -> None:
        """
        Notify all observers of configuration changes.
        
        Args:
            changes: Dictionary of configuration changes
        """
        for observer in self._observers:
            try:
                observer(changes)
            except Exception as e:
                logger.error(f"Error notifying configuration observer: {e}")
    
    def get_raw_config(self) -> Dict[str, Any]:
        """
        Get raw configuration dictionary.
        
        Returns:
            Raw configuration dictionary
        """
        return self._config.config.copy()
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        self._config.config = self._config.DEFAULT_CONFIG.copy()
        success = self._config.save_config()
        
        if success:
            self._notify_observers(self._config.config)
            logger.info("Configuration reset to defaults")
        else:
            logger.error("Failed to reset configuration")