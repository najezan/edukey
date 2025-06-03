"""
Abstract interface for anti-spoofing services.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any, Optional
import numpy as np


class IAntiSpoofingService(ABC):
    """Interface for anti-spoofing functionality."""
    
    @abstractmethod
    def is_real_face(self, face_image: np.ndarray) -> Tuple[bool, float, Optional[Dict[str, Any]]]:
        """
        Determine if a face image is real or a spoofing attempt.
        
        Args:
            face_image: Face image to analyze
            
        Returns:
            Tuple of (is_real, confidence_score, metadata)
        """
        pass
    
    @abstractmethod
    def analyze_face_liveness(self, frames: List[np.ndarray]) -> Tuple[bool, float, Dict[str, Any]]:
        """
        Analyze face liveness across multiple frames.
        
        Args:
            frames: List of consecutive frames
            
        Returns:
            Tuple of (is_live, liveness_score, metadata)
        """
        pass
    
    @abstractmethod
    def detect_abnormal_face_structure(self, face_image: np.ndarray) -> Tuple[bool, Dict[str, Any]]:
        """
        Detect abnormal face structures that might indicate spoofing.
        
        Args:
            face_image: Face image to analyze
            
        Returns:
            Tuple of (is_abnormal, metadata)
        """
        pass
    
    @abstractmethod
    def update_settings(self, settings: Dict[str, Any]) -> None:
        """
        Update anti-spoofing settings.
        
        Args:
            settings: Dictionary of settings to update
        """
        pass