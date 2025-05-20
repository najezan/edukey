"""
Capture tab for dataset collection.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QFormLayout, QLineEdit, QProgressBar,
                           QMessageBox)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, pyqtSignal

from threads.video_thread import VideoThread
from utils.logger import logger

class CaptureTab(QWidget):
    """
    Tab for capturing face dataset.
    
    This tab contains the video display, form for person information,
    and controls for capturing face images.
    """
    
    # Define signals
    capture_completed = pyqtSignal(bool, str)  # Success flag, person name
    
    def __init__(self, face_system):
        """
        Initialize the capture tab.
        
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
        
        # Create form for person information
        form_layout = QFormLayout()
        self.person_name_input = QLineEdit()
        self.class_name_input = QLineEdit()
        # Removed self.num_images_input
        
        form_layout.addRow("Person Name:", self.person_name_input)
        form_layout.addRow("Class:", self.class_name_input)
        # Removed Number of Images row
        
        # Create video display
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setStyleSheet("border: 2px solid #cccccc; background-color: black;")
        
        # Create progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        # Create control buttons
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Capture")
        self.stop_button = QPushButton("Stop Capture")
        self.stop_button.setEnabled(False)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        
        # Connect buttons
        self.start_button.clicked.connect(self.start_capture)
        self.stop_button.clicked.connect(self.stop_capture)
        
        # Create status display
        self.status_label = QLabel("Enter person information and click Start Capture")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        # Add widgets to layout
        layout.addLayout(form_layout)
        layout.addWidget(self.video_label)
        layout.addWidget(self.progress_bar)
        layout.addLayout(button_layout)
        layout.addWidget(self.status_label)
        
        # Set layout for tab
        self.setLayout(layout)
    
    def set_person_info(self, name, class_name):
        """
        Set person information in the form.
        
        Args:
            name (str): Person name
            class_name (str): Class name
        """
        self.person_name_input.setText(name)
        self.class_name_input.setText(class_name)
    
    def start_capture(self):
        """Start dataset capture."""
        person_name = self.person_name_input.text().strip()
        class_name = self.class_name_input.text().strip()
        num_images = self.face_system.config.get("default_num_images", 500)
        
        if not person_name:
            QMessageBox.warning(self, "Warning", "Person name cannot be empty.")
            return
        
        # Check if person is already trained
        if person_name in self.face_system.trained_people:
            reply = QMessageBox.question(
                self, "Confirmation", 
                f"{person_name} is already in the trained model. Do you want to add more images?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        # Add class information to database
        if class_name:
            self.face_system.db_manager.update_student_info(person_name, {"class": class_name})
        
        # Disable start button and enable stop button
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        # Reset progress bar
        self.progress_bar.setValue(0)
        
        # Create and start video thread
        self.video_thread = VideoThread(self.face_system, mode="capture", person_name=person_name, num_images=num_images)
        self.video_thread.update_frame.connect(self.update_frame)
        self.video_thread.update_status.connect(self.update_status)
        self.video_thread.update_progress.connect(self.update_progress)
        self.video_thread.capture_complete.connect(lambda success: self.capture_complete(success, person_name))
        self.video_thread.start()
        
        logger.info(f"Dataset capture started for {person_name}")
    
    def stop_capture(self):
        """Stop dataset capture."""
        if self.video_thread and self.video_thread.isRunning():
            self.video_thread.stop()
            self.video_thread.wait()
        
        # Enable start button and disable stop button
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        # Update status
        self.update_status("Dataset capture stopped")
        
        logger.info("Dataset capture stopped")
    
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
    
    def update_progress(self, value):
        """
        Update progress bar.
        
        Args:
            value (int): Progress value (0-100)
        """
        self.progress_bar.setValue(value)
    
    def capture_complete(self, success, person_name):
        """
        Handle capture completion.
        
        Args:
            success (bool): True if capture completed successfully
            person_name (str): Person name
        """
        # Enable start button and disable stop button
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        if success:
            QMessageBox.information(self, "Success", 
                                   f"Successfully captured face dataset for {person_name}")
            
            # Emit signal for main window to handle
            self.capture_completed.emit(success, person_name)
            
            logger.info(f"Dataset capture completed for {person_name}")
