"""
Asset management tab for tracking asset borrowing and returns.
"""

from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QDateEdit, QHeaderView, QMessageBox,
    QComboBox, QDialog, QFormLayout
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal

class AssetManagementTab(QWidget):
    rfid_detected = pyqtSignal(str)  # Signal for RFID detection
    """Tab for tracking asset borrowing and returns."""
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.init_ui()
        self.load_assets()
        # Connect RFID signal to handler
        self.rfid_detected.connect(self.handle_rfid_detected)
        # Example: If you have a thread or callback for RFID, connect it here
        if hasattr(self.db_manager, 'rfid_callback'):
            self.db_manager.rfid_callback = self.rfid_detected.emit

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Filter layout
        filter_layout = QHBoxLayout()
        self.filter_asset_name = QLineEdit()
        self.filter_asset_name.setPlaceholderText("Filter by Asset Name")
        self.filter_borrower = QLineEdit()
        self.filter_borrower.setPlaceholderText("Filter by Borrower")
        self.filter_class = QLineEdit()
        self.filter_class.setPlaceholderText("Filter by Class")
        
        filter_layout.addWidget(self.filter_asset_name)
        filter_layout.addWidget(self.filter_borrower)
        filter_layout.addWidget(self.filter_class)
        filter_layout.addStretch()
          # Controls layout
        controls_layout = QHBoxLayout()
        
        self.asset_name_input = QLineEdit()
        self.asset_name_input.setPlaceholderText("Asset Name")
        self.borrower_input = QComboBox()
        # Changed from LineEdit to QComboBox
        self.borrower_class = QComboBox()
        self.borrow_btn = QPushButton("Borrow Asset")
        self.return_btn = QPushButton("Return Asset")
        self.delete_btn = QPushButton("Delete Asset")
        self.refresh_btn = QPushButton("Refresh")

        controls_layout.addWidget(self.asset_name_input)
        controls_layout.addWidget(self.borrower_input)
        controls_layout.addWidget(self.borrower_class)
        controls_layout.addWidget(self.borrow_btn)
        controls_layout.addWidget(self.return_btn)
        controls_layout.addWidget(self.delete_btn)
        controls_layout.addWidget(self.refresh_btn)
        controls_layout.addStretch()

        self.borrow_btn.clicked.connect(self.borrow_asset)
        self.return_btn.clicked.connect(self.return_asset)
        self.delete_btn.clicked.connect(self.delete_asset)
        self.refresh_btn.clicked.connect(self.load_assets)
        
        # Connect filter inputs to filter function
        self.filter_asset_name.textChanged.connect(self.filter_assets)
        self.filter_borrower.textChanged.connect(self.filter_assets)
        self.filter_class.textChanged.connect(self.filter_assets)
        
        # Connect borrower selection change to update class dropdown
        self.borrower_input.currentTextChanged.connect(self.update_class_dropdown)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Asset Name", "Borrower", "Class", "Borrowed At", "Returned At"
        ])
        header = self.table.horizontalHeader()
        for i in range(5):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)

        layout.addLayout(filter_layout)
        layout.addLayout(controls_layout)
        layout.addWidget(self.table)
        self.setLayout(layout)
    def load_assets(self):
        self.all_assets = self.db_manager.get_assets() if hasattr(self.db_manager, 'get_assets') else {}
        self.filter_assets()
        # Refresh student dropdown whenever assets are loaded
        self.populate_borrower_dropdown()
        # Class dropdown is updated from within populate_borrower_dropdown()

    def filter_assets(self):
        filter_asset = self.filter_asset_name.text().strip().lower()
        filter_borrower = self.filter_borrower.text().strip().lower()
        filter_class = self.filter_class.text().strip().lower()

        filtered_assets = {}
        for asset, record in self.all_assets.items():
            if (filter_asset in asset.lower() and
                filter_borrower in record.get("borrower", "").lower() and
                filter_class in record.get("class", "").lower()):
                filtered_assets[asset] = record

        self.table.setRowCount(len(filtered_assets))
        for row, (asset, record) in enumerate(sorted(filtered_assets.items())):
            self.table.setItem(row, 0, QTableWidgetItem(asset))
            self.table.setItem(row, 1, QTableWidgetItem(record.get("borrower", "")))
            self.table.setItem(row, 2, QTableWidgetItem(record.get("class", "")))
            borrowed_at_item = QTableWidgetItem(record.get("borrowed_at", ""))
            returned_at_item = QTableWidgetItem(record.get("returned_at", ""))
            borrowed_at_item.setTextAlignment(Qt.AlignCenter)
            returned_at_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, borrowed_at_item)
            self.table.setItem(row, 4, returned_at_item)


    def borrow_asset(self):
        asset = self.asset_name_input.text().strip()
        borrower = self.borrower_input.currentText().strip()
        classes = self.borrower_class.currentText().strip()
        if not asset or not borrower or not classes:
            QMessageBox.warning(self, "Warning", "Please enter asset name/borrower's name/borrower's class.")
            return
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if hasattr(self.db_manager, 'borrow_asset'):
            success = self.db_manager.borrow_asset(asset, borrower, classes, now)
            if success:
                self.load_assets()
                QMessageBox.information(self, "Success", f"{asset} borrowed by {borrower}.")
            else:
                QMessageBox.warning(self, "Error", "Failed to borrow asset.")

    def return_asset(self):
        asset = self.asset_name_input.text().strip()
        if not asset:
            QMessageBox.warning(self, "Warning", "Please enter asset name to return.")
            return
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if hasattr(self.db_manager, 'return_asset'):
            success = self.db_manager.return_asset(asset, now)
            if success:
                self.load_assets()
                QMessageBox.information(self, "Success", f"{asset} returned.")
            else:
                QMessageBox.warning(self, "Error", "Failed to return asset.")

    def delete_asset(self):
        """Delete an asset record."""
        # asset = self.asset_name_input.text().strip()
        selected_asset = self.table.selectedItems()
        if not selected_asset:
            QMessageBox.warning(self, "Warning", "Please select a asset to delete.")
            return
        
        # Get the selected student's name
        row = selected_asset[0].row()
        asset = self.table.item(row, 0).text()

        reply = QMessageBox.question(self, "Confirm Delete", 
                                   f"Are you sure you want to delete the asset record for '{asset}'?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes and hasattr(self.db_manager, 'delete_asset'):
            success = self.db_manager.delete_asset(asset)
            if success:
                self.load_assets()
                QMessageBox.information(self, "Success", f"Asset record for '{asset}' has been deleted.")
            else:
                QMessageBox.warning(self, "Error", "Failed to delete asset record.")

    def populate_borrower_dropdown(self):
        """Populate the borrower dropdown with registered students."""
        current_text = self.borrower_input.currentText() if self.borrower_input.count() > 0 else ""
        
        # Clear and refill the dropdown
        self.borrower_input.clear()
        
        # Add students from trained_people set in db_manager
        if hasattr(self.db_manager, 'trained_people'):
            self.borrower_input.addItems(sorted(list(self.db_manager.trained_people)))
        
        # Try to restore previous selection
        if current_text:
            index = self.borrower_input.findText(current_text)
            if index >= 0:
                self.borrower_input.setCurrentIndex(index)
        
        # Update class dropdown based on current selection
        self.update_class_dropdown()
    
    def update_class_dropdown(self):
        """Update class dropdown based on the selected student."""
        # Get selected student
        student_name = self.borrower_input.currentText()
        
        # Store current selection if any
        current_class = self.borrower_class.currentText() if self.borrower_class.count() > 0 else ""
        
        # Clear the class dropdown
        self.borrower_class.clear()
        
        # Get available classes from the student database
        available_classes = set()
        
        # First, add the class of the selected student if available
        if student_name and hasattr(self.db_manager, 'student_database'):
            student_info = self.db_manager.student_database.get(student_name, {})
            student_class = student_info.get("class", "")
            if student_class:
                available_classes.add(student_class)
        
        # Then add all classes from all students for flexibility
        if hasattr(self.db_manager, 'student_database'):
            for student_data in self.db_manager.student_database.values():
                if "class" in student_data and student_data["class"]:
                    available_classes.add(student_data["class"])
        
        # Add classes to dropdown
        self.borrower_class.addItems(sorted(available_classes))
        
        # If there was a previous selection and it's still available, restore it
        if current_class:
            index = self.borrower_class.findText(current_class)
            if index >= 0:
                self.borrower_class.setCurrentIndex(index)
        # Otherwise select the student's class if available
        elif student_name and hasattr(self.db_manager, 'student_database'):
            student_class = self.db_manager.student_database.get(student_name, {}).get("class", "")
            if student_class:
                index = self.borrower_class.findText(student_class)
                if index >= 0:
                    self.borrower_class.setCurrentIndex(index)

    def handle_rfid_detected(self, rfid_code):
        """Handle detected RFID, show popup with student/class and asset input."""
        student_name = ""
        student_class = ""
        if hasattr(self.db_manager, 'student_database'):
            for name, info in self.db_manager.student_database.items():
                if info.get('rfid') == rfid_code:
                    student_name = name
                    student_class = info.get('class', '')
                    break
        if not student_name:
            QMessageBox.warning(self, "RFID Not Found", f"RFID {rfid_code} not registered in the database.")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Asset Borrowing via RFID")
        layout = QFormLayout(dialog)
        name_label = QLabel(student_name)
        class_label = QLabel(student_class)
        asset_input = QLineEdit()
        asset_input.setPlaceholderText("Enter asset name")
        layout.addRow("Name:", name_label)
        layout.addRow("Class:", class_label)
        layout.addRow("Asset:", asset_input)
        btn_borrow = QPushButton("Borrow")
        btn_cancel = QPushButton("Cancel")
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_borrow)
        btn_layout.addWidget(btn_cancel)
        layout.addRow(btn_layout)
        def do_borrow():
            asset = asset_input.text().strip()
            if not asset:
                QMessageBox.warning(dialog, "Warning", "Enter asset name.")
                return
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if hasattr(self.db_manager, 'borrow_asset'):
                success = self.db_manager.borrow_asset(asset, student_name, student_class, now)
                if success:
                    self.load_assets()
                    QMessageBox.information(self, "Success", f"{asset} borrowed by {student_name}.")
                    dialog.accept()
                else:
                    QMessageBox.warning(dialog, "Failed", "Failed borrow asset.")
        btn_borrow.clicked.connect(do_borrow)
        btn_cancel.clicked.connect(dialog.reject)
        dialog.exec_()
