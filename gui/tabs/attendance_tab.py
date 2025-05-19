"""
Attendance tab for displaying and managing attendance records.
"""

from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QDateEdit, QHeaderView
)
from PyQt5.QtCore import Qt, QDate

class AttendanceTab(QWidget):
    """Tab for displaying and managing attendance records."""
    
    def __init__(self, db_manager, parent=None):
        """
        Initialize the attendance tab.
        
        Args:
            db_manager: DatabaseManager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_manager = db_manager
        
        # Initialize UI
        self.init_ui()
        
        # Load today's attendance
        self.load_attendance()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        
        # Controls layout
        controls_layout = QHBoxLayout()
        
        # Date selection
        self.date_label = QLabel("Date:")
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.dateChanged.connect(self.load_attendance)
        
        # Class filter
        self.class_label = QLabel("Class:")
        self.class_combo = QComboBox()
        self.class_combo.addItem("All Classes")
        self.update_class_list()
        self.class_combo.currentTextChanged.connect(self.load_attendance)
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_attendance)
        
        # Add controls to layout
        controls_layout.addWidget(self.date_label)
        controls_layout.addWidget(self.date_edit)
        controls_layout.addWidget(self.class_label)
        controls_layout.addWidget(self.class_combo)
        controls_layout.addWidget(self.refresh_btn)
        controls_layout.addStretch()
        
        # Table for displaying attendance
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Name", "Class", "Time In", "Status", 
            "Verification Method", "Confidence"
        ])
        
        # Auto-resize columns to content
        header = self.table.horizontalHeader()
        for i in range(6):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        # Statistics layout
        stats_layout = QHBoxLayout()
        self.total_label = QLabel()
        self.present_label = QLabel()
        self.late_label = QLabel()
        stats_layout.addWidget(self.total_label)
        stats_layout.addWidget(self.present_label)
        stats_layout.addWidget(self.late_label)
        stats_layout.addStretch()
        
        # Add all widgets to main layout
        layout.addLayout(controls_layout)
        layout.addWidget(self.table)
        layout.addLayout(stats_layout)
        
        self.setLayout(layout)
    
    def update_class_list(self):
        """Update the class filter combo box with available classes."""
        classes = set()
        for student_data in self.db_manager.student_database.values():
            if "class" in student_data:
                classes.add(student_data["class"])
        
        self.class_combo.clear()
        self.class_combo.addItem("All Classes")
        self.class_combo.addItems(sorted(classes))
    
    def load_attendance(self):
        """Load and display attendance records."""
        date = self.date_edit.date().toString("yyyy-MM-dd")
        selected_class = self.class_combo.currentText()
        
        # Get attendance records for the date
        attendance = self.db_manager.get_attendance(date)
        
        # Filter by class if needed
        if selected_class != "All Classes":
            attendance = {
                name: record for name, record in attendance.items()
                if record.get("class") == selected_class
            }
        
        # Update table
        self.table.setRowCount(len(attendance))
        
        for row, (name, record) in enumerate(sorted(attendance.items())):
            # Name
            self.table.setItem(row, 0, QTableWidgetItem(name))
            
            # Class
            class_item = QTableWidgetItem(record.get("class", ""))
            self.table.setItem(row, 1, class_item)
            
            # Time In
            time_item = QTableWidgetItem(record.get("time_in", ""))
            self.table.setItem(row, 2, time_item)
            
            # Status
            status_item = QTableWidgetItem(record.get("status", ""))
            status_item.setForeground(
                Qt.red if record.get("status") == "late" else Qt.black)
            self.table.setItem(row, 3, status_item)
            
            # Verification Method
            verify_item = QTableWidgetItem(record.get("verification_method", ""))
            self.table.setItem(row, 4, verify_item)
            
            # Confidence
            confidence = record.get("confidence", 0)
            confidence_item = QTableWidgetItem(f"{confidence}%")
            self.table.setItem(row, 5, confidence_item)
        
        # Update statistics
        total = len(attendance)
        present = sum(1 for r in attendance.values() if r.get("status") == "present")
        late = sum(1 for r in attendance.values() if r.get("status") == "late")
        
        self.total_label.setText(f"Total: {total}")
        self.present_label.setText(f"Present: {present}")
        self.late_label.setText(f"Late: {late}")
