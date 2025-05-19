"""
Anti-spoofing tab for testing and managing the anti-spoofing features.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QFormLayout, QDoubleSpinBox, QCheckBox,
                           QTabWidget, QTextEdit, QProgressBar, QMessageBox,
                           QGroupBox, QComboBox, QRadioButton, QFileDialog)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, pyqtSignal, QThread

import face_recognition
import cv2
import numpy as np
from threading import Thread
import time
import os

from core.video_stream import VideoStream
from threads.video_thread import VideoThread
from utils.logger import logger

class AntiSpoofingTab(QWidget):
    """
    Tab for anti-spoofing testing and management.
    
    This tab provides controls for testing the anti-spoofing system,
    visualizing the results, and fine-tuning the detection parameters.
    """
    
    def __init__(self, face_system):
        """
        Initialize the anti-spoofing tab.
        
        Args:
            face_system: Face recognition system
        """
        super().__init__()
        self.face_system = face_system
        self.video_thread = None
        self.test_mode = "live"  # 'live' or 'image'
        
        # Initialize UI components
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()
        
        # Create tabs for different anti-spoofing functionalities
        tabs = QTabWidget()
        
        # Create tabs
        live_test_tab = self._create_live_test_tab()
        image_test_tab = self._create_image_test_tab()
        settings_tab = self._create_settings_tab()
        
        # Add tabs
        tabs.addTab(live_test_tab, "Live Testing")
        tabs.addTab(image_test_tab, "Image Testing")
        tabs.addTab(settings_tab, "Settings")
        
        # Add tabs to main layout
        layout.addWidget(tabs)
        
        # Add status display
        self.status_label = QLabel("Ready to test anti-spoofing")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Set layout
        self.setLayout(layout)
    
    def _create_live_test_tab(self):
        """Create the live testing tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Create video display
        self.live_video_label = QLabel()
        self.live_video_label.setAlignment(Qt.AlignCenter)
        self.live_video_label.setMinimumSize(640, 480)
        self.live_video_label.setStyleSheet("border: 2px solid #cccccc; background-color: black;")
        
        # Create control buttons
        button_layout = QHBoxLayout()
        self.start_live_button = QPushButton("Start Live Test")
        self.stop_live_button = QPushButton("Stop Live Test")
        self.stop_live_button.setEnabled(False)
        
        button_layout.addWidget(self.start_live_button)
        button_layout.addWidget(self.stop_live_button)
        
        # Connect buttons
        self.start_live_button.clicked.connect(self.start_live_test)
        self.stop_live_button.clicked.connect(self.stop_live_test)
        
        # Create test mode selection
        test_mode_group = QGroupBox("Test Mode")
        test_mode_layout = QVBoxLayout()
        
        self.face_only_radio = QRadioButton("Face Detection Only")
        self.anti_spoofing_radio = QRadioButton("With Anti-Spoofing")
        
        # Set default mode
        self.anti_spoofing_radio.setChecked(True)
        
        test_mode_layout.addWidget(self.face_only_radio)
        test_mode_layout.addWidget(self.anti_spoofing_radio)
        
        test_mode_group.setLayout(test_mode_layout)
        
        # Create results display
        results_group = QGroupBox("Live Test Results")
        results_layout = QVBoxLayout()
        
        self.live_results_text = QTextEdit()
        self.live_results_text.setReadOnly(True)
        
        results_layout.addWidget(self.live_results_text)
        results_group.setLayout(results_layout)
        
        # Add widgets to layout
        layout.addWidget(self.live_video_label)
        layout.addLayout(button_layout)
        layout.addWidget(test_mode_group)
        layout.addWidget(results_group)
        
        # Set tab layout
        tab.setLayout(layout)
        return tab
    
    def _create_image_test_tab(self):
        """Create the image testing tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Create image display
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(640, 480)
        self.image_label.setStyleSheet("border: 2px solid #cccccc; background-color: black;")
        
        # Create control buttons
        button_layout = QHBoxLayout()
        self.load_image_button = QPushButton("Load Image")
        self.test_image_button = QPushButton("Test Image")
        self.test_image_button.setEnabled(False)
        
        button_layout.addWidget(self.load_image_button)
        button_layout.addWidget(self.test_image_button)
        
        # Connect buttons
        self.load_image_button.clicked.connect(self.load_image)
        self.test_image_button.clicked.connect(self.test_image)
        
        # Create results display
        results_group = QGroupBox("Image Test Results")
        results_layout = QVBoxLayout()
        
        self.image_results_text = QTextEdit()
        self.image_results_text.setReadOnly(True)
        
        results_layout.addWidget(self.image_results_text)
        results_group.setLayout(results_layout)
        
        # Create threshold adjustment
        threshold_layout = QFormLayout()
        self.image_threshold_spin = QDoubleSpinBox()
        self.image_threshold_spin.setRange(0.1, 1.0)
        self.image_threshold_spin.setSingleStep(0.05)
        self.image_threshold_spin.setValue(self.face_system.anti_spoofing.spoofing_detection_threshold)
        
        threshold_layout.addRow("Detection Threshold:", self.image_threshold_spin)
        
        # Add widgets to layout
        layout.addWidget(self.image_label)
        layout.addLayout(button_layout)
        layout.addLayout(threshold_layout)
        layout.addWidget(results_group)
        
        # Set tab layout
        tab.setLayout(layout)
        return tab
    
    def _create_settings_tab(self):
        """Create the settings tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Create anti-spoofing settings
        settings_group = QGroupBox("Anti-Spoofing Settings")
        settings_layout = QFormLayout()
        
        self.enable_anti_spoofing_check = QCheckBox()
        self.enable_anti_spoofing_check.setChecked(self.face_system.enable_anti_spoofing)
        
        self.spoofing_threshold_spin = QDoubleSpinBox()
        self.spoofing_threshold_spin.setRange(0.1, 1.0)
        self.spoofing_threshold_spin.setSingleStep(0.05)
        self.spoofing_threshold_spin.setValue(self.face_system.anti_spoofing.spoofing_detection_threshold)
        
        settings_layout.addRow("Enable Anti-Spoofing:", self.enable_anti_spoofing_check)
        settings_layout.addRow("Detection Threshold:", self.spoofing_threshold_spin)
        
        # Add information about how anti-spoofing works
        info_text = """
        <b>How Anti-Spoofing Works:</b><br>
        The system uses YOLO to detect presentation attacks such as:
        <ul>
            <li>Printed photos</li>
            <li>Digital screens (phones, tablets)</li>
            <li>Video replays</li>
            <li>3D masks</li>
        </ul>
        
        <b>Detection Methods:</b><br>
        <ul>
            <li>Texture analysis: Detects moiré patterns and unnatural textures</li>
            <li>Lighting consistency: Analyzes lighting variations that differ from real faces</li>
            <li>Face structure: Evaluates 3D properties of the face</li>
            <li>Liveness detection: Tracks micro-movements in real faces</li>
        </ul>
        
        <b>Adjusting Threshold:</b><br>
        <ul>
            <li>Higher threshold: More strict detection, may have false positives</li>
            <li>Lower threshold: More lenient detection, may miss some spoofing attempts</li>
        </ul>
        """
        
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        info_label.setTextFormat(Qt.RichText)
        
        settings_layout.addRow(info_label)
        settings_group.setLayout(settings_layout)
        
        # Create model info
        model_group = QGroupBox("YOLO Model Information")
        model_layout = QVBoxLayout()
        
        # Get model information
        yolo_status = "Loaded" if hasattr(self.face_system.anti_spoofing, 'yolo_model') and self.face_system.anti_spoofing.yolo_model is not None else "Not Loaded"
        spoofing_model_status = "Loaded" if hasattr(self.face_system.anti_spoofing, 'spoofing_model') and self.face_system.anti_spoofing.spoofing_model is not None else "Not Loaded"
        
        model_info_text = f"""
        <b>YOLOv8 Face Detection Model:</b> {yolo_status}
        <b>Anti-Spoofing Model:</b> {spoofing_model_status}
        <b>Model Path:</b> {self.face_system.anti_spoofing.models_dir}
        """
        
        model_info_label = QLabel(model_info_text)
        model_info_label.setTextFormat(Qt.RichText)
        
        model_layout.addWidget(model_info_label)
        
        # Download/Update models button
        self.update_models_button = QPushButton("Download/Update Models")
        self.update_models_button.clicked.connect(self.update_models)
        model_layout.addWidget(self.update_models_button)
        
        model_group.setLayout(model_layout)
        
        # Create save button
        self.save_settings_button = QPushButton("Save Settings")
        self.save_settings_button.clicked.connect(self.save_anti_spoofing_settings)
        
        # Add widgets to layout
        layout.addWidget(settings_group)
        layout.addWidget(model_group)
        layout.addWidget(self.save_settings_button)
        
        # Set tab layout
        tab.setLayout(layout)
        return tab
    
    def update_frame(self, image):
        """
        Update video frame in the current mode.
        
        Args:
            image (QImage): Frame to display
        """
        if self.test_mode == "live":
            pixmap = QPixmap.fromImage(image)
            self.live_video_label.setPixmap(pixmap.scaled(
                self.live_video_label.width(), 
                self.live_video_label.height(), 
                Qt.KeepAspectRatio
            ))
        
    def update_status(self, status):
        """
        Update status message.
        
        Args:
            status (str): Status message
        """
        self.status_label.setText(status)
        
        # Also add to results text based on mode
        if self.test_mode == "live":
            self.live_results_text.append(status)
        else:
            self.image_results_text.append(status)
    
    def start_live_test(self):
        """Start live anti-spoofing test."""
        # Enable anti-spoofing based on radio button
        self.face_system.enable_anti_spoofing = self.anti_spoofing_radio.isChecked()
        
        # Update status
        anti_spoofing_status = "enabled" if self.face_system.enable_anti_spoofing else "disabled"
        self.update_status(f"Starting live test with anti-spoofing {anti_spoofing_status}")
        
        # Set test mode
        self.test_mode = "live"
        
        # Disable start button and enable stop button
        self.start_live_button.setEnabled(False)
        self.stop_live_button.setEnabled(True)
        
        # Clear results
        self.live_results_text.clear()
        
        # Create and start custom video thread for anti-spoofing testing
        self.video_thread = CustomVideoThread(self.face_system)
        self.video_thread.update_frame.connect(self.update_frame)
        self.video_thread.update_status.connect(self.update_status)
        self.video_thread.start()
    
    def stop_live_test(self):
        """Stop live anti-spoofing test."""
        if self.video_thread and self.video_thread.isRunning():
            self.video_thread.stop()
            self.video_thread.wait()
        
        # Enable start button and disable stop button
        self.start_live_button.setEnabled(True)
        self.stop_live_button.setEnabled(False)
        
        # Update status
        self.update_status("Live test stopped")
    
    def load_image(self):
        """Load image for anti-spoofing testing."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        
        if file_path:
            # Load image
            image = cv2.imread(file_path)
            if image is None:
                self.update_status(f"Failed to load image: {file_path}")
                return
            
            # Store image for testing
            self.test_image_path = file_path
            self.test_image_data = image
            
            # Display image
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            h, w, ch = image_rgb.shape
            bytes_per_line = ch * w
            qt_image = QImage(image_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            pixmap = QPixmap.fromImage(qt_image)
            self.image_label.setPixmap(pixmap.scaled(
                self.image_label.width(), 
                self.image_label.height(), 
                Qt.KeepAspectRatio
            ))
            
            # Enable test button
            self.test_image_button.setEnabled(True)
            
            # Update status
            self.update_status(f"Loaded image: {os.path.basename(file_path)}")
            
            # Clear results
            self.image_results_text.clear()
    
    def test_image(self):
        """Test loaded image for anti-spoofing."""
        if not hasattr(self, 'test_image_data'):
            self.update_status("No image loaded")
            return
        
        # Get current threshold
        threshold = self.image_threshold_spin.value()
        
        # Set threshold temporarily for this test
        original_threshold = self.face_system.anti_spoofing.spoofing_detection_threshold
        self.face_system.anti_spoofing.spoofing_detection_threshold = threshold
        
        # Create a copy of image for processing
        image = self.test_image_data.copy()
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Start testing in a separate thread to avoid UI freezing
        self.update_status("Analyzing image for spoofing attempts...")
        
        # Run in a separate thread
        test_thread = Thread(target=self._process_test_image, args=(image, rgb_image))
        test_thread.daemon = True
        test_thread.start()
        
        # Restore original threshold
        self.face_system.anti_spoofing.spoofing_detection_threshold = original_threshold
    
    def _process_test_image(self, image, rgb_image):
        """
        Process test image in a separate thread.
        
        Args:
            image (numpy.ndarray): BGR image
            rgb_image (numpy.ndarray): RGB image
        """
        try:
            # First detect faces using face_recognition
            face_locations = face_recognition.face_locations(rgb_image, model=self.face_system.detection_method)
            
            if not face_locations:
                self.update_status("No faces detected in the image")
                return
            
            # Create a copy to draw on
            result_image = image.copy()
            
            # Process each face
            for i, (top, right, bottom, left) in enumerate(face_locations):
                # Extract face
                face_img = rgb_image[top:bottom, left:right]
                
                # Get anti-spoofing result
                is_real, real_score, metadata = self.face_system.anti_spoofing.is_real_face(face_img)
                
                # Determine box color
                if is_real:
                    # Green for real face
                    color = (0, 255, 0)
                    result_text = f"REAL ({int(real_score*100)}%)"
                else:
                    # Red for spoofing attempt
                    color = (0, 0, 255)
                    result_text = f"FAKE ({int(real_score*100)}%)"
                
                # Draw rectangle around face
                cv2.rectangle(result_image, (left, top), (right, bottom), color, 2)
                
                # Draw result text
                cv2.putText(result_image, result_text, (left, top - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                
                # Log detailed results
                self.update_status(f"Face {i+1}: {'REAL' if is_real else 'FAKE'} - Confidence: {int(real_score*100)}%")
                
                # Log metadata
                if metadata:
                    for key, value in metadata.items():
                        if isinstance(value, float):
                            self.update_status(f"  {key}: {value:.3f}")
                        else:
                            self.update_status(f"  {key}: {value}")
            
            # Display result
            result_rgb = cv2.cvtColor(result_image, cv2.COLOR_BGR2RGB)
            h, w, ch = result_rgb.shape
            bytes_per_line = ch * w
            qt_image = QImage(result_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            pixmap = QPixmap.fromImage(qt_image)
            self.image_label.setPixmap(pixmap.scaled(
                self.image_label.width(), 
                self.image_label.height(), 
                Qt.KeepAspectRatio
            ))
            
            # Summary
            self.update_status(f"Analysis complete with threshold {self.image_threshold_spin.value()}")
            
        except Exception as e:
            self.update_status(f"Error analyzing image: {e}")
    
    def update_models(self):
        """Download or update anti-spoofing models."""
        # Confirm before downloading
        reply = QMessageBox.question(
            self, "Update Models", 
            "This will download or update the YOLO models for anti-spoofing detection. Continue?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            # Run in a separate thread to avoid UI freezing
            self.update_status("Downloading/updating models...")
            self.update_models_button.setEnabled(False)
            
            download_thread = Thread(target=self._download_models)
            download_thread.daemon = True
            download_thread.start()
    
    def _download_models(self):
        """Download models in a separate thread."""
        try:
            # Call the download method
            self.face_system.anti_spoofing._check_and_download_models()
            
            # Reload models
            self.face_system.anti_spoofing._load_models()
            
            # Update status
            self.update_status("Models updated successfully")
            
            # Update UI from main thread
            from PyQt5.QtCore import QMetaObject, Q_ARG, Qt
            QMetaObject.invokeMethod(
                self.update_models_button, "setEnabled", 
                Qt.QueuedConnection, Q_ARG(bool, True)
            )
            
        except Exception as e:
            self.update_status(f"Error updating models: {e}")
            # Re-enable button
            from PyQt5.QtCore import QMetaObject, Q_ARG, Qt
            QMetaObject.invokeMethod(
                self.update_models_button, "setEnabled", 
                Qt.QueuedConnection, Q_ARG(bool, True)
            )
    
    def save_anti_spoofing_settings(self):
        """Save anti-spoofing settings."""
        # Collect settings
        settings = {
            "enable_anti_spoofing": self.enable_anti_spoofing_check.isChecked(),
            "spoofing_detection_threshold": self.spoofing_threshold_spin.value()
        }
        
        # Update face system settings
        self.face_system.update_settings(settings)
        
        # Show confirmation
        QMessageBox.information(self, "Settings Saved", "Anti-spoofing settings have been saved successfully.")
        
        logger.info("Anti-spoofing settings saved")


class CustomVideoThread(QThread):
    """
    Custom thread for anti-spoofing testing with detailed metrics.
    """
    
    # Define PyQt signals
    update_frame = pyqtSignal(QImage)
    update_status = pyqtSignal(str)
    
    def __init__(self, face_system):
        """
        Initialize the custom video thread.
        
        Args:
            face_system: Face recognition system
        """
        super().__init__()
        self.face_system = face_system
        self.running = False
    
    def run(self):
        """Run anti-spoofing test thread."""
        self.running = True
        
        # Initialize video stream
        self.update_status.emit("Starting video stream...")
        vs = VideoStream(src=0, width=1280, height=720).start()
        time.sleep(2.0)  # Allow camera to warm up
        
        self.update_status.emit("Anti-spoofing test started")
        
        # For FPS calculation
        fps_start = time.time()
        fps_counter = 0
        fps = 0
        
        # For metrics tracking
        detections = 0
        real_faces = 0
        fake_faces = 0
        
        # Last metrics update time
        last_metrics_time = time.time()
        
        while self.running:
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
            
            # Convert BGR to RGB for face_recognition
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detect faces
            face_locations = face_recognition.face_locations(rgb_frame, model=self.face_system.detection_method)
            
            # Process faces
            for (top, right, bottom, left) in face_locations:
                # Extract face region
                face_img = rgb_frame[top:bottom, left:right]
                
                # Increment detection counter
                detections += 1
                
                # Perform anti-spoofing check if enabled
                if self.face_system.enable_anti_spoofing:
                    # Check if this is a real face or a spoofing attempt
                    is_real, real_score, metadata = self.face_system.anti_spoofing.is_real_face(face_img)
                    
                    # Update counters
                    if is_real:
                        real_faces += 1
                        # Green for real face
                        color = (0, 255, 0)
                        result_text = f"REAL: {int(real_score*100)}%"
                    else:
                        fake_faces += 1
                        # Red for fake face
                        color = (0, 0, 255)
                        result_text = f"FAKE: {int(real_score*100)}%"
                    
                    # Draw detailed metrics on frame
                    if metadata:
                        y_offset = top - 40
                        for key, value in metadata.items():
                            if isinstance(value, float) and key in ["moire_score", "lighting_consistency", "texture_score"]:
                                y_offset += 20
                                metric_text = f"{key}: {value:.2f}"
                                cv2.putText(frame, metric_text, (left, y_offset), 
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                else:
                    # No anti-spoofing, just show face detected
                    color = (0, 255, 255)
                    result_text = "FACE DETECTED"
                
                # Draw rectangle around face
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                
                # Draw result text
                cv2.putText(frame, result_text, (left, top - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
            # Show FPS counter
            cv2.putText(frame, f"FPS: {fps}", (30, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Show detection counters
            anti_spoofing_text = "Anti-Spoofing: ON" if self.face_system.enable_anti_spoofing else "Anti-Spoofing: OFF"
            cv2.putText(frame, anti_spoofing_text, (30, 60), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0) if self.face_system.enable_anti_spoofing else (0, 0, 255), 2)
            
            if self.face_system.enable_anti_spoofing:
                cv2.putText(frame, f"Real: {real_faces}, Fake: {fake_faces}", (30, 90), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            
            # Convert to Qt format for display
            rgb_frame_display = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame_display.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_frame_display.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            # Emit signal to update UI
            self.update_frame.emit(qt_image)
            
            # Periodically output metrics
            current_time = time.time()
            if current_time - last_metrics_time >= 5.0:  # Every 5 seconds
                if self.face_system.enable_anti_spoofing:
                    real_percentage = 0 if detections == 0 else (real_faces / detections) * 100
                    fake_percentage = 0 if detections == 0 else (fake_faces / detections) * 100
                    
                    self.update_status.emit(f"Metrics: {detections} detections, "
                                          f"{real_faces} real ({real_percentage:.1f}%), "
                                          f"{fake_faces} fake ({fake_percentage:.1f}%)")
                
                last_metrics_time = current_time
            
            # Sleep to control frame rate
            time.sleep(0.01)
        
        vs.stop()
        self.update_status.emit("Anti-spoofing test stopped")
    
    def stop(self):
        """Stop the thread."""
        self.running = False
