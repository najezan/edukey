"""
Face recognition service implementation.
"""

import face_recognition
import numpy as np
from typing import List, Tuple, Dict, Any
from core.interfaces.face_recognition_interface import IFaceRecognitionService
from utils.logger import logger


class FaceRecognitionService(IFaceRecognitionService):
    """
    Service responsible for face recognition functionality.
    """
    
    def __init__(self, tolerance: float = 0.45, model: str = "small"):
        """
        Initialize face recognition service.
        
        Args:
            tolerance: Face recognition tolerance threshold
            model: Face encoding model ('small' or 'large')
        """
        self.tolerance = tolerance
        self.model = model
        self.known_face_encodings: List[np.ndarray] = []
        self.known_face_names: List[str] = []
        logger.info(f"FaceRecognitionService initialized with tolerance={tolerance}, model={model}")
    
    def encode_faces(self, frame: np.ndarray, face_locations: List[Tuple[int, int, int, int]]) -> List[np.ndarray]:
        """
        Generate face encodings for detected faces.
        
        Args:
            frame: Input image frame
            face_locations: List of face locations
            
        Returns:
            List of face encodings
        """
        try:
            if not face_locations:
                return []
            
            # Generate encodings with higher quality for better accuracy
            num_jitters = 20 if self.model == "large" else 1
            face_encodings = face_recognition.face_encodings(
                frame, 
                face_locations, 
                num_jitters=num_jitters, 
                model=self.model
            )
            
            return face_encodings
            
        except Exception as e:
            logger.error(f"Error encoding faces: {e}")
            return []
    
    def recognize_face(self, face_encoding: np.ndarray) -> Tuple[str, float]:
        """
        Recognize a face from its encoding.
        
        Args:
            face_encoding: Face encoding array
            
        Returns:
            Tuple of (person_name, confidence_score)
        """
        try:
            if len(self.known_face_encodings) == 0:
                return "Unknown", 0.0
            
            # Compare face with known faces
            matches = face_recognition.compare_faces(
                self.known_face_encodings, 
                face_encoding, 
                tolerance=self.tolerance
            )
            
            # Calculate distances to find best match
            face_distances = face_recognition.face_distance(
                self.known_face_encodings, 
                face_encoding
            )
            
            best_match_index = np.argmin(face_distances)
            
            if matches[best_match_index]:
                name = self.known_face_names[best_match_index]
                # Convert distance to confidence percentage
                confidence = (1 - face_distances[best_match_index]) * 100
                return name, confidence
            else:
                return "Unknown", 0.0
                
        except Exception as e:
            logger.error(f"Error recognizing face: {e}")
            return "Unknown", 0.0
    
    def load_known_faces(self, encodings: List[np.ndarray], names: List[str]) -> None:
        """
        Load known face encodings and names.
        
        Args:
            encodings: List of known face encodings
            names: List of corresponding person names
        """
        if len(encodings) != len(names):
            logger.error("Number of encodings and names must match")
            return
        
        self.known_face_encodings = encodings.copy()
        self.known_face_names = names.copy()
        logger.info(f"Loaded {len(encodings)} known faces")
    
    def set_tolerance(self, tolerance: float) -> None:
        """
        Set recognition tolerance.
        
        Args:
            tolerance: Recognition tolerance (0.0-1.0)
        """
        if 0.0 <= tolerance <= 1.0:
            self.tolerance = tolerance
            logger.info(f"Recognition tolerance set to {tolerance}")
        else:
            logger.warning(f"Invalid tolerance value: {tolerance}. Must be between 0.0 and 1.0")
    
    def set_model(self, model: str) -> None:
        """
        Set face encoding model.
        
        Args:
            model: Model type ('small' or 'large')
        """
        if model in ['small', 'large']:
            self.model = model
            logger.info(f"Face encoding model set to {model}")
        else:
            logger.warning(f"Invalid model: {model}. Using current model: {self.model}")
    
    def get_recognition_stats(self) -> Dict[str, Any]:
        """
        Get recognition statistics.
        
        Returns:
            Dictionary containing recognition statistics
        """
        return {
            "total_known_faces": len(self.known_face_encodings),
            "tolerance": self.tolerance,
            "model": self.model,
            "known_names": list(set(self.known_face_names))
        }