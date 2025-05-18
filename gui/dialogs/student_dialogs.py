"""
Dialog modules for student information management.
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                            QLabel, QLineEdit, QPushButton, QMessageBox, QComboBox)

class StudentInfoDialog(QDialog):
    """
    Dialog for updating student information.
    
    This dialog allows the user to update student information such as class.
    """
    
    def __init__(self, face_system, parent=None):
        """
        Initialize the dialog.
        
        Args:
            face_system: Face recognition system
            parent: Parent widget
        """
        super().__init__(parent)
        self.face_system = face_system
        self.setWindowTitle("Update Student Information")
        self.setMinimumWidth(400)
        
        # Create layout
        layout = QVBoxLayout()
        
        # Create form layout for student selection
        form_layout = QFormLayout()
        
        # Create student selection combo box
        self.student_combo = QComboBox()
        self.student_combo.addItems(sorted(list(self.face_system.trained_people)))
        form_layout.addRow("Select Student:", self.student_combo)
        
        # Create class input field
        self.class_input = QLineEdit()
        form_layout.addRow("Class:", self.class_input)
        
        # Add form to main layout
        layout.addLayout(form_layout)
        
        # Connect student selection to update class field
        self.student_combo.currentTextChanged.connect(self.update_class_field)
        
        # Create buttons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        # Connect buttons
        self.save_button.clicked.connect(self.save_info)
        self.cancel_button.clicked.connect(self.reject)
        
        # Add buttons to layout
        layout.addLayout(button_layout)
        
        # Set dialog layout
        self.setLayout(layout)
        
        # Initialize class field
        self.update_class_field(self.student_combo.currentText())
    
    def update_class_field(self, student_name):
        """
        Update class field when student selection changes.
        
        Args:
            student_name (str): Selected student name
        """
        if student_name in self.face_system.student_database:
            self.class_input.setText(self.face_system.student_database[student_name].get("class", ""))
        else:
            self.class_input.setText("")
    
    def save_info(self):
        """Save student information."""
        student_name = self.student_combo.currentText()
        class_name = self.class_input.text().strip()
        
        if not class_name:
            QMessageBox.warning(self, "Warning", "Class name cannot be empty.")
            return
        
        # Update database
        if student_name not in self.face_system.student_database:
            self.face_system.student_database[student_name] = {}
        
        self.face_system.student_database[student_name]["class"] = class_name
        
        # Save the updated database
        self.face_system.db_manager.save_student_database()
        
        QMessageBox.information(self, "Success", f"Updated {student_name}'s class to {class_name}")
        self.accept()
