"""
Modified settings tab to include anti-spoofing controls.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
                           QLabel, QComboBox, QSpinBox, QDoubleSpinBox, 
                           QCheckBox, QPushButton, QGroupBox, QMessageBox, QTimeEdit,
                           QScrollArea)
from PyQt5.QtCore import Qt, QTime

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
        
        # Create camera settings
        camera_group = QGroupBox("Camera Settings")
        camera_layout = QFormLayout()
        
        self.camera_combo = QComboBox()
        self.camera_combo.addItems(["0", "1", "2", "3"])  # Common camera indices
        self.camera_combo.setCurrentText(str(self.face_system.config.get("camera_index", 0)))
        camera_layout.addRow("Camera Device:", self.camera_combo)
        camera_group.setLayout(camera_layout)
        
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
        
        # Create attendance settings
        attendance_group = QGroupBox("Attendance Settings")
        attendance_layout = QFormLayout()
        
        self.min_confidence_spin = QSpinBox()
        self.min_confidence_spin.setRange(50, 100)
        self.min_confidence_spin.setValue(int(self.face_system.config.get("attendance_min_confidence", 85)))
        self.min_confidence_spin.setSuffix("%")
        
        self.late_cutoff_time = QTimeEdit()
        self.late_cutoff_time.setDisplayFormat("HH:mm")
        cutoff_time = self.face_system.config.get("attendance_late_cutoff", "09:00")
        self.late_cutoff_time.setTime(QTime.fromString(cutoff_time, "HH:mm"))
        
        self.attendance_cooldown_spin = QSpinBox()
        self.attendance_cooldown_spin.setRange(1, 60)
        self.attendance_cooldown_spin.setValue(self.face_system.config.get("attendance_cooldown", 5))
        self.attendance_cooldown_spin.setSuffix(" minutes")
        
        attendance_layout.addRow("Minimum Recognition Confidence:", self.min_confidence_spin)
        attendance_layout.addRow("Late Cutoff Time:", self.late_cutoff_time)
        attendance_layout.addRow("Attendance Cooldown:", self.attendance_cooldown_spin)
        attendance_group.setLayout(attendance_layout)
        
        # Add widgets to layout
        layout.addWidget(detection_group)
        layout.addWidget(recognition_group)
        layout.addWidget(camera_group)
        layout.addWidget(performance_group)
        layout.addWidget(anti_spoofing_group)
        layout.addWidget(rfid_group)
        layout.addWidget(attendance_group)
        layout.addWidget(system_info_group)
        layout.addWidget(self.save_button)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Create container widget for scroll area
        container = QWidget()
        container.setLayout(layout)
        scroll.setWidget(container)
        
        # Create main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(scroll)
        
        # Set layout for tab
        self.setLayout(main_layout)
    
    def save_settings(self):
        """Save settings."""
        # Collect settings
        settings = {
            "detection_method": self.detection_method_combo.currentText(),
            "camera_index": int(self.camera_combo.currentText()),
            "face_recognition_tolerance": self.recognition_tolerance.value(),
            "batch_size": self.batch_size_spin.value(),
            "frame_skip": self.frame_skip_spin.value(),
            "display_fps": self.display_fps_check.isChecked(),
            "rfid_port": self.rfid_port_spin.value(),
            "rfid_timeout": self.rfid_timeout_spin.value(),
            "enable_anti_spoofing": self.enable_anti_spoofing_check.isChecked(),
            "spoofing_detection_threshold": self.spoofing_threshold_spin.value(),
            "attendance_min_confidence": int(self.min_confidence_spin.value()),
            "attendance_late_cutoff": self.late_cutoff_time.time().toString("HH:mm"),
            "attendance_cooldown": self.attendance_cooldown_spin.value()
        }
        
        # Update face system settings
        self.face_system.update_settings(settings)
        
        # Show confirmation
        QMessageBox.information(self, "Settings Saved", "Settings have been saved successfully.")
        
        logger.info("Settings saved")