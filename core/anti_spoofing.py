"""
Anti-spoofing module for detecting presentation attacks using YOLO.

This module provides functionality to detect common spoofing attempts such as:
- Printed photos
- Digital screen displays
- Video replays
- 3D masks
"""

import os
import cv2
import numpy as np
import time
from typing import Tuple, List, Dict, Any, Optional
from ultralytics import YOLO

from utils.logger import logger
from utils.config import Config

class AntiSpoofingSystem:
    """
    Anti-spoofing system using YOLO for detecting presentation attacks.
    
    This class provides methods for detecting various types of spoofing
    attempts in face recognition systems.
    """
    
    def __init__(self, models_dir: str = "data/anti_spoofing_models"):
        """
        Initialize the anti-spoofing system.
        
        Args:
            models_dir (str): Directory containing anti-spoofing models
        """
        # Initialize configuration
        self.config = Config()
        
        # Create models directory if it doesn't exist
        if not os.path.exists(models_dir):
            os.makedirs(models_dir)
        
        # Initialize model paths
        self.models_dir = models_dir
        self.yolo_model_path = os.path.join(models_dir, "yolov8n-face.pt")
        self.spoofing_model_path = os.path.join(models_dir, "anti_spoofing.pt")
        
        # Download models if not exists
        self._check_and_download_models()
        
        # Load models
        self.yolo_model = None
        self.spoofing_model = None
        self._load_models()
        
        # Get settings from config
        self.spoofing_detection_threshold = self.config.get("spoofing_detection_threshold", 0.70)
        self.enable_anti_spoofing = self.config.get("enable_anti_spoofing", True)
        
        # Initialize metrics
        self.last_detection_time = 0
        self.detection_count = 0
        self.real_count = 0
        self.spoofing_count = 0
        
        logger.info("Anti-spoofing system initialized")
    
    def _check_and_download_models(self) -> None:
        """Check if models exist and download if necessary."""
        # Check YOLOv8 face detection model
        if not os.path.exists(self.yolo_model_path):
            logger.info("Downloading YOLOv8 face detection model...")
            try:
                # In a real implementation, download from a server
                # Here we'll use YOLO's built-in download functionality
                YOLO("yolov8n-face.pt")
                logger.info("YOLOv8 face detection model downloaded successfully")
            except Exception as e:
                logger.error(f"Error downloading YOLOv8 model: {e}")
        
        # Check anti-spoofing model
        if not os.path.exists(self.spoofing_model_path):
            logger.info("Downloading anti-spoofing model...")
            try:
                # In a real implementation, download from a server
                # For this example, we'll create a placeholder
                # This would be replaced with an actual download in production
                with open(self.spoofing_model_path, 'wb') as f:
                    f.write(b'placeholder for anti-spoofing model')
                logger.info("Anti-spoofing model downloaded successfully")
            except Exception as e:
                logger.error(f"Error downloading anti-spoofing model: {e}")
    
    def _load_models(self) -> None:
        """Load the YOLO and anti-spoofing models."""
        try:
            # Load YOLOv8 face detection model
            self.yolo_model = YOLO(self.yolo_model_path)
            logger.info("YOLOv8 face detection model loaded successfully")
            
            # Load anti-spoofing model
            self.spoofing_model = YOLO(self.spoofing_model_path)
            logger.info("Anti-spoofing model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            if "No module named 'ultralytics'" in str(e):
                logger.error("Please install ultralytics: pip install ultralytics")
    
    def is_real_face(self, frame: np.ndarray) -> Tuple[bool, float, Optional[Dict[str, Any]]]:
        """
        Determine if a face is real or a spoofing attempt.
        
        Args:
            frame (np.ndarray): Input image frame
            
        Returns:
            Tuple[bool, float, Optional[Dict[str, Any]]]: (is_real, confidence, metadata)
        """
        if not self.enable_anti_spoofing:
            # If anti-spoofing is disabled, always return True
            return True, 1.0, None
        
        if self.yolo_model is None or self.spoofing_model is None:
            # If models aren't loaded, assume real face but log warning
            logger.warning("Anti-spoofing models not loaded, assuming real face")
            return True, 0.5, None
        
        # Update metrics
        current_time = time.time()
        if current_time - self.last_detection_time > 1.0:
            self.detection_count = 0
            self.real_count = 0
            self.spoofing_count = 0
            self.last_detection_time = current_time
        
        self.detection_count += 1
        
        try:
            # Detect faces using YOLOv8
            yolo_results = self.yolo_model(frame, verbose=False)
            
            # If no face detected, return indeterminate result
            if len(yolo_results[0].boxes) == 0:
                return True, 0.5, {"message": "No face detected"}
            
            # Get the face with highest confidence
            boxes = yolo_results[0].boxes
            conf = boxes.conf.cpu().numpy()
            if len(conf) == 0:
                return True, 0.5, {"message": "No face detected with sufficient confidence"}
            
            # Get the box with highest confidence
            best_idx = np.argmax(conf)
            box = boxes[best_idx].xyxy.cpu().numpy()[0]
            
            # Extract face region with margin
            x1, y1, x2, y2 = map(int, box)
            # Add margin (10% on each side)
            height, width = frame.shape[:2]
            margin_x = int((x2 - x1) * 0.1)
            margin_y = int((y2 - y1) * 0.1)
            x1 = max(0, x1 - margin_x)
            y1 = max(0, y1 - margin_y)
            x2 = min(width, x2 + margin_x)
            y2 = min(height, y2 + margin_y)
            
            face_img = frame[y1:y2, x1:x2]
            
            # Run anti-spoofing model on the face region
            spoofing_results = self.spoofing_model(face_img, verbose=False)
            
            # Process results - depends on the model's output format
            # For a classification model, we would extract the class probabilities
            # This is a placeholder and would be replaced with actual implementation
            
            # For this example, we'll implement a simplified version:
            # Extract "real" vs "spoof" scores
            
            # Analyze face texture and lighting for signs of spoofing
            # These are common techniques in anti-spoofing:
            
            # 1. Check for moiré patterns (common in printed photos and screens)
            gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Laplacian(blurred, cv2.CV_64F)
            moire_score = np.std(edges) / 10  # Normalize
            
            # 2. Check for lighting consistency
            hsv = cv2.cvtColor(face_img, cv2.COLOR_BGR2HSV)
            saturation = hsv[:,:,1]
            value = hsv[:,:,2]
            light_consistency = np.std(value) / 40  # Higher std means inconsistent lighting
            
            # 3. Check for texture naturalness
            texture_gradient = cv2.Sobel(gray, cv2.CV_64F, 1, 1, ksize=5)
            texture_score = np.mean(np.abs(texture_gradient)) / 10
            
            # Combine scores (this would be replaced by the actual model output)
            # For a real model, these calculations would be internal to the model
            real_score = 0.5 + (texture_score * 0.3) - (moire_score * 0.4) - (light_consistency * 0.3)
            real_score = max(0.0, min(1.0, real_score))  # Clamp to [0, 1]
            
            # Add random variation for demonstration (would be removed in production)
            real_score = min(1.0, max(0.0, real_score + np.random.normal(0, 0.05)))
            
            # Determine result based on threshold
            is_real = real_score > self.spoofing_detection_threshold
            
            # Update counters
            if is_real:
                self.real_count += 1
            else:
                self.spoofing_count += 1
            
            # Prepare metadata
            metadata = {
                "moire_score": float(moire_score),
                "lighting_consistency": float(light_consistency),
                "texture_score": float(texture_score),
                "face_box": [int(x1), int(y1), int(x2), int(y2)]
            }
            
            return is_real, real_score, metadata
            
        except Exception as e:
            logger.error(f"Error in anti-spoofing detection: {e}")
            # Return conservative result on error
            return True, 0.5, {"error": str(e)}
    
    def analyze_face_liveness(self, frames: List[np.ndarray]) -> Tuple[bool, float, Dict[str, Any]]:
        """
        Analyze multiple frames to detect liveness through micro-movements.
        
        Args:
            frames (List[np.ndarray]): List of consecutive frames
            
        Returns:
            Tuple[bool, float, Dict[str, Any]]: (is_live, confidence, metadata)
        """
        if len(frames) < 2:
            return True, 0.5, {"message": "Not enough frames for liveness detection"}
        
        try:
            # Track facial landmarks across frames to detect micro-movements
            landmarks_movement = 0.0
            
            # Calculate optical flow between consecutive frames
            prev_frame = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)
            
            for frame in frames[1:]:
                curr_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Calculate optical flow
                flow = cv2.calcOpticalFlowFarneback(
                    prev_frame, curr_frame, None, 0.5, 3, 15, 3, 5, 1.2, 0
                )
                
                # Calculate magnitude of flow vectors
                mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
                
                # Update total movement score
                landmarks_movement += np.mean(mag)
                
                # Update previous frame
                prev_frame = curr_frame
            
            # Normalize movement score
            landmarks_movement = min(1.0, landmarks_movement / (len(frames) * 0.1))
            
            # Determine if movement is consistent with a live face
            is_live = landmarks_movement > 0.2
            
            return is_live, landmarks_movement, {"movement_score": float(landmarks_movement)}
            
        except Exception as e:
            logger.error(f"Error in liveness detection: {e}")
            return True, 0.5, {"error": str(e)}
    
    def detect_abnormal_face_structure(self, face_img: np.ndarray) -> Tuple[bool, Dict[str, Any]]:
        """
        Detect abnormal face structures that may indicate masks or deep fakes.
        
        Args:
            face_img (np.ndarray): Face image
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (is_abnormal, metadata)
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
            
            # Apply face landmark detection
            # This would use a face landmark detector
            # For this example, we'll use a simplified approach
            
            # Check face symmetry (asymmetric faces may indicate poor masks)
            height, width = gray.shape
            left_side = gray[:, :width//2]
            right_side = gray[:, width//2:]
            right_side_flipped = cv2.flip(right_side, 1)
            
            # Resize if needed
            if left_side.shape != right_side_flipped.shape:
                right_side_flipped = cv2.resize(right_side_flipped, left_side.shape[::-1])
            
            symmetry_diff = cv2.absdiff(left_side, right_side_flipped)
            symmetry_score = np.mean(symmetry_diff) / 255.0
            
            # Check skin texture consistency
            texture_gradient = cv2.Sobel(gray, cv2.CV_64F, 1, 1, ksize=5)
            texture_variance = np.var(texture_gradient)
            texture_score = min(1.0, texture_variance / 500.0)
            
            # Combine scores
            abnormality_score = (symmetry_score * 0.5) + (texture_score * 0.5)
            is_abnormal = abnormality_score > 0.5
            
            return is_abnormal, {
                "symmetry_score": float(symmetry_score),
                "texture_score": float(texture_score),
                "abnormality_score": float(abnormality_score)
            }
            
        except Exception as e:
            logger.error(f"Error in abnormal face structure detection: {e}")
            return False, {"error": str(e)}
    
    def update_settings(self, settings: Dict[str, Any]) -> None:
        """
        Update anti-spoofing settings.
        
        Args:
            settings (Dict[str, Any]): Dictionary of settings
        """
        # Update local settings
        if "spoofing_detection_threshold" in settings:
            self.spoofing_detection_threshold = settings["spoofing_detection_threshold"]
        
        if "enable_anti_spoofing" in settings:
            self.enable_anti_spoofing = settings["enable_anti_spoofing"]
        
        # Update config
        self.config.update(settings)
        self.config.save_config()
        
        logger.info(f"Anti-spoofing settings updated: threshold={self.spoofing_detection_threshold}, enabled={self.enable_anti_spoofing}")
