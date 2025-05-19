"""
Modified main GUI window to include anti-spoofing tab.
"""

from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget, QLabel, QMessageBox
from PyQt5.QtCore import Qt

from utils.logger import logger
from gui.tabs.recognition_tab import RecognitionTab
from gui.tabs.capture_tab import CaptureTab
from gui.tabs.training_tab import TrainingTab
from gui.tabs.database_tab import DatabaseTab
from gui.tabs.rfid_tab import RFIDTab
from gui.tabs.settings_tab import SettingsTab
from gui.tabs.anti_spoofing_tab import AntiSpoofingTab
from gui.dialogs.card_dialogs import NewCardDialog, ExistingCardDialog
from threads.rfid_thread import RFIDServerThread

class FaceRecognitionGUI(QMainWindow):
    """
    Main GUI window for the face recognition system.
    
    This class is responsible for creating the main window and tabs,
    and handling the interaction between them.
    """
    
    def __init__(self, face_system):
        """
        Initialize the main window.
        
        Args:
            face_system: Face recognition system
        """
        super().__init__()
        self.face_system = face_system
        
        # RFID mode settings
        self.rfid_mode = "identify"  # Default mode: "identify" or "add_edit"
        
        # Create RFID server thread
        self.rfid_server = RFIDServerThread(face_system)
        self.rfid_server.rfid_detected.connect(self.handle_rfid_detection)
        self.rfid_server.update_status.connect(self.update_rfid_status)
        
        # Set up the main window
        self.setWindowTitle("Face Recognition System with RFID and Anti-Spoofing")
        self.setMinimumSize(1200, 800)
        
        # Create central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Create tabs
        self.recognition_tab = RecognitionTab(self.face_system)
        self.capture_tab = CaptureTab(self.face_system)
        self.training_tab = TrainingTab(self.face_system)
        self.database_tab = DatabaseTab(self.face_system)
        self.rfid_tab = RFIDTab(self.face_system, self)
        self.anti_spoofing_tab = AntiSpoofingTab(self.face_system)
        self.settings_tab = SettingsTab(self.face_system)
        
        # Add tabs to tab widget
        self.tabs.addTab(self.recognition_tab, "Face Recognition")
        self.tabs.addTab(self.capture_tab, "Capture Dataset")
        self.tabs.addTab(self.training_tab, "Train Model")
        self.tabs.addTab(self.database_tab, "Student Database")
        self.tabs.addTab(self.rfid_tab, "RFID Management")
        self.tabs.addTab(self.anti_spoofing_tab, "Anti-Spoofing")
        self.tabs.addTab(self.settings_tab, "Settings")
        
        # Create main layout and add tab widget
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        
        # Create status bar
        self.status_label = QLabel("Ready")
        self.statusBar().addWidget(self.status_label)
        
        # Set layout for central widget
        self.central_widget.setLayout(main_layout)
        
        # Set style sheet for modern look
        self.set_style_sheet()
        
        # Connect signals from tabs
        self._connect_signals()
        
        logger.info("GUI initialized")
    
    def _connect_signals(self):
        """Connect signals from tabs to handle inter-tab communication."""
        # Connect capture complete signal to training tab
        self.capture_tab.capture_completed.connect(self.handle_capture_completed)
        
        # Connect training complete signal to database tab
        self.training_tab.training_completed.connect(self.handle_training_completed)
        
        # Connect RFID mode signal from RFID tab
        self.rfid_tab.mode_changed.connect(self.set_rfid_mode)
    
    def set_style_sheet(self):
        """Set style sheet for modern look."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: #ffffff;
                border-radius: 5px;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                border: 1px solid #cccccc;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 8px 12px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                border-bottom: 1px solid #ffffff;
            }
            QPushButton {
                background-color: #4a86e8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a76d8;
            }
            QPushButton:pressed {
                background-color: #2a66c8;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #888888;
            }
            QLabel {
                color: #333333;
            }
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
            }
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: #f0f0f0;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4a86e8;
                border-radius: 3px;
            }
            QTableWidget {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
                gridline-color: #e0e0e0;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #e0e0ff;
                color: black;
            }
            QHeaderView::section {
                background-color: #e0e0e0;
                padding: 6px;
                border: 1px solid #cccccc;
                border-left: none;
                border-top: none;
            }
        """)
    
    def update_status(self, message):
        """
        Update status bar message.
        
        Args:
            message (str): Status message
        """
        self.status_label.setText(message)
        logger.info(message)
    
    def update_rfid_status(self, message):
        """
        Update RFID status.
        
        Args:
            message (str): RFID status message
        """
        self.recognition_tab.update_rfid_status(message)
        self.rfid_tab.update_status(message)
        self.update_status(message)
    
    def set_rfid_mode(self, mode):
        """
        Set RFID operation mode.
        
        Args:
            mode (str): RFID mode ('identify' or 'add_edit')
        """
        self.rfid_mode = mode
        logger.info(f"RFID mode set to: {mode}")
        
        mode_text = "Identify" if mode == "identify" else "Add/Edit"
        self.update_rfid_status(f"RFID Mode: {mode_text}")
    
    def handle_rfid_detection(self, identifier, is_new_card):
        """
        Handle RFID card detection based on current mode.
        
        Args:
            identifier (str): Card ID or person name
            is_new_card (bool): True if the card is new, False if existing
        """
        if self.rfid_mode == "add_edit":
            # Add/Edit mode - show dialogs for new or existing cards
            if is_new_card:
                # This is a new card, show registration dialog
                card_id = identifier  # For new cards, identifier is the card ID
                self.handle_new_card(card_id)
            else:
                # This is an existing card, show management dialog
                person_name = identifier  # For existing cards, identifier is the person name
                card_id = self.find_card_id_by_person(person_name)
                self.handle_existing_card(card_id, person_name)
        else:
            # Identify mode - just use the card for authentication
            if not is_new_card:
                # This is an existing card, use it for authentication
                person_name = identifier  # For existing cards, identifier is the person name
                
                # Set RFID authentication in face system
                self.face_system.set_rfid_authentication(person_name)
                
                # Update RFID status in recognition tab
                self.update_rfid_status(f"RFID Card: {person_name} authenticated")
                
                # Show a small notification
                QMessageBox.information(self, "RFID Authentication", 
                                       f"Card authenticated for {person_name}")
            else:
                # This is a new card, show warning
                card_id = identifier
                QMessageBox.warning(self, "Unknown Card", 
                                   f"Card ID {card_id} is not registered in the system.\n\n"
                                   f"Switch to Add/Edit mode to register this card.")
    
    def find_card_id_by_person(self, person_name):
        """
        Find card ID by person name.
        
        Args:
            person_name (str): Person name
            
        Returns:
            str: Card ID or None if not found
        """
        for card_id, name in self.face_system.db_manager.rfid_database.items():
            if name == person_name:
                return card_id
        return None
    
    def handle_new_card(self, card_id):
        """
        Handle new RFID card detection.
        
        Args:
            card_id (str): RFID card ID
        """
        dialog = NewCardDialog(self.face_system, card_id, self)
        if dialog.exec_():
            # Register the card
            person_name = dialog.person_name
            class_name = dialog.class_name
            
            # Add card to database
            self.face_system.db_manager.add_rfid_card(card_id, person_name)
            
            # Add class information to database
            if class_name:
                self.face_system.db_manager.update_student_info(person_name, {"class": class_name})
            
            # Refresh RFID table
            self.rfid_tab.refresh_rfid_table()
            
            # If user chose to capture dataset, start capture
            if dialog.should_capture:
                # Switch to capture tab
                self.tabs.setCurrentIndex(1)  # Index 1 is the capture tab
                
                # Set person name and class in capture form
                self.capture_tab.set_person_info(person_name, class_name)
                
                # Start capture
                self.capture_tab.start_capture()
            else:
                QMessageBox.information(self, "Success", f"RFID card {card_id} registered to {person_name}")
    
    def handle_existing_card(self, card_id, person_name):
        """
        Handle existing RFID card detection.
        
        Args:
            card_id (str): RFID card ID
            person_name (str): Person name
        """
        dialog = ExistingCardDialog(self.face_system, card_id, person_name, self)
        if dialog.exec_():
            # Update class information
            new_class = dialog.class_name
            
            # Update database
            self.face_system.db_manager.update_student_info(person_name, {"class": new_class})
            
            # Refresh database table
            self.database_tab.refresh_database()
            
            # If user chose to capture more dataset, start capture
            if dialog.should_capture:
                # Switch to capture tab
                self.tabs.setCurrentIndex(1)  # Index 1 is the capture tab
                
                # Set person name and class in capture form
                self.capture_tab.set_person_info(person_name, new_class)
                
                # Start capture
                self.capture_tab.start_capture()
            else:
                QMessageBox.information(self, "Success", f"Updated information for {person_name}")
    
    def handle_capture_completed(self, success, person_name):
        """
        Handle capture completion.
        
        Args:
            success (bool): True if capture was successful
            person_name (str): Person name
        """
        if success:
            # Ask if user wants to train the model now
            reply = QMessageBox.question(
                self, "Train Model", 
                "Do you want to train the model with the new dataset now?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self.tabs.setCurrentIndex(2)  # Switch to training tab
                self.training_tab.start_training()
    
    def handle_training_completed(self, success):
        """
        Handle training completion.
        
        Args:
            success (bool): True if training was successful
        """
        if success:
            # Refresh database tab
            self.database_tab.refresh_database()
            # Refresh RFID tab person combo
            self.rfid_tab.refresh_person_combo()
    
    def closeEvent(self, event):
        """
        Handle window close event.
        
        Args:
            event: Close event
        """
        # Stop video threads in tabs
        self.recognition_tab.stop_recognition()
        self.capture_tab.stop_capture()
        
        # Stop anti-spoofing test if running
        if hasattr(self.anti_spoofing_tab, 'video_thread') and self.anti_spoofing_tab.video_thread and self.anti_spoofing_tab.video_thread.isRunning():
            self.anti_spoofing_tab.stop_live_test()
        
        # Stop RFID server
        if self.rfid_server.isRunning():
            self.rfid_server.stop()
            self.rfid_server.wait()
        
        # Check if training is in progress
        if self.training_tab.is_training:
            reply = QMessageBox.question(
                self, "Training in Progress", 
                "Training is still in progress. Do you want to wait for it to complete?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self.training_tab.wait_for_training()
        
        logger.info("Application closing")
        event.accept()