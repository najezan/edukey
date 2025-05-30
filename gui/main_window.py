"""
Modified main GUI window to use combined Student & RFID tab.
"""

from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget, QLabel, QMessageBox, QCheckBox
from PyQt5.QtCore import Qt

from utils.logger import logger
from gui.tabs.recognition_tab import RecognitionTab
from gui.tabs.capture_tab import CaptureTab
from gui.tabs.training_tab import TrainingTab
from gui.tabs.student_rfid_tab import StudentRFIDTab
from gui.tabs.anti_spoofing_tab import AntiSpoofingTab
from gui.tabs.settings_tab import SettingsTab
from gui.tabs.attendance_tab import AttendanceTab
from gui.dialogs.card_dialogs import NewCardDialog, ExistingCardDialog
from threads.rfid_thread import RFIDServerThread
from gui.tabs.asset_management_tab import AssetManagementTab

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
        self.student_rfid_tab = StudentRFIDTab(self.face_system, self)
        self.anti_spoofing_tab = AntiSpoofingTab(self.face_system)
        self.attendance_tab = AttendanceTab(self.face_system.db_manager, self)
        self.settings_tab = SettingsTab(self.face_system)
        self.asset_management_tab = AssetManagementTab(self.face_system.db_manager, self)
        
        # Add tabs to tab widget
        self.tabs.addTab(self.recognition_tab, "Face Recognition")
        self.tabs.addTab(self.capture_tab, "Capture Dataset")
        self.tabs.addTab(self.training_tab, "Train Model")
        self.tabs.addTab(self.student_rfid_tab, "Student & RFID Management")
        self.tabs.addTab(self.asset_management_tab, "Asset Management")
        self.tabs.addTab(self.anti_spoofing_tab, "Anti-Spoofing")
        self.tabs.addTab(self.attendance_tab, "Attendance")
        self.tabs.addTab(self.settings_tab, "Settings")
        
        # Now connect RFID server signals (after self.student_rfid_tab is created)
        self.rfid_server.rfid_detected.connect(self.student_rfid_tab.handle_rfid_detection)
        self.rfid_server.rfid_detected.connect(self.asset_management_tab.handle_rfid_detected)
        self.rfid_server.update_status.connect(self.update_rfid_status)
        
        # Create main layout and add tab widget
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        
        # Create status bar
        self.status_label = QLabel("Ready")
        self.statusBar().addWidget(self.status_label)
        
        # Add dark mode toggle
        self.dark_mode_checkbox = QCheckBox("Dark Mode")
        self.dark_mode_checkbox.setChecked(False)
        self.dark_mode_checkbox.stateChanged.connect(self.toggle_dark_mode)
        self.statusBar().addPermanentWidget(self.dark_mode_checkbox)
        
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
        self.student_rfid_tab.mode_changed.connect(self.set_rfid_mode)
    
    def set_style_sheet(self, dark_mode=False):
        """Set style sheet for modern or dark look."""
        if dark_mode:
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #232629;
                }
                QTabWidget::pane {
                    border: 1px solid #444;
                    background-color: #232629;
                    border-radius: 5px;
                }
                QTabBar::tab {
                    background-color: #2d2f31;
                    border: 1px solid #444;
                    border-bottom: none;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                    padding: 8px 12px;
                    margin-right: 2px;
                    color: #e0e0e0;
                }
                QTabBar::tab:selected {
                    background-color: #232629;
                    border-bottom: 1px solid #232629;
                    color: #fff;
                }
                QPushButton {
                    background-color: #3a76d8;
                    color: #fff;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    background-color: #295bb5;
                }
                QPushButton:pressed {
                    background-color: #1a3d7a;
                }
                QPushButton:disabled {
                    background-color: #444;
                    color: #888;
                }
                QLabel, QGroupBox, QCheckBox, QRadioButton, QAbstractItemView, QMenuBar, QMenu, QStatusBar {
                    color: #e0e0e0;
                }
                QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit {
                    border: 1px solid #444;
                    border-radius: 4px;
                    padding: 6px;
                    background-color: #2d2f31;
                    color: #e0e0e0;
                    selection-background-color: #3a76d8;
                    selection-color: #fff;
                }
                QProgressBar {
                    border: 1px solid #444;
                    border-radius: 4px;
                    background-color: #232629;
                    text-align: center;
                    color: #e0e0e0;
                }
                QProgressBar::chunk {
                    background-color: #3a76d8;
                    border-radius: 3px;
                }
                QTableWidget, QTableView {
                    border: 1px solid #444;
                    border-radius: 4px;
                    background-color: #232629;
                    gridline-color: #444;
                    color: #e0e0e0;
                    selection-background-color: #3a76d8;
                    selection-color: #fff;
                    alternate-background-color: #282b30;
                }
                QTableWidget::item, QTableView::item {
                    padding: 4px;
                }
                QTableWidget::item:selected, QTableView::item:selected {
                    background-color: #3a76d8;
                    color: #fff;
                }
                QHeaderView::section {
                    background-color: #2d2f31;
                    padding: 6px;
                    border: 1px solid #444;
                    border-left: none;
                    border-top: none;
                    color: #e0e0e0;
                }
                QScrollBar:vertical, QScrollBar:horizontal {
                    background: #232629;
                }
            """)
        else:
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
                    color: #222;
                }
                QTabBar::tab:selected {
                    background-color: #ffffff;
                    border-bottom: 1px solid #ffffff;
                    color: #111;
                }
                QPushButton {
                    background-color: #4a86e8;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
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
                QLabel, QGroupBox, QCheckBox, QRadioButton, QAbstractItemView, QMenuBar, QMenu, QStatusBar {
                    color: #222;
                }
                QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit {
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    padding: 6px;
                    background-color: white;
                    color: #222;
                    selection-background-color: #4a86e8;
                    selection-color: #fff;
                }
                QProgressBar {
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    background-color: #f0f0f0;
                    text-align: center;
                    color: #222;
                }
                QProgressBar::chunk {
                    background-color: #4a86e8;
                    border-radius: 3px;
                }
                QTableWidget, QTableView {
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    background-color: white;
                    gridline-color: #e0e0e0;
                    color: #222;
                    selection-background-color: #e0e0ff;
                    selection-color: #111;
                    alternate-background-color: #f5f5f5;
                }
                QTableWidget::item, QTableView::item {
                    padding: 4px;
                }
                QTableWidget::item:selected, QTableView::item:selected {
                    background-color: #e0e0ff;
                    color: #111;
                }
                QHeaderView::section {
                    background-color: #e0e0e0;
                    padding: 6px;
                    border: 1px solid #cccccc;
                    border-left: none;
                    border-top: none;
                    color: #222;
                }
                QScrollBar:vertical, QScrollBar:horizontal {
                    background: #f0f0f0;
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
        self.student_rfid_tab.update_status(message)
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
            self.student_rfid_tab.refresh_database()
            # Refresh RFID tab person combo
            self.student_rfid_tab.refresh_person_combo()
    
    def toggle_dark_mode(self, state):
        self.set_style_sheet(dark_mode=bool(state))
    
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