"""
Thread for video processing with PyQt signals.
"""

import os
import time
import cv2
import numpy as np
from typing import Optional
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage
from concurrent.futures import ThreadPoolExecutor

from core.video_stream import VideoStream
from utils.logger import logger

class VideoThread(QThread):
    """
    Thread for handling video processing with PyQt signals.
    
    This class handles video capture and processing in a separate thread,
    emitting signals to update the UI.
    """
    
    # Define PyQt signals
    update_frame = pyqtSignal(QImage)
    update_status = pyqtSignal(str)
    update_progress = pyqtSignal(int)
    capture_complete = pyqtSignal(bool)
    
    def __init__(self, face_system, mode: str = "recognition", person_name: Optional[str] = None):
        """
        Initialize the video thread.
        
        Args:
            face_system: Face recognition system
            mode (str): Operation mode ('recognition' or 'capture')
            person_name (Optional[str]): Person name for capture mode
        """
        super().__init__()
        self.face_system = face_system
        self.mode = mode
        self.person_name = person_name
        self.running = False
        
    def run(self):
        """Run the thread based on the selected mode."""
        self.running = True
        
        if self.mode == "capture":
            self.capture_dataset()
        elif self.mode == "recognition":
            self.recognize_faces()
    
    def stop(self):
        """Stop the thread."""
        self.running = False
    
    def capture_dataset(self):
        """Capture face dataset in a thread."""
        # Create directory for this person if it doesn't exist
        person_dir = os.path.join(self.face_system.db_manager.dataset_dir, self.person_name)
        if not os.path.exists(person_dir):
            os.makedirs(person_dir)
        
        # Initialize video stream
        self.update_status.emit("Starting video stream...")
        vs = VideoStream(src=0, width=1280, height=720).start()
        time.sleep(2.0)  # Allow camera to warm up
        
        self.update_status.emit(f"Capturing face dataset for {self.person_name}")
        
        count = 0
        start_time = time.time()
        fps_counter = 0
        fps = 0
        
        # Use a queue to process frames in parallel for higher FPS
        process_queue = []
        
        while self.running and count < 500:
            # Read frame from threaded video stream
            frame = vs.read()
            if frame is None:
                self.update_status.emit("Failed to grab frame")
                break
                
            # Mirror the image (more intuitive for user)
            frame = cv2.flip(frame, 1)
            
            # Calculate FPS
            fps_counter += 1
            if time.time() - start_time >= 1.0:
                fps = fps_counter
                fps_counter = 0
                start_time = time.time()
            
            # Convert BGR to RGB (face_recognition uses RGB)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Use smaller detection frame for faster processing during capture
            detection_frame = cv2.resize(rgb_frame, (0, 0), fx=0.5, fy=0.5)
            
            # Detect faces - use CNN if GPU available for better accuracy
            face_locations = face_recognition.face_locations(detection_frame, model=self.face_system.detection_method)
            
            # Scale back face locations to original frame size
            scaled_face_locations = []
            for (top, right, bottom, left) in face_locations:
                # Scale back up
                top *= 2
                right *= 2
                bottom *= 2
                left *= 2
                scaled_face_locations.append((top, right, bottom, left))
            
            for (top, right, bottom, left) in scaled_face_locations:
                # Draw rectangle around face
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                
                count += 1
                
                # Save the captured face with GPU-accelerated resize
                img_name = os.path.join(person_dir, f"{self.person_name}_{count}.jpg")
                face_img = frame[top:bottom, left:right]
                
                # Thread the writing of images to avoid slowing down capture
                process_queue.append((img_name, face_img.copy()))
                
                # Only process the queue when it's large enough
                if len(process_queue) >= 5:
                    # Use thread to save images without blocking
                    def save_images(queue):
                        for img_path, img in queue:
                            cv2.imwrite(img_path, img)
                    
                    Thread(target=save_images, args=(process_queue.copy(),)).start()
                    process_queue = []
                
                # Display count on the image
                cv2.putText(frame, f"Captures: {count}/500", (30, 50), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                # Display progress bar
                progress = int((count / 500) * 200)  # 200px wide progress bar
                cv2.rectangle(frame, (30, 70), (30 + progress, 90), (0, 255, 0), -1)
                cv2.rectangle(frame, (30, 70), (230, 90), (255, 255, 255), 2)
            
            # Show FPS on frame
            cv2.putText(frame, f"FPS: {fps}", (frame.shape[1] - 160, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Display GPU/CPU mode
            mode = "GPU" if self.face_system.is_cuda_available() else "CPU"
            cv2.putText(frame, f"Mode: {mode}", (frame.shape[1] - 160, 60), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Convert to Qt format for display
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            # Emit signal to update UI
            self.update_frame.emit(qt_image)
            self.update_progress.emit(int((count / 500) * 100))
            
            # Sleep to control frame rate
            time.sleep(0.01)
        
        # Process any remaining images in the queue
        if process_queue:
            for img_path, img in process_queue:
                cv2.imwrite(img_path, img)
        
        self.update_status.emit(f"Captured {count} face samples for {self.person_name}")
        vs.stop()
        self.capture_complete.emit(True)
    
    def recognize_faces(self):
        """Recognize faces in real-time from webcam."""
        if not self.face_system.known_face_encodings:
            self.update_status.emit("No trained faces in the database. Please capture and train first.")
            self.capture_complete.emit(False)
            return
        
        # Initialize video stream
        self.update_status.emit("Starting video stream...")
        vs = VideoStream(src=0, width=1280, height=720).start()
        time.sleep(2.0)  # Allow camera to warm up
        
        self.update_status.emit("Face recognition started")
        
        # Set frame downscale factor based on GPU capability
        downscale_factor = 0.5 if self.face_system.is_cuda_available() else 0.25
        
        # For FPS calculation
        fps_start = time.time()
        fps_counter = 0
        fps = 0
        
        # Initialize batch processing
        batch_size = self.face_system.batch_size  # Higher batch size for GPU
        frames_to_process = []
        
        # Create thread pool for parallel processing
        with ThreadPoolExecutor(max_workers=self.face_system.batch_size) as executor:
            while self.running:
                loop_start = time.time()
                
                # Read frame from threaded video stream
                frame = vs.read()
                if frame is None:
                    break
                    
                # Mirror the image
                frame = cv2.flip(frame, 1)
                
                # Calculate FPS
                fps_counter += 1
                if (time.time() - fps_start) >= 1.0:
                    fps = fps_counter
                    fps_counter = 0
                    fps_start = time.time()
                
                # Skip processing if we already have enough frames
                if len(frames_to_process) < batch_size:
                    # Resize frame for faster processing
                    small_frame = cv2.resize(frame, (0, 0), fx=downscale_factor, fy=downscale_factor)
                    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                    frames_to_process.append((frame.copy(), rgb_small_frame, downscale_factor))
                
                # Process batches when we have enough frames or on every Nth frame
                if len(frames_to_process) >= batch_size or fps_counter % self.face_system.frame_skip == 0:
                    # Use GPU-accelerated batch processing
                    # Submit batch processing job
                    batch_future = executor.submit(self.face_system.process_face_recognition_batch, frames_to_process)
                    
                    # Get results and update display
                    for processed_frame, face_locations, face_matches in batch_future.result():
                        # Display the results
                        for (top, right, bottom, left), (name, confidence, class_info) in zip(face_locations, face_matches):
                            # Draw face box
                            if name == "Unknown" or confidence < 60:
                                color = (0, 0, 255)  # Red for unknown
                            else:
                                color = (0, 255, 0)  # Green for known
                            
                            cv2.rectangle(processed_frame, (left, top), (right, bottom), color, 2)
                            
                            # Draw name and class label
                            if name != "Unknown":
                                # Display name
                                cv2.putText(processed_frame, f"{name}", (left + 6, bottom - 26), 
                                            cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)
                                
                                # Display class information
                                if class_info:
                                    cv2.putText(processed_frame, f"Class: {class_info}", (left + 6, bottom - 6), 
                                                cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
                                
                                # Display confidence
                                cv2.putText(processed_frame, f"{confidence}%", (left + 6, top - 6),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)
                            else:
                                # Just display "Unknown" for unrecognized faces
                                cv2.putText(processed_frame, "Unknown", (left + 6, bottom - 6), 
                                            cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)
                        
                        # Show FPS counter and processing info
                        cv2.putText(processed_frame, f"FPS: {fps}", (processed_frame.shape[1] - 160, 30), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        
                        # Display GPU/CPU mode
                        mode = "GPU" if self.face_system.is_cuda_available() else "CPU"
                        cv2.putText(processed_frame, f"Mode: {mode}", (processed_frame.shape[1] - 160, 60), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        
                        # Display batch size
                        cv2.putText(processed_frame, f"Batch: {batch_size}", (processed_frame.shape[1] - 160, 90), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        
                        # Convert to Qt format for display
                        rgb_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                        h, w, ch = rgb_frame.shape
                        bytes_per_line = ch * w
                        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                        
                        # Emit signal to update UI
                        self.update_frame.emit(qt_image)
                    
                    # Clear processed frames
                    frames_to_process = []
                else:
                    # Show FPS counter on current frame
                    cv2.putText(frame, f"FPS: {fps}", (frame.shape[1] - 160, 30), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    
                    # Display GPU/CPU mode
                    mode = "GPU" if self.face_system.is_cuda_available() else "CPU"
                    cv2.putText(frame, f"Mode: {mode}", (frame.shape[1] - 160, 60), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    
                    # Convert to Qt format for display
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w, ch = rgb_frame.shape
                    bytes_per_line = ch * w
                    qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                    
                    # Emit signal to update UI
                    self.update_frame.emit(qt_image)
                
                # Calculate loop time and dynamically adjust batch size
                loop_time = time.time() - loop_start
                if self.face_system.is_cuda_available() and loop_time < 0.01:  # If processing is fast, increase batch size
                    batch_size = min(32, batch_size + 1)
                elif loop_time > 0.05:  # If processing is slow, decrease batch size
                    batch_size = max(4, batch_size - 1)
                
                # Sleep to control frame rate
                time.sleep(0.01)
        
        vs.stop()
        self.capture_complete.emit(True)
