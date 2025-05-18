"""
Recognition tab for face recognition.
"""

import time
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QMessageBox)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, pyqtSignal

from threads.video_thread import VideoThread
from utils.logger import logger

class RecognitionTab(QWidget):
    """
    Tab for real-time face recognition.
    
    This tab contains the video display and controls for face recognition.
    """
    
    def __init__(self, face_system):
        """
        Initialize the recognition tab.
        
        Args:
            face_system: Face recognition system
        """
        super().__init__()
        self.face_system = face_system
        self.video_thread = None
        
        # Initialize UI components
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()
        
        # Create video display
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setStyleSheet("border: 2px solid #cccccc; background-color: black;")
        
        # Create control buttons
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Recognition")
        self.stop_button = QPushButton("Stop Recognition")
        self.stop_button.setEnabled(False)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        
        # Connect buttons
        self.start_button.clicked.connect(self.start_recognition)
        self.stop_button.clicked.connect(self.stop_recognition)
        
        # Create status display
        self.status_label = QLabel("Ready to start face recognition")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        # Create RFID status display
        self.rfid_status_label = QLabel("No RFID card detected")
        self.rfid_status_label.setAlignment(Qt.AlignCenter)
        
        # Add widgets to layout
        layout.addWidget(self.video_label)
        layout.addLayout(button_layout)
        layout.addWidget(self.status_label)
        layout.addWidget(self.rfid_status_label)
        
        # Set layout for tab
        self.setLayout(layout)
    
    def start_recognition(self):
        """Start face recognition."""
        if not self.face_system.known_face_encodings:
            QMessageBox.warning(self, "Warning", "No trained faces in the database. Please capture and train first.")
            return
        
        # Disable start button and enable stop button
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        # Create and start video thread
        self.video_thread = VideoThread(self.face_system, mode="recognition")
        self.video_thread.update_frame.connect(self.update_frame)
        self.video_thread.update_status.connect(self.update_status)
        self.video_thread.capture_complete.connect(self.recognition_complete)
        self.video_thread.start()
        
        logger.info("Face recognition started")
    
    def stop_recognition(self):
        """Stop face recognition."""
        if self.video_thread and self.video_thread.isRunning():
            self.video_thread.stop()
            self.video_thread.wait()
        
        # Enable start button and disable stop button
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        # Update status
        self.update_status("Face recognition stopped")
        
        logger.info("Face recognition stopped")
    
    def update_frame(self, image):
        """
        Update video frame.
        
        Args:
            image (QImage): Frame to display
        """
        pixmap = QPixmap.fromImage(image)
        self.video_label.setPixmap(pixmap.scaled(
            self.video_label.width(), 
            self.video_label.height(), 
            Qt.KeepAspectRatio
        ))
    
    def update_status(self, status):
        """
        Update status message.
        
        Args:
            status (str): Status message
        """
        self.status_label.setText(status)
    
    def update_rfid_status(self, status):
        """
        Update RFID status message.
        
        Args:
            status (str): RFID status message
        """
        self.rfid_status_label.setText(status)
    
    def recognition_complete(self, success):
        """
        Handle recognition completion.
        
        Args:
            success (bool): True if recognition completed successfully
        """
        # Enable start button and disable stop button
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
