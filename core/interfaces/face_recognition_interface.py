"""
Abstract interfaces for face recognition services.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any, Optional
import numpy as np


class IFaceDetectionService(ABC):
    """Interface for face detection functionality."""
    
    @abstractmethod
    def detect_faces(self, frame: np.ndarray, scale_factor: float = 1.0) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in a frame.
        
        Args:
            frame: Input image frame
            scale_factor: Scale factor for detection optimization
            
        Returns:
            List of face locations as (top, right, bottom, left) tuples
        """
        pass
    
    @abstractmethod
    def set_detection_method(self, method: str) -> None:
        """
        Set the face detection method.
        
        Args:
            method: Detection method ('hog' or 'cnn')
        """
        pass


class IFaceRecognitionService(ABC):
    """Interface for face recognition functionality."""
    
    @abstractmethod
    def encode_faces(self, frame: np.ndarray, face_locations: List[Tuple[int, int, int, int]]) -> List[np.ndarray]:
        """
        Generate face encodings for detected faces.
        
        Args:
            frame: Input image frame
            face_locations: List of face locations
            
        Returns:
            List of face encodings
        """
        pass
    
    @abstractmethod
    def recognize_face(self, face_encoding: np.ndarray) -> Tuple[str, float]:
        """
        Recognize a face from its encoding.
        
        Args:
            face_encoding: Face encoding array
            
        Returns:
            Tuple of (person_name, confidence_score)
        """
        pass
    
    @abstractmethod
    def load_known_faces(self, encodings: List[np.ndarray], names: List[str]) -> None:
        """
        Load known face encodings and names.
        
        Args:
            encodings: List of known face encodings
            names: List of corresponding person names
        """
        pass


class IPerformanceOptimizer(ABC):
    """Interface for performance optimization functionality."""
    
    @abstractmethod
    def is_cuda_available(self) -> bool:
        """Check if CUDA is available for GPU acceleration."""
        pass
    
    @abstractmethod
    def optimize_for_hardware(self) -> Dict[str, Any]:
        """
        Get optimized settings based on available hardware.
        
        Returns:
            Dictionary containing optimized settings
        """
        pass


class IBatchProcessor(ABC):
    """Interface for batch processing functionality."""
    
    @abstractmethod
    def process_image_batch(self, image_paths: List[str], person_name: str) -> Tuple[List[np.ndarray], List[str]]:
        """
        Process a batch of images for training.
        
        Args:
            image_paths: List of image file paths
            person_name: Name of the person in images
            
        Returns:
            Tuple of (face_encodings, person_names)
        """
        pass
    
    @abstractmethod
    def process_frame_batch(self, frames: List[np.ndarray]) -> List[Dict[str, Any]]:
        """
        Process a batch of frames for recognition.
        
        Args:
            frames: List of image frames
            
        Returns:
            List of recognition results
        """
        pass