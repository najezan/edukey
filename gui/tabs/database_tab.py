"""
Database tab for managing student information.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QTableWidget, QTableWidgetItem)
from PyQt5.QtCore import Qt

from gui.dialogs.student_dialogs import StudentInfoDialog
from utils.logger import logger

class DatabaseTab(QWidget):
    """
    Tab for managing the student database.
    
    This tab contains a table of students and controls for managing
    student information.
    """
    
    def __init__(self, face_system):
        """
        Initialize the database tab.
        
        Args:
            face_system: Face recognition system
        """
        super().__init__()
        self.face_system = face_system
        
        # Initialize UI components
        self._init_ui()
        
        # Initialize table
        self.refresh_database()
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()
        
        # Create table for student database
        self.student_table = QTableWidget()
        self.student_table.setColumnCount(3)
        self.student_table.setHorizontalHeaderLabels(["Name", "Class", "Face Encodings"])
        self.student_table.horizontalHeader().setStretchLastSection(True)
        
        # Create control buttons
        button_layout = QHBoxLayout()
        self.update_button = QPushButton("Update Student Info")
        self.refresh_button = QPushButton("Refresh Database")
        
        button_layout.addWidget(self.update_button)
        button_layout.addWidget(self.refresh_button)
        
        # Connect buttons
        self.update_button.clicked.connect(self.update_student_info)
        self.refresh_button.clicked.connect(self.refresh_database)
        
        # Add widgets to layout
        layout.addWidget(self.student_table)
        layout.addLayout(button_layout)
        
        # Set layout for tab
        self.setLayout(layout)
    
    def update_student_info(self):
        """Update student information."""
        if not self.face_system.trained_people:
            QMessageBox.warning(self, "Warning", "No people in the trained model yet.")
            return
        
        dialog = StudentInfoDialog(self.face_system, self)
        if dialog.exec_():
            # Refresh database tab
            self.refresh_database()
            logger.info("Student information updated")
    
    def refresh_database(self):
        """Refresh student database table."""
        # Clear table
        self.student_table.setRowCount(0)
        
        # Add rows for each student
        for i, person_name in enumerate(sorted(list(self.face_system.trained_people))):
            self.student_table.insertRow(i)
            
            # Count how many encodings are associated with this person
            encoding_count = self.face_system.known_face_names.count(person_name)
            
            # Get class information
            class_info = self.face_system.student_database.get(person_name, {}).get("class", "Not set")
            
            # Set table items
            self.student_table.setItem(i, 0, QTableWidgetItem(person_name))
            self.student_table.setItem(i, 1, QTableWidgetItem(class_info))
            self.student_table.setItem(i, 2, QTableWidgetItem(str(encoding_count)))
        
        logger.info("Student database refreshed")
