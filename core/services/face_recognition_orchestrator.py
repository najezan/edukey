"""
Orchestrator service that coordinates all face recognition services.
This replaces the monolithic FaceRecognitionSystem with a service-oriented approach.
"""

import time
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass

from core.services.face_detection_service import FaceDetectionService
from core.services.face_recognition_service import FaceRecognitionService
from core.services.performance_optimizer import PerformanceOptimizer
from core.services.batch_processor import BatchProcessor
from core.services.configuration_service import ConfigurationService
from core.interfaces.anti_spoofing_interface import IAntiSpoofingService
from core.attendance_manager import AttendanceManager
from database.db_manager import DatabaseManager
from utils.logger import logger


@dataclass
class RecognitionResult:
    """Result of face recognition operation."""
    name: str
    confidence: float
    class_info: str
    face_location: Tuple[int, int, int, int]
    anti_spoofing_result: Dict[str, Any]
    verification_method: str = "face"


@dataclass
class FrameProcessingResult:
    """Result of frame processing operation."""
    frame: np.ndarray
    face_locations: List[Tuple[int, int, int, int]]
    recognitions: List[RecognitionResult]
    processing_time: float
    fps: float


class FaceRecognitionOrchestrator:
    """
    Orchestrates all face recognition services to provide a unified interface.
    This replaces the original FaceRecognitionSystem with better separation of concerns.
    """
    
    def __init__(self, 
                 base_dir: str = "data",
                 anti_spoofing_service: Optional[IAntiSpoofingService] = None):
        """
        Initialize the face recognition orchestrator.
        
        Args:
            base_dir: Base directory for data storage
            anti_spoofing_service: Anti-spoofing service implementation
        """
        logger.info("Initializing FaceRecognitionOrchestrator")
        
        # Initialize core services
        self.config_service = ConfigurationService()
        self.performance_optimizer = PerformanceOptimizer()
        
        # Get optimized settings
        optimal_settings = self.performance_optimizer.optimize_for_hardware()
        
        # Initialize detection and recognition services with optimal settings
        face_config = self.config_service.get_face_recognition_config()
        self.detection_service = FaceDetectionService(face_config.detection_method)
        self.recognition_service = FaceRecognitionService(
            tolerance=face_config.tolerance,
            model=face_config.model
        )
        
        # Initialize batch processor
        self.batch_processor = BatchProcessor(
            self.detection_service,
            self.recognition_service,
            self.performance_optimizer
        )
        
        # Initialize database and attendance managers
        self.db_manager = DatabaseManager(base_dir)
        self.attendance_manager = AttendanceManager(self.db_manager)
        
        # Load known faces
        self._load_known_faces()
        
        # Initialize anti-spoofing service
        self.anti_spoofing_service = anti_spoofing_service
        self.enable_anti_spoofing = self.config_service.get_anti_spoofing_config().enabled
        
        # RFID authentication state
        self.last_rfid_person: Optional[str] = None
        self.last_rfid_time: float = 0
        self.rfid_timeout = self.config_service.get_rfid_config().timeout
        
        # Performance tracking
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.current_fps = 0.0
        
        # Frame buffer for liveness detection
        self.frame_buffer: List[np.ndarray] = []
        self.max_frame_buffer = self.config_service.get_anti_spoofing_config().max_frame_buffer
        
        logger.info("FaceRecognitionOrchestrator initialized successfully")
    
    def _load_known_faces(self) -> None:
        """Load known face encodings from database."""
        try:
            encodings = self.db_manager.face_encodings
            names = self.db_manager.face_names
            
            if encodings and names:
                self.recognition_service.load_known_faces(encodings, names)
                logger.info(f"Loaded {len(encodings)} known faces")
            else:
                logger.info("No known faces found in database")
                
        except Exception as e:
            logger.error(f"Error loading known faces: {e}")
    
    def process_frame(self, frame: np.ndarray, scale_factor: float = 0.25) -> FrameProcessingResult:
        """
        Process a single frame for face recognition.
        
        Args:
            frame: Input frame
            scale_factor: Scale factor for performance optimization
            
        Returns:
            FrameProcessingResult containing all recognition data
        """
        start_time = time.time()
        
        try:
            # Update frame buffer for liveness detection
            self._update_frame_buffer(frame)
            
            # Detect faces
            face_locations = self.detection_service.detect_faces(frame, scale_factor)
            
            recognitions = []
            if face_locations:
                # Create RGB version for face_recognition library
                rgb_frame = frame[:, :, ::-1]  # BGR to RGB
                
                # Get face encodings
                face_encodings = self.recognition_service.encode_faces(rgb_frame, face_locations)
                
                # Process each detected face
                for i, (face_encoding, face_location) in enumerate(zip(face_encodings, face_locations)):
                    recognition = self._process_single_face(
                        face_encoding, 
                        face_location, 
                        rgb_frame, 
                        frame
                    )
                    recognitions.append(recognition)
            
            # Calculate processing metrics
            processing_time = time.time() - start_time
            fps = self._calculate_fps()
            
            return FrameProcessingResult(
                frame=frame,
                face_locations=face_locations,
                recognitions=recognitions,
                processing_time=processing_time,
                fps=fps
            )
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            return FrameProcessingResult(
                frame=frame,
                face_locations=[],
                recognitions=[],
                processing_time=time.time() - start_time,
                fps=0.0
            )
    
    def _process_single_face(self, 
                           face_encoding: np.ndarray, 
                           face_location: Tuple[int, int, int, int],
                           rgb_frame: np.ndarray,
                           original_frame: np.ndarray) -> RecognitionResult:
        """
        Process a single detected face.
        
        Args:
            face_encoding: Face encoding
            face_location: Face location coordinates
            rgb_frame: RGB version of frame
            original_frame: Original frame for attendance
            
        Returns:
            RecognitionResult for the face
        """
        # Recognize face
        name, confidence = self.recognition_service.recognize_face(face_encoding)
        
        # Get class information
        class_info = ""
        if name != "Unknown" and name in self.db_manager.student_database:
            student_data = self.db_manager.student_database[name]
            class_info = student_data.get("class", "")
        
        # Check RFID verification
        verification_method = "face"
        if self._is_rfid_verified(name):
            verification_method = "face+rfid"
            class_info += " [RFID Verified]"
            confidence = min(100, confidence + 10)  # Boost confidence for RFID verified
        
        # Anti-spoofing check
        anti_spoofing_result = {}
        if self.enable_anti_spoofing and self.anti_spoofing_service:
            anti_spoofing_result = self._check_anti_spoofing(
                face_location, 
                rgb_frame, 
                name, 
                confidence
            )
            
            # Update name and confidence based on anti-spoofing results
            if not anti_spoofing_result.get("is_real", True):
                spoof_penalty = int((1 - anti_spoofing_result.get("real_score", 0.5)) * 50)
                confidence = max(0, confidence - spoof_penalty)
                
                if confidence < 40:
                    name = "Spoofing Attempt"
                    class_info = "ALERT: Photo/Screen detected"
                elif anti_spoofing_result.get("real_score", 1.0) < 0.3:
                    class_info += " [SPOOFING SUSPECTED]"
        
        # Record attendance if confidence is high enough
        min_confidence = self.config_service.get_raw_config().get("attendance_min_confidence", 85)
        if confidence >= min_confidence and name not in ["Unknown", "Spoofing Attempt"]:
            success, message = self.attendance_manager.mark_attendance(
                name,
                confidence,
                original_frame,
                verification_method=verification_method,
                class_info=class_info
            )
            
            if not success:
                class_info += f" [{message}]"
        elif confidence < min_confidence and name != "Unknown":
            class_info += f" [Confidence too low: {confidence:.0f}%]"
        
        return RecognitionResult(
            name=name,
            confidence=confidence,
            class_info=class_info,
            face_location=face_location,
            anti_spoofing_result=anti_spoofing_result,
            verification_method=verification_method
        )
    
    def _update_frame_buffer(self, frame: np.ndarray) -> None:
        """Update frame buffer for liveness detection."""
        self.frame_buffer.append(frame.copy())
        if len(self.frame_buffer) > self.max_frame_buffer:
            self.frame_buffer.pop(0)
    
    def _is_rfid_verified(self, name: str) -> bool:
        """Check if person is RFID verified."""
        if not self.last_rfid_person:
            return False
        
        if (time.time() - self.last_rfid_time) > self.rfid_timeout:
            return False
        
        return name == self.last_rfid_person
    
    def _check_anti_spoofing(self, 
                           face_location: Tuple[int, int, int, int],
                           rgb_frame: np.ndarray,
                           name: str,
                           confidence: float) -> Dict[str, Any]:
        """
        Perform anti-spoofing checks.
        
        Args:
            face_location: Face location coordinates
            rgb_frame: RGB frame
            name: Recognized name
            confidence: Recognition confidence
            
        Returns:
            Anti-spoofing result dictionary
        """
        result = {}
        
        try:
            # Extract face region
            top, right, bottom, left = face_location
            face_img = rgb_frame[top:bottom, left:right]
            
            if face_img.shape[0] > 20 and face_img.shape[1] > 20 and self.anti_spoofing_service:
                # Check if face is real
                is_real, real_score, spoof_metadata = self.anti_spoofing_service.is_real_face(face_img)
                
                result.update({
                    "is_real": is_real,
                    "real_score": real_score,
                    "spoof_metadata": spoof_metadata
                })
                
                if not is_real and confidence > 0:
                    logger.warning(f"Potential spoofing attack detected for {name}: score={real_score}")
                
                # Liveness detection if we have enough frames
                if len(self.frame_buffer) >= 3 and self.anti_spoofing_service:
                    is_live, liveness_score, liveness_metadata = self.anti_spoofing_service.analyze_face_liveness(
                        self.frame_buffer[-3:]
                    )
                    
                    result["liveness"] = {
                        "is_live": is_live,
                        "liveness_score": liveness_score,
                        "liveness_metadata": liveness_metadata
                    }
                    
                    if not is_live and liveness_score < 0.3:
                        logger.warning(f"Potential liveness attack detected: score={liveness_score}")
            
        except Exception as e:
            logger.error(f"Error in anti-spoofing check: {e}")
        
        return result
    
    def _calculate_fps(self) -> float:
        """Calculate current FPS."""
        self.frame_count += 1
        current_time = time.time()
        
        if current_time - self.last_fps_time >= 1.0:  # Update FPS every second
            self.current_fps = self.frame_count / (current_time - self.last_fps_time)
            self.frame_count = 0
            self.last_fps_time = current_time
        
        return self.current_fps
    
    def set_rfid_authentication(self, person_name: str) -> None:
        """
        Set RFID authentication for a person.
        
        Args:
            person_name: Person name associated with RFID
        """
        self.last_rfid_person = person_name
        self.last_rfid_time = time.time()
        logger.info(f"RFID authentication set for {person_name}")
    
    def verify_two_factor_auth(self, face_name: str, rfid_name: str) -> Tuple[bool, str]:
        """
        Verify two-factor authentication (face + RFID).
        
        Args:
            face_name: Name detected by face recognition
            rfid_name: Name associated with RFID card
            
        Returns:
            Tuple of (success, message)
        """
        if face_name == rfid_name:
            return True, "Two-factor authentication successful"
        elif face_name == "Unknown":
            return False, "Face not recognized"
        elif face_name == "Spoofing Attempt":
            return False, "Anti-spoofing check failed"
        elif rfid_name is None:
            return False, "RFID card not presented"
        else:
            return False, "Face and RFID card don't match"
    
    def process_training_batch(self, person_names: List[str]) -> bool:
        """
        Process training for multiple persons.
        
        Args:
            person_names: List of person names to train
            
        Returns:
            True if training was successful
        """
        try:
            dataset_dir = self.db_manager.dataset_dir
            encodings, names = self.batch_processor.process_training_batch(dataset_dir, person_names)
            
            if encodings and names:
                # Add to database
                success = self.db_manager.add_face_encodings(encodings, names)
                if success:
                    # Reload known faces
                    self._load_known_faces()
                    logger.info(f"Training completed for {len(set(names))} persons")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error in training batch: {e}")
            return False
    
    def update_settings(self, settings: Dict[str, Any]) -> None:
        """
        Update system settings.
        
        Args:
            settings: Dictionary of settings to update
        """
        try:
            # Update configuration service
            face_config = self.config_service.get_face_recognition_config()
            
            if "face_recognition_tolerance" in settings:
                face_config.tolerance = settings["face_recognition_tolerance"]
                self.recognition_service.set_tolerance(face_config.tolerance)
            
            if "detection_method" in settings:
                face_config.detection_method = settings["detection_method"]
                self.detection_service.set_detection_method(face_config.detection_method)
            
            # Update configuration
            self.config_service.update_face_recognition_config(face_config)
            
            # Update other settings
            if "rfid_timeout" in settings:
                self.rfid_timeout = settings["rfid_timeout"]
            
            if "enable_anti_spoofing" in settings:
                self.enable_anti_spoofing = settings["enable_anti_spoofing"]
            
            if "spoofing_detection_threshold" in settings and self.anti_spoofing_service:
                self.anti_spoofing_service.update_settings(settings)
            
            logger.info("Settings updated successfully")
            
        except Exception as e:
            logger.error(f"Error updating settings: {e}")
    
    def get_system_stats(self) -> Dict[str, Any]:
        """
        Get system statistics.
        
        Returns:
            Dictionary containing system statistics
        """
        recognition_stats = self.recognition_service.get_recognition_stats()
        optimal_settings = self.performance_optimizer.optimize_for_hardware()
        
        return {
            "recognition": recognition_stats,
            "performance": optimal_settings,
            "anti_spoofing_enabled": self.enable_anti_spoofing,
            "rfid_authenticated": self.last_rfid_person is not None,
            "current_fps": self.current_fps,
            "frame_buffer_size": len(self.frame_buffer)
        }