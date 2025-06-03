"""
Legacy adapter for backward compatibility with existing FaceRecognitionSystem usage.
This allows existing code to work with the new service-oriented architecture.
"""

import numpy as np
from typing import List, Tuple, Dict, Any, Optional

from core.services.face_recognition_orchestrator import FaceRecognitionOrchestrator, RecognitionResult
from core.anti_spoofing import AntiSpoofingSystem
from utils.logger import logger


class FaceRecognitionSystemAdapter:
    """
    Adapter that provides backward compatibility with the original FaceRecognitionSystem interface.
    
    This class wraps the new FaceRecognitionOrchestrator and maintains the same API
    as the original FaceRecognitionSystem to ensure existing code continues to work.
    """
    
    def __init__(self, base_dir: str = "data"):
        """
        Initialize the adapter with the new orchestrator.
        
        Args:
            base_dir: Base directory for data storage
        """
        logger.info("Initializing FaceRecognitionSystemAdapter for backward compatibility")
        
        # Initialize anti-spoofing service
        self.anti_spoofing = AntiSpoofingSystem()
        
        # Initialize the new orchestrator
        self.orchestrator = FaceRecognitionOrchestrator(
            base_dir=base_dir,
            anti_spoofing_service=self.anti_spoofing
        )
        
        # Expose legacy properties for backward compatibility
        self._setup_legacy_properties()
        
        logger.info("FaceRecognitionSystemAdapter initialized successfully")
    
    def _setup_legacy_properties(self) -> None:
        """Setup properties that mimic the original FaceRecognitionSystem."""
        # Database manager
        self.db_manager = self.orchestrator.db_manager
        self.attendance_manager = self.orchestrator.attendance_manager
        
        # Configuration
        self.config = self.orchestrator.config_service._config
        
        # Performance settings
        optimal_settings = self.orchestrator.performance_optimizer.optimize_for_hardware()
        self.detection_method = optimal_settings["detection_method"]
        self.batch_size = optimal_settings["batch_size"]
        self.frame_skip = self.orchestrator.config_service.get_performance_config().frame_skip
        self.display_fps = self.orchestrator.config_service.get_performance_config().display_fps
        
        # Face recognition settings
        face_config = self.orchestrator.config_service.get_face_recognition_config()
        self.face_recognition_tolerance = face_config.tolerance
        
        # Anti-spoofing settings
        anti_spoofing_config = self.orchestrator.config_service.get_anti_spoofing_config()
        self.enable_anti_spoofing = anti_spoofing_config.enabled
        
        # RFID settings
        rfid_config = self.orchestrator.config_service.get_rfid_config()
        self.rfid_timeout = rfid_config.timeout
        
        # Performance tracking
        self.current_frame = 0
        self.fps = 0
        self.frame_time = 0
        
        # Known faces (for compatibility)
        recognition_stats = self.orchestrator.recognition_service.get_recognition_stats()
        self.known_face_encodings = self.orchestrator.recognition_service.known_face_encodings
        self.known_face_names = self.orchestrator.recognition_service.known_face_names
        self.trained_people = set(recognition_stats["known_names"])
        self.student_database = self.db_manager.student_database
        
        # RFID authentication
        self.last_rfid_person = self.orchestrator.last_rfid_person
        self.last_rfid_time = self.orchestrator.last_rfid_time
        
        # CPU cores
        self.n_cpu_cores = self.orchestrator.performance_optimizer._cpu_cores
        
        # Frame buffer
        self.frame_buffer = self.orchestrator.frame_buffer
        self.max_frame_buffer = self.orchestrator.max_frame_buffer
    
    def is_cuda_available(self) -> bool:
        """Check if CUDA is available (legacy method)."""
        return self.orchestrator.performance_optimizer.is_cuda_available()
    
    def process_image_batch(self, image_batch: List[str], person_name: str) -> Tuple[List[Any], List[str]]:
        """
        Process a batch of images for training (legacy method).
        
        Args:
            image_batch: List of image paths
            person_name: Person name
            
        Returns:
            Tuple of face encodings and names
        """
        return self.orchestrator.batch_processor.process_image_batch(image_batch, person_name)
    
    def process_face_recognition_batch(self, batch_frames: List[Tuple[np.ndarray, np.ndarray, float]]) -> List[Tuple[np.ndarray, List[Tuple[int, int, int, int]], List[Tuple[str, int, str, Dict[str, Any]]]]]:
        """
        Process a batch of frames for face recognition (legacy method).
        
        Args:
            batch_frames: List of (frame, rgb_frame, scale_factor) tuples
            
        Returns:
            List of (frame, face_locations, face_matches) tuples
        """
        results = []
        
        for frame, rgb_frame, scale_factor in batch_frames:
            # Process frame using new orchestrator
            processing_result = self.orchestrator.process_frame(frame, scale_factor)
            
            # Convert to legacy format
            face_matches = []
            for recognition in processing_result.recognitions:
                face_match = (
                    recognition.name,
                    int(recognition.confidence),
                    recognition.class_info,
                    recognition.anti_spoofing_result
                )
                face_matches.append(face_match)
            
            # Update performance tracking
            self.fps = processing_result.fps
            self.frame_time = processing_result.processing_time
            
            results.append((frame, processing_result.face_locations, face_matches))
        
        return results
    
    def verify_two_factor_auth(self, face_name: str, rfid_name: str) -> Tuple[bool, str]:
        """Verify two-factor authentication (legacy method)."""
        return self.orchestrator.verify_two_factor_auth(face_name, rfid_name)
    
    def set_rfid_authentication(self, person_name: str) -> None:
        """Set RFID authentication (legacy method)."""
        self.orchestrator.set_rfid_authentication(person_name)
        # Update legacy properties
        self.last_rfid_person = self.orchestrator.last_rfid_person
        self.last_rfid_time = self.orchestrator.last_rfid_time
    
    def update_settings(self, settings: Dict[str, Any]) -> None:
        """Update settings (legacy method)."""
        self.orchestrator.update_settings(settings)
        # Update legacy properties
        self._setup_legacy_properties()
    
    # Additional legacy methods that might be used
    def _determine_detection_method(self) -> str:
        """Legacy method for determining detection method."""
        optimal_settings = self.orchestrator.performance_optimizer.optimize_for_hardware()
        return optimal_settings["detection_method"]
    
    def _determine_batch_size(self) -> int:
        """Legacy method for determining batch size."""
        return self.orchestrator.performance_optimizer.get_recommended_batch_size("recognition")
    
    # Properties for backward compatibility
    @property
    def current_fps(self) -> float:
        """Get current FPS."""
        return self.orchestrator.current_fps
    
    @property
    def frame_count(self) -> int:
        """Get current frame count."""
        return self.orchestrator.frame_count


# For complete backward compatibility, we can also create an alias
FaceRecognitionSystem = FaceRecognitionSystemAdapter