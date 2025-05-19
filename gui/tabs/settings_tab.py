"""
Modified settings tab to include anti-spoofing controls.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
                           QLabel, QComboBox, QSpinBox, QDoubleSpinBox, 
                           QCheckBox, QPushButton, QGroupBox, QMessageBox)
from PyQt5.QtCore import Qt

from utils.logger import logger

class SettingsTab(QWidget):
    """
    Tab for configuring system settings.
    
    This tab contains controls for configuring detection, recognition,
    performance, anti-spoofing and RFID settings.
    """
    
    def __init__(self, face_system):
        """
        Initialize the settings tab.
        
        Args:
            face_system: Face recognition system
        """
        super().__init__()
        self.face_system = face_system
        
        # Initialize UI components
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()
        
        # Create settings groups
        detection_group = QGroupBox("Face Detection Settings")
        recognition_group = QGroupBox("Face Recognition Settings")
        performance_group = QGroupBox("Performance Settings")
        anti_spoofing_group = QGroupBox("Anti-Spoofing Settings")
        rfid_group = QGroupBox("RFID Settings")
        
        # Create detection settings
        detection_layout = QFormLayout()
        self.detection_method_combo = QComboBox()
        self.detection_method_combo.addItems(["hog", "cnn"])
        self.detection_method_combo.setCurrentText(self.face_system.detection_method)
        
        detection_layout.addRow("Detection Method:", self.detection_method_combo)
        detection_group.setLayout(detection_layout)
        
        # Create recognition settings
        recognition_layout = QFormLayout()
        self.recognition_tolerance = QDoubleSpinBox()
        self.recognition_tolerance.setRange(0.1, 1.0)
        self.recognition_tolerance.setSingleStep(0.05)
        self.recognition_tolerance.setValue(self.face_system.face_recognition_tolerance)
        
        recognition_layout.addRow("Recognition Tolerance:", self.recognition_tolerance)
        recognition_group.setLayout(recognition_layout)
        
        # Create performance settings
        performance_layout = QFormLayout()
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(1, 32)
        self.batch_size_spin.setValue(self.face_system.batch_size)
        
        self.frame_skip_spin = QSpinBox()
        self.frame_skip_spin.setRange(1, 10)
        self.frame_skip_spin.setValue(self.face_system.frame_skip)
        
        self.display_fps_check = QCheckBox()
        self.display_fps_check.setChecked(self.face_system.display_fps)
        
        performance_layout.addRow("Batch Size:", self.batch_size_spin)
        performance_layout.addRow("Frame Skip:", self.frame_skip_spin)
        performance_layout.addRow("Display FPS:", self.display_fps_check)
        performance_group.setLayout(performance_layout)
        
        # Create anti-spoofing settings
        anti_spoofing_layout = QFormLayout()
        
        self.enable_anti_spoofing_check = QCheckBox()
        self.enable_anti_spoofing_check.setChecked(self.face_system.enable_anti_spoofing)
        
        self.spoofing_threshold_spin = QDoubleSpinBox()
        self.spoofing_threshold_spin.setRange(0.1, 1.0)
        self.spoofing_threshold_spin.setSingleStep(0.05)
        self.spoofing_threshold_spin.setValue(self.face_system.anti_spoofing.spoofing_detection_threshold)
        
        anti_spoofing_layout.addRow("Enable Anti-Spoofing:", self.enable_anti_spoofing_check)
        anti_spoofing_layout.addRow("Detection Threshold:", self.spoofing_threshold_spin)
        
        # Add description
        anti_spoofing_description = QLabel(
            "Anti-spoofing uses YOLO to detect presentation attacks such as\n"
            "printed photos, digital screens, and other spoofing methods.\n"
            "Higher threshold means stricter detection but may cause false positives."
        )
        anti_spoofing_description.setWordWrap(True)
        anti_spoofing_layout.addRow(anti_spoofing_description)
        
        anti_spoofing_group.setLayout(anti_spoofing_layout)
        
        # Create RFID settings
        rfid_layout = QFormLayout()
        self.rfid_port_spin = QSpinBox()
        self.rfid_port_spin.setRange(1024, 65535)
        self.rfid_port_spin.setValue(self.face_system.config.get("rfid_port", 8080))
        
        self.rfid_timeout_spin = QSpinBox()
        self.rfid_timeout_spin.setRange(5, 300)
        self.rfid_timeout_spin.setValue(self.face_system.rfid_timeout)
        self.rfid_timeout_spin.setSuffix(" seconds")
        
        rfid_layout.addRow("RFID Server Port:", self.rfid_port_spin)
        rfid_layout.addRow("RFID Authentication Timeout:", self.rfid_timeout_spin)
        rfid_group.setLayout(rfid_layout)
        
        # Create system info display
        system_info_group = QGroupBox("System Information")
        system_info_layout = QVBoxLayout()
        
        gpu_status = "Available" if self.face_system.is_cuda_available() else "Not Available"
        anti_spoofing_status = "Enabled" if self.face_system.enable_anti_spoofing else "Disabled"
        yolo_status = "Loaded" if hasattr(self.face_system.anti_spoofing, 'yolo_model') and self.face_system.anti_spoofing.yolo_model is not None else "Not Loaded"
        
        system_info_text = f"""
        <b>GPU Acceleration:</b> {gpu_status}
        <b>CPU Cores:</b> {self.face_system.n_cpu_cores}
        <b>Detection Method:</b> {self.face_system.detection_method.upper()}
        <b>Trained People:</b> {len(self.face_system.trained_people)}
        <b>Face Encodings:</b> {len(self.face_system.known_face_encodings)}
        <b>RFID Cards:</b> {len(self.face_system.db_manager.rfid_database)}
        <b>Anti-Spoofing:</b> {anti_spoofing_status}
        <b>YOLO Model:</b> {yolo_status}
        """
        
        system_info_label = QLabel(system_info_text)
        system_info_layout.addWidget(system_info_label)
        system_info_group.setLayout(system_info_layout)
        
        # Create save button
        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self.save_settings)
        
        # Add widgets to layout
        layout.addWidget(detection_group)
        layout.addWidget(recognition_group)
        layout.addWidget(performance_group)
        layout.addWidget(anti_spoofing_group)
        layout.addWidget(rfid_group)
        layout.addWidget(system_info_group)
        layout.addWidget(self.save_button)
        
        # Set layout for tab
        self.setLayout(layout)
    
    def save_settings(self):
        """Save settings."""
        # Collect settings
        settings = {
            "detection_method": self.detection_method_combo.currentText(),
            "face_recognition_tolerance": self.recognition_tolerance.value(),
            "batch_size": self.batch_size_spin.value(),
            "frame_skip": self.frame_skip_spin.value(),
            "display_fps": self.display_fps_check.isChecked(),
            "rfid_port": self.rfid_port_spin.value(),
            "rfid_timeout": self.rfid_timeout_spin.value(),
            "enable_anti_spoofing": self.enable_anti_spoofing_check.isChecked(),
            "spoofing_detection_threshold": self.spoofing_threshold_spin.value()
        }
        
        # Update face system settings
        self.face_system.update_settings(settings)
        
        # Show confirmation
        QMessageBox.information(self, "Settings Saved", "Settings have been saved successfully.")
        
        logger.info("Settings saved")