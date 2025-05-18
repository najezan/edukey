"""
Dialog modules for RFID card management.
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                            QLabel, QLineEdit, QPushButton, QMessageBox)
from PyQt5.QtCore import Qt

class NewCardDialog(QDialog):
    """
    Dialog for registering a new RFID card and capturing dataset.
    
    This dialog is shown when a new RFID card is detected and allows the user
    to register the card and optionally capture a dataset.
    """
    
    def __init__(self, face_system, card_id, parent=None):
        """
        Initialize the dialog.
        
        Args:
            face_system: Face recognition system
            card_id (str): RFID card ID
            parent: Parent widget
        """
        super().__init__(parent)
        self.face_system = face_system
        self.card_id = card_id
        self.setWindowTitle("Register New RFID Card")
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)
        
        # Create layout
        layout = QVBoxLayout()
        
        # Card ID display
        card_id_label = QLabel(f"<b>Card ID:</b> {card_id}")
        card_id_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(card_id_label)
        
        # Create form layout for input fields
        form_layout = QFormLayout()
        
        # Create input fields
        self.name_input = QLineEdit()
        self.class_input = QLineEdit()
        
        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("Class:", self.class_input)
        
        # Add form to main layout
        layout.addLayout(form_layout)
        
        # Create buttons
        button_layout = QHBoxLayout()
        self.register_button = QPushButton("Register Card")
        self.capture_button = QPushButton("Register & Capture Dataset")
        self.cancel_button = QPushButton("Cancel")
        
        button_layout.addWidget(self.register_button)
        button_layout.addWidget(self.capture_button)
        button_layout.addWidget(self.cancel_button)
        
        # Connect buttons
        self.register_button.clicked.connect(self.register_card)
        self.capture_button.clicked.connect(self.register_and_capture)
        self.cancel_button.clicked.connect(self.reject)
        
        # Add buttons to layout
        layout.addLayout(button_layout)
        
        # Set dialog layout
        self.setLayout(layout)
    
    def register_card(self):
        """Register the card without capturing dataset."""
        name = self.name_input.text().strip()
        class_name = self.class_input.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Warning", "Name must be filled.")
            return
        
        # Store the information
        self.person_name = name
        self.class_name = class_name
        self.should_capture = False
        
        self.accept()
    
    def register_and_capture(self):
        """Register the card and capture dataset."""
        name = self.name_input.text().strip()
        class_name = self.class_input.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Warning", "Name must be filled.")
            return
        
        # Store the information
        self.person_name = name
        self.class_name = class_name
        self.should_capture = True
        
        self.accept()


class ExistingCardDialog(QDialog):
    """
    Dialog for managing an existing RFID card.
    
    This dialog is shown when an existing RFID card is detected and allows
    the user to update information or capture more dataset images.
    """
    
    def __init__(self, face_system, card_id, person_name, parent=None):
        """
        Initialize the dialog.
        
        Args:
            face_system: Face recognition system
            card_id (str): RFID card ID
            person_name (str): Person name
            parent: Parent widget
        """
        super().__init__(parent)
        self.face_system = face_system
        self.card_id = card_id
        self.person_name = person_name
        self.setWindowTitle("Manage RFID Card")
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)
        
        # Get class information
        self.class_name = ""
        if person_name in self.face_system.student_database:
            self.class_name = self.face_system.student_database[person_name].get("class", "")
        
        # Create layout
        layout = QVBoxLayout()
        
        # Card and person information
        info_layout = QVBoxLayout()
        card_id_label = QLabel(f"<b>Card ID:</b> {card_id}")
        person_label = QLabel(f"<b>Person:</b> {person_name}")
        class_label = QLabel(f"<b>Class:</b> {self.class_name}")
        
        card_id_label.setAlignment(Qt.AlignCenter)
        person_label.setAlignment(Qt.AlignCenter)
        class_label.setAlignment(Qt.AlignCenter)
        
        info_layout.addWidget(card_id_label)
        info_layout.addWidget(person_label)
        info_layout.addWidget(class_label)
        
        # Add info to main layout
        layout.addLayout(info_layout)
        
        # Create form layout for updating class
        form_layout = QFormLayout()
        self.new_class_input = QLineEdit(self.class_name)
        form_layout.addRow("Update Class:", self.new_class_input)
        
        # Add form to main layout
        layout.addLayout(form_layout)
        
        # Create buttons
        button_layout = QHBoxLayout()
        self.update_button = QPushButton("Update Information")
        self.capture_button = QPushButton("Capture More Dataset")
        self.cancel_button = QPushButton("Cancel")
        
        button_layout.addWidget(self.update_button)
        button_layout.addWidget(self.capture_button)
        button_layout.addWidget(self.cancel_button)
        
        # Connect buttons
        self.update_button.clicked.connect(self.update_info)
        self.capture_button.clicked.connect(self.capture_more)
        self.cancel_button.clicked.connect(self.reject)
        
        # Add buttons to layout
        layout.addLayout(button_layout)
        
        # Set dialog layout
        self.setLayout(layout)
    
    def update_info(self):
        """Update student information."""
        new_class = self.new_class_input.text().strip()
        
        if not new_class:
            QMessageBox.warning(self, "Warning", "Class name cannot be empty.")
            return
        
        # Store the information
        self.class_name = new_class
        self.should_capture = False
        
        self.accept()
    
    def capture_more(self):
        """Capture more dataset for this person."""
        # Store the information
        self.class_name = self.new_class_input.text().strip()
        self.should_capture = True
        
        self.accept()
