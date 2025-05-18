"""
Settings tab for configuring the face recognition system.
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
    performance, and RFID settings.
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
        
        system_info_text = f"""
        <b>GPU Acceleration:</b> {gpu_status}
        <b>CPU Cores:</b> {self.face_system.n_cpu_cores}
        <b>Detection Method:</b> {self.face_system.detection_method.upper()}
        <b>Trained People:</b> {len(self.face_system.trained_people)}
        <b>Face Encodings:</b> {len(self.face_system.known_face_encodings)}
        <b>RFID Cards:</b> {len(self.face_system.db_manager.rfid_database)}
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
            "rfid_timeout": self.rfid_timeout_spin.value()
        }
        
        # Update face system settings
        self.face_system.update_settings(settings)
        
        # Show confirmation
        QMessageBox.information(self, "Settings Saved", "Settings have been saved successfully.")
        
        logger.info("Settings saved")
