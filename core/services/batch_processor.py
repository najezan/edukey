"""
Batch processing service implementation.
"""

import face_recognition
import numpy as np
import concurrent.futures
from typing import List, Tuple, Dict, Any
from core.interfaces.face_recognition_interface import IBatchProcessor
from core.services.face_detection_service import FaceDetectionService
from core.services.face_recognition_service import FaceRecognitionService
from core.services.performance_optimizer import PerformanceOptimizer
from utils.logger import logger


class BatchProcessor(IBatchProcessor):
    """
    Service responsible for batch processing operations.
    """
    
    def __init__(self, 
                 detection_service: FaceDetectionService | None = None,
                 recognition_service: FaceRecognitionService | None = None,
                 performance_optimizer: PerformanceOptimizer | None = None):
        """
        Initialize batch processor.
        
        Args:
            detection_service: Face detection service
            recognition_service: Face recognition service
            performance_optimizer: Performance optimizer service
        """
        self.detection_service = detection_service or FaceDetectionService()
        self.recognition_service = recognition_service or FaceRecognitionService()
        self.performance_optimizer = performance_optimizer or PerformanceOptimizer()
        
        # Get optimal settings
        self.optimal_settings = self.performance_optimizer.optimize_for_hardware()
        logger.info("BatchProcessor initialized with optimal settings")
    
    def process_image_batch(self, image_paths: List[str], person_name: str) -> Tuple[List[np.ndarray], List[str]]:
        """
        Process a batch of images for training.
        
        Args:
            image_paths: List of image file paths
            person_name: Name of the person in images
            
        Returns:
            Tuple of (face_encodings, person_names)
        """
        batch_encodings = []
        batch_names = []
        
        try:
            max_workers = self.performance_optimizer.get_optimal_thread_count("cpu_bound")
            
            # Use ThreadPoolExecutor for I/O bound image loading
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all image processing tasks
                future_to_path = {
                    executor.submit(self._process_single_image, img_path, person_name): img_path 
                    for img_path in image_paths
                }
                
                # Collect results
                for future in concurrent.futures.as_completed(future_to_path):
                    img_path = future_to_path[future]
                    try:
                        encoding, name = future.result()
                        if encoding is not None:
                            batch_encodings.append(encoding)
                            batch_names.append(name)
                    except Exception as e:
                        logger.error(f"Error processing image {img_path}: {e}")
            
            logger.info(f"Processed {len(batch_encodings)} images for {person_name}")
            return batch_encodings, batch_names
            
        except Exception as e:
            logger.error(f"Error in batch image processing: {e}")
            return [], []
    
    def _process_single_image(self, image_path: str, person_name: str) -> Tuple[np.ndarray | None, str | None]:
        """
        Process a single image for training.
        
        Args:
            image_path: Path to image file
            person_name: Name of the person
            
        Returns:
            Tuple of (face_encoding, person_name) or (None, None) if failed
        """
        try:
            # Load image
            image = face_recognition.load_image_file(image_path)
            
            # Detect faces
            face_locations = self.detection_service.detect_faces(image)
            
            if len(face_locations) > 0:
                # Get face encodings
                face_encodings = self.recognition_service.encode_faces(image, face_locations)
                
                if face_encodings:
                    return face_encodings[0], person_name
            
            return None, None
            
        except Exception as e:
            logger.error(f"Error processing single image {image_path}: {e}")
            return None, None
    
    def process_frame_batch(self, frames: List[np.ndarray]) -> List[Dict[str, Any]]:
        """
        Process a batch of frames for recognition.
        
        Args:
            frames: List of image frames
            
        Returns:
            List of recognition results
        """
        results = []
        
        try:
            batch_size = self.performance_optimizer.get_recommended_batch_size("recognition")
            
            # Process frames in smaller batches for memory efficiency
            for i in range(0, len(frames), batch_size):
                batch = frames[i:i + batch_size]
                batch_results = self._process_frame_sub_batch(batch)
                results.extend(batch_results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch frame processing: {e}")
            return []
    
    def _process_frame_sub_batch(self, frames: List[np.ndarray]) -> List[Dict[str, Any]]:
        """
        Process a sub-batch of frames.
        
        Args:
            frames: List of frames to process
            
        Returns:
            List of recognition results
        """
        results = []
        
        try:
            for frame in frames:
                # Detect faces
                face_locations = self.detection_service.detect_faces(frame, scale_factor=0.25)
                
                frame_result = {
                    "frame": frame,
                    "face_locations": face_locations,
                    "recognitions": []
                }
                
                if face_locations:
                    # Get face encodings
                    face_encodings = self.recognition_service.encode_faces(frame, face_locations)
                    
                    # Recognize each face
                    for i, face_encoding in enumerate(face_encodings):
                        name, confidence = self.recognition_service.recognize_face(face_encoding)
                        
                        recognition_result = {
                            "face_index": i,
                            "name": name,
                            "confidence": confidence,
                            "location": face_locations[i] if i < len(face_locations) else None
                        }
                        
                        frame_result["recognitions"].append(recognition_result)
                
                results.append(frame_result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing frame sub-batch: {e}")
            return []
    
    def process_training_batch(self, dataset_dir: str, person_names: List[str]) -> Tuple[List[np.ndarray], List[str]]:
        """
        Process a complete training batch from dataset directory.
        
        Args:
            dataset_dir: Path to dataset directory
            person_names: List of person names to process
            
        Returns:
            Tuple of (all_encodings, all_names)
        """
        all_encodings = []
        all_names = []
        
        try:
            import os
            
            for person_name in person_names:
                person_dir = os.path.join(dataset_dir, person_name)
                if not os.path.exists(person_dir):
                    logger.warning(f"Person directory not found: {person_dir}")
                    continue
                
                # Get all image files
                image_files = []
                for ext in ['.jpg', '.jpeg', '.png', '.bmp']:
                    image_files.extend([
                        os.path.join(person_dir, f) 
                        for f in os.listdir(person_dir) 
                        if f.lower().endswith(ext)
                    ])
                
                if image_files:
                    # Process images for this person
                    person_encodings, person_names_list = self.process_image_batch(image_files, person_name)
                    all_encodings.extend(person_encodings)
                    all_names.extend(person_names_list)
            
            logger.info(f"Training batch processed: {len(all_encodings)} total encodings")
            return all_encodings, all_names
            
        except Exception as e:
            logger.error(f"Error processing training batch: {e}")
            return [], []