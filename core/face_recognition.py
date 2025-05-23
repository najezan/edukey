"""
Modified version of FaceRecognitionSystem to include anti-spoofing support.
"""

import os
import time
import numpy as np
import multiprocessing
from typing import List, Tuple, Dict, Any
import face_recognition

from database.db_manager import DatabaseManager
from utils.config import Config
from utils.logger import logger
from core.anti_spoofing import AntiSpoofingSystem
from core.attendance_manager import AttendanceManager

# Check for GPU availability and configure dlib to use CUDA if available
try:
    import dlib
    if dlib.DLIB_USE_CUDA:
        logger.info("CUDA is available! GPU acceleration enabled.")
        # Set dlib's CUDA device to 0 (first GPU)
        dlib.cuda.set_device(0)
    else:
        logger.info("CUDA is not available. Using CPU only.")
except:
    logger.warning("Unable to check CUDA status. Assuming CPU only.")

class FaceRecognitionSystem:
    """
    Core face recognition system that handles detection and recognition.
    
    This class provides methods for face detection, recognition, 
    and processing of face images, with additional anti-spoofing protection.
    """
    
    def __init__(self, base_dir: str = "data"):
        """
        Initialize the face recognition system.
        
        Args:
            base_dir (str): Base directory for data storage
        """
        # Initialize database manager
        self.db_manager = DatabaseManager(base_dir)
        
        # Initialize config
        self.config = Config()
        
        # Initialize attendance manager
        self.attendance_manager = AttendanceManager(self.db_manager)
        
        # Configure face detection and recognition settings
        self.detection_method = self._determine_detection_method()
        logger.info(f"Using {self.detection_method.upper()} face detection method")
        
        # Get other settings from config
        self.face_recognition_tolerance = self.config.get("face_recognition_tolerance", 0.45)
        self.batch_size = self._determine_batch_size()
        self.frame_skip = self.config.get("frame_skip", 1)
        self.display_fps = self.config.get("display_fps", True)
        
        # Initialize anti-spoofing system
        self.anti_spoofing = AntiSpoofingSystem()
        self.enable_anti_spoofing = self.config.get("enable_anti_spoofing", True)
        
        # Derived from database manager
        self.known_face_encodings = self.db_manager.face_encodings
        self.known_face_names = self.db_manager.face_names
        self.trained_people = self.db_manager.trained_people
        self.student_database = self.db_manager.student_database
        
        # Performance tracking
        self.current_frame = 0
        self.fps = 0
        self.frame_time = 0
        
        # RFID authentication variables
        self.last_rfid_person = None
        self.last_rfid_time = 0
        self.rfid_timeout = self.config.get("rfid_timeout", 30)
        
        # Compute resources
        self.n_cpu_cores = max(1, multiprocessing.cpu_count() - 1)
        
        # Buffer for anti-spoofing liveness detection
        self.frame_buffer = []
        self.max_frame_buffer = 10  # Keep last 10 frames for liveness detection
        
    def _determine_detection_method(self) -> str:
        """
        Determine the best face detection method based on GPU availability.
        
        Returns:
            str: Detection method ('cnn' or 'hog')
        """
        # Get from config first
        method = self.config.get("detection_method")
        
        # If not specified in config, determine based on GPU availability
        if not method:
            method = "cnn" if self.is_cuda_available() else "hog"
            # Save to config
            self.config.set("detection_method", method)
            self.config.save_config()
            
        return method
    
    def _determine_batch_size(self) -> int:
        """
        Determine the optimal batch size based on GPU availability.
        
        Returns:
            int: Batch size
        """
        # Get from config first
        batch_size = self.config.get("batch_size")
        
        # If not specified in config, determine based on GPU availability
        if not batch_size:
            batch_size = 16 if self.is_cuda_available() else 4
            # Save to config
            self.config.set("batch_size", batch_size)
            self.config.save_config()
            
        return batch_size
        
    def is_cuda_available(self) -> bool:
        """
        Check if CUDA is available for dlib and configure for maximum performance.
        
        Returns:
            bool: True if CUDA is available, False otherwise
        """
        try:
            cuda_available = dlib.DLIB_USE_CUDA
            if cuda_available:
                # Use the first device by default
                dlib.cuda.set_device(0)
            return cuda_available
        except:
            return False
    
    def process_image_batch(self, image_batch: List[str], person_name: str) -> Tuple[List[Any], List[str]]:
        """
        Process a batch of images for training using GPU acceleration.
        
        Args:
            image_batch (List[str]): List of image paths
            person_name (str): Person name
            
        Returns:
            Tuple[List[Any], List[str]]: Tuple of face encodings and names
        """
        batch_encodings = []
        batch_names = []
        
        for img_path in image_batch:
            # Load the image with GPU acceleration if available
            image = face_recognition.load_image_file(img_path)
            
            # Find face locations
            face_locations = face_recognition.face_locations(image, model=self.detection_method)
            
            if len(face_locations) > 0:
                # Use higher num_jitters for better accuracy when GPU is available
                num_jitters = 20 if self.is_cuda_available() else 1
                model = "large" if self.is_cuda_available() else "small"
                
                face_encodings = face_recognition.face_encodings(
                    image, face_locations, num_jitters=num_jitters, model=model)
                
                if face_encodings:
                    batch_encodings.append(face_encodings[0])
                    batch_names.append(person_name)
        
        return batch_encodings, batch_names
    
    def process_face_recognition_batch(self, batch_frames: List[Tuple[np.ndarray, np.ndarray, float]]) -> List[Tuple[np.ndarray, List[Tuple[int, int, int, int]], List[Tuple[str, int, str, Dict[str, Any]]]]]:
        """
        Process a batch of frames for face recognition using GPU acceleration.
        
        Args:
            batch_frames (List[Tuple[np.ndarray, np.ndarray, float]]): List of (frame, rgb_frame, scale_factor) tuples
            
        Returns:
            List[Tuple[np.ndarray, List[Tuple[int, int, int, int]], List[Tuple[str, int, str, Dict[str, Any]]]]]: 
                List of (frame, face_locations, face_matches) tuples with anti-spoofing results
        """
        results = []
        
        # Update frame buffer for liveness detection
        for frame, _, _ in batch_frames:
            self.frame_buffer.append(frame.copy())
            # Keep buffer size limited
            if len(self.frame_buffer) > self.max_frame_buffer:
                self.frame_buffer.pop(0)
        
        # Perform liveness detection if we have enough frames
        liveness_result = None
        if len(self.frame_buffer) >= 3 and self.enable_anti_spoofing:
            is_live, liveness_score, liveness_metadata = self.anti_spoofing.analyze_face_liveness(self.frame_buffer[-3:])
            if not is_live and liveness_score < 0.3:  # Very low movement
                logger.warning(f"Potential liveness attack detected: score={liveness_score}")
                liveness_result = {
                    "is_live": is_live,
                    "liveness_score": liveness_score,
                    "liveness_metadata": liveness_metadata
                }
        
        for frame, rgb_frame, scale_factor in batch_frames:
            # Detect face locations
            face_locations = face_recognition.face_locations(rgb_frame, model=self.detection_method)
            
            if face_locations:
                # Get face encodings
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                
                # Match faces
                face_matches = []
                for i, face_encoding in enumerate(face_encodings):
                    # See if the face is a match for known faces
                    matches = face_recognition.compare_faces(
                        self.known_face_encodings, face_encoding, tolerance=self.face_recognition_tolerance)
                    name = "Unknown"
                    confidence = 0
                    class_info = ""
                    anti_spoofing_result = {}
                    
                    # Get best match
                    if len(self.known_face_encodings) > 0:
                        face_distances = face_recognition.face_distance(
                            self.known_face_encodings, face_encoding)
                        best_match_index = np.argmin(face_distances)
                        if matches[best_match_index]:
                            name = self.known_face_names[best_match_index]
                            # Get class information from database
                            if name in self.student_database:
                                class_info = self.student_database[name].get("class", "")
                            # Convert distance to confidence percentage
                            confidence = int((1 - face_distances[best_match_index]) * 100)
                            
                            # Record attendance
                            if confidence >= self.config.get("attendance_min_confidence", 85):
                                # Pass the original frame (before scaling) for saving
                                original_frame_for_attendance = frame 
                                success, message = self.attendance_manager.mark_attendance(
                                    name, 
                                    confidence,
                                    original_frame_for_attendance, # Pass the original frame here
                                    verification_method="face+rfid" if self.last_rfid_person == name else "face",
                                    class_info=class_info
                                )
                                
                                if not success:
                                    # Add attendance status to class info
                                    class_info += f" [{message}]"
                            else:
                                class_info += f" [Confidence too low: {confidence}%]"
                            
                            # Check for RFID match if available
                            if self.last_rfid_person and (time.time() - self.last_rfid_time) < self.rfid_timeout:
                                if name == self.last_rfid_person:
                                    # Add RFID verified indicator
                                    class_info += " [RFID Verified]"
                                    # Increase confidence for verified matches
                                    confidence = min(100, confidence + 10)
                    
                    # Perform anti-spoofing check if enabled
                    if self.enable_anti_spoofing:
                        # Extract face region for anti-spoofing check
                        top, right, bottom, left = face_locations[i]
                        face_img = rgb_frame[top:bottom, left:right]
                        
                        # Make sure the face image is large enough for anti-spoofing
                        if face_img.shape[0] > 20 and face_img.shape[1] > 20:
                            # Check if this is a real face or a spoofing attempt
                            is_real, real_score, spoof_metadata = self.anti_spoofing.is_real_face(face_img)
                            
                            if not is_real and confidence > 0:
                                # This is likely a spoofing attempt
                                logger.warning(f"Potential spoofing attack detected for {name}: score={real_score}")
                                
                                # Adjust confidence based on spoofing score
                                spoof_penalty = int((1 - real_score) * 50)  # Up to 50% penalty
                                confidence = max(0, confidence - spoof_penalty)
                                
                                # Add spoofing warning to class info
                                if confidence < 40:
                                    name = "Spoofing Attempt"
                                    class_info = "ALERT: Photo/Screen detected"
                                elif real_score < 0.3:
                                    class_info += " [SPOOFING SUSPECTED]"
                            
                            # Add anti-spoofing results to metadata
                            anti_spoofing_result = {
                                "is_real": is_real,
                                "real_score": real_score,
                                "spoof_metadata": spoof_metadata
                            }
                        
                        # Include liveness result if available
                        if liveness_result:
                            anti_spoofing_result["liveness"] = liveness_result
                    
                    face_matches.append((name, confidence, class_info, anti_spoofing_result))
                
                # Scale back up face locations
                scaled_locations = []
                for (top, right, bottom, left) in face_locations:
                    # Scale back up
                    top = int(top / scale_factor)
                    right = int(right / scale_factor)
                    bottom = int(bottom / scale_factor)
                    left = int(left / scale_factor)
                    scaled_locations.append((top, right, bottom, left))
                
                results.append((frame, scaled_locations, face_matches))
            else:
                results.append((frame, [], []))
        
        return results
    
    def verify_two_factor_auth(self, face_name: str, rfid_name: str) -> Tuple[bool, str]:
        """
        Verify two-factor authentication (face + RFID).
        
        Args:
            face_name (str): Name detected by face recognition
            rfid_name (str): Name associated with RFID card
            
        Returns:
            Tuple[bool, str]: (success, message)
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
    
    def set_rfid_authentication(self, person_name: str) -> None:
        """
        Set RFID authentication for a person.
        
        Args:
            person_name (str): Person name
        """
        self.last_rfid_person = person_name
        self.last_rfid_time = time.time()
    
    def update_settings(self, settings: Dict[str, Any]) -> None:
        """
        Update face recognition settings.
        
        Args:
            settings (Dict[str, Any]): Dictionary of settings
        """
        # Update local settings
        if "detection_method" in settings:
            self.detection_method = settings["detection_method"]
        
        if "face_recognition_tolerance" in settings:
            self.face_recognition_tolerance = settings["face_recognition_tolerance"]
        
        if "batch_size" in settings:
            self.batch_size = settings["batch_size"]
        
        if "frame_skip" in settings:
            self.frame_skip = settings["frame_skip"]
        
        if "display_fps" in settings:
            self.display_fps = settings["display_fps"]
        
        if "rfid_timeout" in settings:
            self.rfid_timeout = settings["rfid_timeout"]
        
        if "enable_anti_spoofing" in settings:
            self.enable_anti_spoofing = settings["enable_anti_spoofing"]
            
        if "spoofing_detection_threshold" in settings:
            # Update anti-spoofing system settings
            self.anti_spoofing.update_settings({"spoofing_detection_threshold": settings["spoofing_detection_threshold"]})
        
        # Update config
        self.config.update(settings)
        self.config.save_config()
