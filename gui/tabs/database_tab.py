"""
Database tab for managing student information.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QTableWidget, QTableWidgetItem, QMessageBox)
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
        self.student_table.setColumnCount(4)
        self.student_table.setHorizontalHeaderLabels(["Name", "Class", "Face Encodings", "Point"])
        self.student_table.horizontalHeader().setStretchLastSection(True)
        self.student_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.student_table.setSelectionMode(QTableWidget.SingleSelection)
        
        # Create control buttons
        button_layout = QHBoxLayout()
        self.update_button = QPushButton("Update Student Info")
        self.delete_button = QPushButton("Delete Student")
        self.refresh_button = QPushButton("Refresh Database")
        
        button_layout.addWidget(self.update_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.refresh_button)
        
        # Connect buttons
        self.update_button.clicked.connect(self.update_student_info)
        self.delete_button.clicked.connect(self.delete_student)
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
            # Ensure point is set for updated/created student
            student_name = dialog.student_combo.currentText()
            if student_name in self.face_system.student_database:
                if "point" not in self.face_system.student_database[student_name]:
                    self.face_system.student_database[student_name]["point"] = 100
                self.face_system.db_manager.save_student_database()
            # Refresh database tab
            self.refresh_database()
            logger.info("Student information updated")
    
    def delete_student(self):
        """Delete a student and all associated data."""
        # Check if there are any students
        if not self.face_system.trained_people:
            QMessageBox.warning(self, "Warning", "No people in the trained model yet.")
            return
        
        # Check if a student is selected
        selected_items = self.student_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select a student to delete.")
            return
        
        # Get the selected student's name
        row = selected_items[0].row()
        student_name = self.student_table.item(row, 0).text()
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, "Confirm Deletion",
            f"Are you sure you want to delete {student_name} and all associated data?\n\n"
            f"This will remove:\n"
            f"- Student information\n"
            f"- Face recognition data\n"
            f"- RFID card associations\n"
            f"- All dataset images\n\n"
            f"This action cannot be undone!",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Delete the student
            if self.face_system.db_manager.delete_student(student_name):
                # Update face system references
                self.face_system.known_face_encodings = self.face_system.db_manager.face_encodings
                self.face_system.known_face_names = self.face_system.db_manager.face_names
                self.face_system.trained_people = self.face_system.db_manager.trained_people
                self.face_system.student_database = self.face_system.db_manager.student_database
                
                # Refresh the database display
                self.refresh_database()
                
                # Show success message
                QMessageBox.information(self, "Success", f"Successfully deleted {student_name} and all associated data.")
                logger.info(f"Student {student_name} deleted successfully")
                
                # Trigger refresh in RFID tab (if main window has access to it)
                if hasattr(self.parent(), "main_window") and hasattr(self.parent().main_window, "rfid_tab"):
                    self.parent().main_window.rfid_tab.refresh_rfid_table()
                    self.parent().main_window.rfid_tab.refresh_person_combo()
            else:
                QMessageBox.critical(self, "Error", f"Failed to delete {student_name}. Check logs for details.")
    
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
            
            # Get point information, default to 100 if not set
            point = self.face_system.student_database.get(person_name, {}).get("point", 100)
            
            # Set table items
            self.student_table.setItem(i, 0, QTableWidgetItem(person_name))
            self.student_table.setItem(i, 1, QTableWidgetItem(class_info))
            self.student_table.setItem(i, 2, QTableWidgetItem(str(encoding_count)))
            self.student_table.setItem(i, 3, QTableWidgetItem(str(point)))
        
        logger.info("Student database refreshed")