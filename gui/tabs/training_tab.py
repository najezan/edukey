"""
Training tab for model training.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                           QProgressBar, QTextEdit, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal

from threads.training_thread import TrainingThread
from utils.logger import logger

class TrainingTab(QWidget):
    """
    Tab for training the face recognition model.
    
    This tab contains controls for training the model, progress display,
    and log display.
    """
    
    # Define signals
    training_completed = pyqtSignal(bool)  # Success flag
    
    def __init__(self, face_system):
        """
        Initialize the training tab.
        
        Args:
            face_system: Face recognition system
        """
        super().__init__()
        self.face_system = face_system
        self.training_thread = None
        self.is_training = False
        
        # Initialize UI components
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()
        
        # Create information display
        self.info_label = QLabel("Click 'Start Training' to train the face recognition model")
        self.info_label.setAlignment(Qt.AlignCenter)
        
        # Create progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        # Create status display
        self.status_label = QLabel("Ready to train")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        # Create log display
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(200)
        
        # Create control button
        self.start_button = QPushButton("Start Training")
        self.start_button.clicked.connect(self.start_training)
        
        # Add widgets to layout
        layout.addWidget(self.info_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        layout.addWidget(self.log_text)
        layout.addWidget(self.start_button)
        
        # Set layout for tab
        self.setLayout(layout)
    
    def start_training(self):
        """Start model training."""
        # Check for new faces to train
        new_people = self.face_system.db_manager.get_new_persons_to_train()
        
        if not new_people:
            # Check if force training is desired even with no new people
            reply = QMessageBox.question(
                self, "No New People", 
                "No new people to train. Do you want to force re-training for all people?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        # Disable training button
        self.start_button.setEnabled(False)
        self.is_training = True
        
        # Reset progress bar and log
        self.progress_bar.setValue(0)
        self.log_text.clear()
        
        # Create and start training thread
        self.training_thread = TrainingThread(self.face_system)
        self.training_thread.update_status.connect(self.update_status)
        self.training_thread.update_progress.connect(self.update_progress)
        self.training_thread.training_complete.connect(self.training_complete)
        self.training_thread.start()
        
        logger.info("Model training started")
    
    def update_status(self, status):
        """
        Update status message and log.
        
        Args:
            status (str): Status message
        """
        self.status_label.setText(status)
        self.log_text.append(status)
        
        # Scroll to bottom of log
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
        
        logger.info(status)
    
    def update_progress(self, value):
        """
        Update progress bar.
        
        Args:
            value (int): Progress value (0-100)
        """
        self.progress_bar.setValue(value)
    
    def training_complete(self, success):
        """
        Handle training completion.
        
        Args:
            success (bool): True if training completed successfully
        """
        # Enable training button
        self.start_button.setEnabled(True)
        self.is_training = False
        
        if success:
            QMessageBox.information(self, "Success", "Model training completed successfully!")
            # Emit signal for main window to handle
            self.training_completed.emit(True)
            
            logger.info("Model training completed successfully")
        else:
            QMessageBox.warning(self, "Warning", "No new faces were found to train.")
            logger.warning("No new faces were found to train")
    
    def wait_for_training(self):
        """Wait for training to complete (used when closing the application)."""
        if self.training_thread and self.training_thread.isRunning():
            self.training_thread.wait()
            logger.info("Waited for training thread to complete")
