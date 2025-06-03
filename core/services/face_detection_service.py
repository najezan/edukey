"""
Face detection service implementation.
"""

import face_recognition
import numpy as np
from typing import List, Tuple
from core.interfaces.face_recognition_interface import IFaceDetectionService
from utils.logger import logger


class FaceDetectionService(IFaceDetectionService):
    """
    Service responsible for face detection functionality.
    """
    
    def __init__(self, detection_method: str = "hog"):
        """
        Initialize face detection service.
        
        Args:
            detection_method: Detection method ('hog' or 'cnn')
        """
        self.detection_method = detection_method
        logger.info(f"FaceDetectionService initialized with {detection_method} method")
    
    def detect_faces(self, frame: np.ndarray, scale_factor: float = 1.0) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in a frame.
        
        Args:
            frame: Input image frame
            scale_factor: Scale factor for detection optimization
            
        Returns:
            List of face locations as (top, right, bottom, left) tuples
        """
        try:
            # Scale down frame if needed for performance
            if scale_factor != 1.0:
                height, width = frame.shape[:2]
                small_frame = frame[::int(1/scale_factor), ::int(1/scale_factor)]
                face_locations = face_recognition.face_locations(small_frame, model=self.detection_method)
                
                # Scale back up face locations
                scaled_locations = []
                for (top, right, bottom, left) in face_locations:
                    top = int(top / scale_factor)
                    right = int(right / scale_factor)
                    bottom = int(bottom / scale_factor)
                    left = int(left / scale_factor)
                    scaled_locations.append((top, right, bottom, left))
                
                return scaled_locations
            else:
                return face_recognition.face_locations(frame, model=self.detection_method)
                
        except Exception as e:
            logger.error(f"Error detecting faces: {e}")
            return []
    
    def set_detection_method(self, method: str) -> None:
        """
        Set the face detection method.
        
        Args:
            method: Detection method ('hog' or 'cnn')
        """
        if method in ['hog', 'cnn']:
            self.detection_method = method
            logger.info(f"Detection method changed to {method}")
        else:
            logger.warning(f"Invalid detection method: {method}. Using current method: {self.detection_method}")