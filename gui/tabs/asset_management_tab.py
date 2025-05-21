"""
Asset management tab for tracking asset borrowing and returns.
"""

from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QHeaderView, QMessageBox,
    QComboBox, QDialog, QFormLayout, QMainWindow, QTabWidget
)
from PyQt5.QtCore import Qt, pyqtSignal

class AssetManagementTab(QWidget):
    rfid_detected = pyqtSignal(str)  # Signal for RFID detection
    """Tab for tracking asset borrowing and returns."""
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.main_window = parent  # Store main window reference for tab switching
        self.init_ui()
        self.load_assets()
        # Connect RFID signal to handler
        self.rfid_detected.connect(self.handle_rfid_detected)
        if hasattr(self.db_manager, 'rfid_callback'):
            self.db_manager.rfid_callback = self.rfid_detected.emit
        # Track last RFID and asset for return logic
        self._last_rfid = None
        self._last_asset = None

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
        self.borrower_input.setPlaceholderText("Select Borrower")
        self.borrower_input.setEditable(True)  # Allow user to type in the dropdown
        # Changed from LineEdit to QComboBox
        # self.borrower_class = QComboBox()
        self.borrow_btn = QPushButton("Borrow Asset")
        self.return_btn = QPushButton("Return Asset")
        self.delete_btn = QPushButton("Delete Asset")
        self.refresh_btn = QPushButton("Refresh")

        controls_layout.addWidget(self.asset_name_input)
        controls_layout.addWidget(self.borrower_input)
        # controls_layout.addWidget(self.borrower_class)
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
        # self.borrower_input.currentTextChanged.connect(self.update_class_dropdown)

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
        """Filter assets based on search criteria with improved case handling and null checks."""
        try:
            filter_asset = self.filter_asset_name.text().strip().lower() if hasattr(self, 'filter_asset_name') else ""
            filter_borrower = self.filter_borrower.text().strip().lower() if hasattr(self, 'filter_borrower') else ""
            filter_class = self.filter_class.text().strip().lower() if hasattr(self, 'filter_class') else ""
        except AttributeError:
            filter_asset = ""
            filter_borrower = ""
            filter_class = ""

        filtered_assets = {}
        for asset, record in self.all_assets.items():
            asset_name = str(asset).lower() if asset else ""
            borrower_name = str(record.get("borrower", "")).lower() if record else ""
            class_name = str(record.get("class", "")).lower() if record else ""
            
            if (filter_asset in asset_name and
                filter_borrower in borrower_name and
                filter_class in class_name):
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
        classes = self.db_manager.student_database.get(borrower, {}).get("class", "").strip() if borrower else ""
        if not asset or not borrower:
            QMessageBox.warning(self, "Warning", "Please enter asset name.")
            return
        
        # check if the borrower is in the student database
        if not classes:
            QMessageBox.warning(self, "Warning", "Please select a valid borrower.")
            return
        
        # check if the asset is already borrowed
        if asset in self.all_assets and self.all_assets[asset].get("borrower"):
            QMessageBox.warning(self, "Warning", f"{asset} is already borrowed by {self.all_assets[asset]['borrower']}.")
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
        """Populate the borrower dropdown with registered students with improved error handling."""
        try:
            current_text = self.borrower_input.currentText() if self.borrower_input.count() > 0 else ""
            
            # Clear and refill the dropdown
            self.borrower_input.clear()
            
            # Add students from trained_people set in db_manager
            if hasattr(self.db_manager, 'trained_people') and self.db_manager.trained_people:
                students = sorted(list(self.db_manager.trained_people))
                if students:
                    self.borrower_input.addItems(students)
                    
                    # Try to restore previous selection
                    if current_text:
                        index = self.borrower_input.findText(current_text)
                        if index >= 0:
                            self.borrower_input.setCurrentIndex(index)
                    
                    # Update class dropdown based on current selection
                    # self.update_class_dropdown()
                else:
                    self.borrower_input.addItem("No students available")
            else:
                self.borrower_input.addItem("No students database available")
        except Exception as e:
            print(f"Error populating borrower dropdown: {str(e)}")
            self.borrower_input.addItem("Error loading students")
    
    # def update_class_dropdown(self):
    #     """Update class dropdown based on the selected student with improved error handling and synchronization."""
    #     try:
    #         # Get selected student
    #         student_name = self.borrower_input.currentText()
            
    #         # Store current selection if any
    #         current_class = self.borrower_class.currentText() if self.borrower_class.count() > 0 else ""
            
    #         # Clear the class dropdown
    #         self.borrower_class.clear()
            
    #         student_info = {}
    #         if student_name and student_name not in ["No students available", "No students database available", "Error loading students"]:
    #             # Get available classes from the student database
    #             available_classes = set()
                
    #             # First, add the class of the selected student if available
    #             if hasattr(self.db_manager, 'student_database'):
    #                 student_info = self.db_manager.student_database.get(student_name, {})
    #                 student_class = student_info.get("class", "")
    #                 if student_class:
    #                     available_classes.add(student_class)
                
    #             # Then add all classes from all students for flexibility
    #             if hasattr(self.db_manager, 'student_database'):
    #                 for student_data in self.db_manager.student_database.values():
    #                     if "class" in student_data and student_data["class"]:
    #                         available_classes.add(student_data["class"])
                
    #             if available_classes:
    #                 # Add classes to dropdown
    #                 self.borrower_class.addItems(sorted(available_classes))
                    
    #                 # Try to restore previous selection if available
    #                 if current_class:
    #                     index = self.borrower_class.findText(current_class)
    #                     if index >= 0:
    #                         self.borrower_class.setCurrentIndex(index)
    #                 # Otherwise select the student's class if available
    #                 elif student_info.get("class"):
    #                     index = self.borrower_class.findText(student_info["class"])
    #                     if index >= 0:
    #                         self.borrower_class.setCurrentIndex(index)
    #             else:
    #                 self.borrower_class.addItem("No classes available")
    #         else:
    #             self.borrower_class.addItem("No class available")
    #     except Exception as e:
    #         print(f"Error updating class dropdown: {str(e)}")
    #         self.borrower_class.addItem("Error loading classes")

    def _get_main_window(self):
        win = self.window()
        tabs = getattr(win, 'tabs', None)
        if tabs and isinstance(tabs, QTabWidget):
            return win
        return None

    def handle_rfid_detected(self, rfid_code, is_new_card=None):
        """
        Handle RFID card detection for asset management, matching StudentRFIDTab logic.
        Args:
            rfid_code (str): Card ID or person name
            is_new_card (bool or None): True if new card, False if existing, None if unknown (for backward compatibility)
        """
        main_window = self.main_window
        mode = getattr(main_window, 'rfid_mode', 'identify') if main_window else 'identify'
        # Find student info
        student_name = ""
        student_class = ""
        card_id = rfid_code
        # Try to resolve card to student
        if hasattr(self.db_manager, 'rfid_database') and rfid_code in self.db_manager.rfid_database:
            student_name = self.db_manager.rfid_database[rfid_code]
            student_info = self.db_manager.student_database.get(student_name, {})
            student_class = student_info.get('class', '')
            is_new = False
        else:
            # Try to resolve by name (for identify mode)
            if hasattr(self.db_manager, 'student_database') and rfid_code in self.db_manager.student_database:
                student_name = rfid_code
                student_info = self.db_manager.student_database.get(student_name, {})
                student_class = student_info.get('class', '')
                # Try to find card id
                card_id = student_info.get('rfid', rfid_code)
                is_new = False
            else:
                is_new = True
        # If is_new_card is provided by signal, use it
        if is_new_card is not None:
            is_new = is_new_card
        # Only allow detection if current tab is Asset Management
        tabs = getattr(main_window, 'tabs', None)
        if tabs:
            current_tab = tabs.currentWidget()
            if current_tab is not self:
                return
        if mode == "add_edit":
            if is_new:
                # New card: switch to Student & RFID tab for registration
                if main_window and hasattr(main_window, 'student_rfid_tab'):
                    main_window.tabs.setCurrentWidget(main_window.student_rfid_tab)
                    QMessageBox.information(main_window.student_rfid_tab, "Unknown Card", f"Card ID {card_id} is not registered in the system.\n\nSwitched to Student & RFID tab for registration.")
                else:
                    QMessageBox.warning(self, "Unknown Card", f"Card ID {card_id} is not registered in the system.\n\nSwitch to Student & RFID tab to register this card.")
            else:
                # Existing card: show borrow dialog
                self._show_borrow_dialog(card_id, student_name, student_class)
        else:
            # Identify mode: authenticate or return asset
            if not is_new:
                # If last asset borrowed by this card, return it
                if self._last_rfid == card_id and self._last_asset:
                    asset = self._last_asset
                    asset_info = self.all_assets.get(asset, {})
                    if asset_info.get('borrower') == student_name and not asset_info.get('returned_at'):
                        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        if hasattr(self.db_manager, 'return_asset'):
                            success = self.db_manager.return_asset(asset, now)
                            if success:
                                self.load_assets()
                                QMessageBox.information(self, "Returned", f"{asset} returned by {student_name}.")
                            else:
                                QMessageBox.warning(self, "Error", f"Failed to return {asset}.")
                        self._last_rfid = None
                        self._last_asset = None
                        return
                    else:
                        self._last_rfid = None
                        self._last_asset = None
                # Otherwise, show borrow dialog
                self._show_borrow_dialog(card_id, student_name, student_class)
            else:
                # New card in identify mode: switch to Student & RFID tab for registration
                if main_window and hasattr(main_window, 'student_rfid_tab'):
                    main_window.tabs.setCurrentWidget(main_window.student_rfid_tab)
                    QMessageBox.information(main_window.student_rfid_tab, "Unknown Card", f"Card ID {card_id} is not registered in the system.\n\nSwitched to Student & RFID tab for registration.")
                else:
                    QMessageBox.warning(self, "Unknown Card", f"Card ID {card_id} is not registered in the system.\n\nSwitch to Student & RFID tab to register this card.")

    def _show_borrow_dialog(self, card_id, student_name, student_class):
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
                    self._last_rfid = card_id
                    self._last_asset = asset
                    dialog.accept()
                else:
                    QMessageBox.warning(dialog, "Failed", "Failed borrow asset.")
        btn_borrow.clicked.connect(do_borrow)
        btn_cancel.clicked.connect(dialog.reject)
        dialog.exec_()
        if dialog.result() != QDialog.Accepted:
            self._last_rfid = None
            self._last_asset = None
