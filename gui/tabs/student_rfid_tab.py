"""
Combined tab for managing students and their RFID cards.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
                           QPushButton, QLabel, QTableWidget, QTableWidgetItem, 
                           QLineEdit, QComboBox, QRadioButton, QMessageBox,
                           QInputDialog, QSplitter, QTabWidget)
from PyQt5.QtCore import Qt, pyqtSignal

from gui.dialogs.student_dialogs import StudentInfoDialog
from utils.logger import logger

class StudentRFIDTab(QWidget):
    """
    Combined tab for managing student information and RFID cards.
    
    This tab contains both the student database and RFID management functionality
    in a single integrated interface.
    """
    
    # Define signals
    mode_changed = pyqtSignal(str)  # Mode ('identify' or 'add_edit')
    
    def __init__(self, face_system, main_window):
        """
        Initialize the combined student and RFID tab.
        
        Args:
            face_system: Face recognition system
            main_window: Main window for RFID server access
        """
        super().__init__()
        self.face_system = face_system
        self.main_window = main_window
        
        # Initialize UI components
        self._init_ui()
        
        # Initialize tables
        self.refresh_database()
        self.refresh_rfid_table()
    
    def _init_ui(self):
        """Initialize UI components."""
        # Main layout
        main_layout = QVBoxLayout()
        
        # Create tab selection area
        tab_widget = QTabWidget()
        
        # Student Database Tab
        student_tab = QWidget()
        student_layout = QVBoxLayout()
        
        # Create table for student database
        self.student_table = QTableWidget()
        self.student_table.setColumnCount(3)
        self.student_table.setHorizontalHeaderLabels(["Name", "Class", "Face Encodings"])
        self.student_table.horizontalHeader().setStretchLastSection(True)
        self.student_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.student_table.setSelectionMode(QTableWidget.SingleSelection)
        
        # Student control buttons
        student_button_layout = QHBoxLayout()
        self.update_student_button = QPushButton("Update Student Info")
        self.delete_student_button = QPushButton("Delete Student")
        self.refresh_student_button = QPushButton("Refresh Database")
        
        student_button_layout.addWidget(self.update_student_button)
        student_button_layout.addWidget(self.delete_student_button)
        student_button_layout.addWidget(self.refresh_student_button)
        
        # Connect student buttons
        self.update_student_button.clicked.connect(self.update_student_info)
        self.delete_student_button.clicked.connect(self.delete_student)
        self.refresh_student_button.clicked.connect(self.refresh_database)
        
        # Add student widgets to layout
        student_layout.addWidget(self.student_table)
        student_layout.addLayout(student_button_layout)
        student_tab.setLayout(student_layout)
        
        # RFID Management Tab
        rfid_tab = QWidget()
        rfid_layout = QVBoxLayout()
        
        # Create RFID card table
        self.rfid_table = QTableWidget()
        self.rfid_table.setColumnCount(2)
        self.rfid_table.setHorizontalHeaderLabels(["Card ID", "Person"])
        self.rfid_table.horizontalHeader().setStretchLastSection(True)
        
        # Create a simple refresh button for the RFID table
        refresh_layout = QHBoxLayout()
        self.refresh_rfid_button = QPushButton("Refresh RFID Table")
        refresh_layout.addWidget(self.refresh_rfid_button)
        
        # Connect refresh button
        self.refresh_rfid_button.clicked.connect(self.refresh_rfid_table)
        
        # Create hidden person combo for internal use (not displayed)
        self.person_combo = QComboBox()
        self.refresh_person_combo()
        
        # Create RFID mode selection
        mode_group = QGroupBox("RFID Operation Mode")
        mode_layout = QVBoxLayout()
        
        self.identify_radio = QRadioButton("Identify Mode")
        self.add_edit_radio = QRadioButton("Add/Edit Mode")
        
        # Set default mode
        self.identify_radio.setChecked(True)
        
        # Connect mode radio buttons
        self.identify_radio.toggled.connect(self.on_mode_changed)
        
        # Add mode description labels
        identify_desc = QLabel("Identify Mode: RFID cards are used for authentication and identification only.")
        add_edit_desc = QLabel("Add/Edit Mode: RFID cards trigger registration or editing dialogs.")
        
        mode_layout.addWidget(self.identify_radio)
        mode_layout.addWidget(identify_desc)
        mode_layout.addWidget(self.add_edit_radio)
        mode_layout.addWidget(add_edit_desc)
        
        mode_group.setLayout(mode_layout)
        
        # Create server status display
        self.server_status = QLabel("RFID Server: Stopped")
        
        # Create server control buttons
        server_button_layout = QHBoxLayout()
        self.start_server_button = QPushButton("Start RFID Server")
        self.stop_server_button = QPushButton("Stop RFID Server")
        self.stop_server_button.setEnabled(False)
        
        server_button_layout.addWidget(self.start_server_button)
        server_button_layout.addWidget(self.stop_server_button)
        
        # Connect server buttons
        self.start_server_button.clicked.connect(self.start_rfid_server)
        self.stop_server_button.clicked.connect(self.stop_rfid_server)
        
        # Add RFID widgets to layout
        rfid_layout.addWidget(self.rfid_table)
        rfid_layout.addLayout(refresh_layout)
        rfid_layout.addWidget(mode_group)
        rfid_layout.addWidget(self.server_status)
        rfid_layout.addLayout(server_button_layout)
        rfid_tab.setLayout(rfid_layout)
        
        # Add tabs to tab widget
        tab_widget.addTab(student_tab, "Student Management")
        tab_widget.addTab(rfid_tab, "RFID Management")
        
        # Add tab widget to main layout
        main_layout.addWidget(tab_widget)
        
        # Set main layout
        self.setLayout(main_layout)
    
    #
    # Student Database Methods
    #
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
                
                # Also refresh RFID table and combo
                self.refresh_rfid_table()
                self.refresh_person_combo()
                
                # Show success message
                QMessageBox.information(self, "Success", f"Successfully deleted {student_name} and all associated data.")
                logger.info(f"Student {student_name} deleted successfully")
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
            
            # Set table items
            self.student_table.setItem(i, 0, QTableWidgetItem(person_name))
            self.student_table.setItem(i, 1, QTableWidgetItem(class_info))
            self.student_table.setItem(i, 2, QTableWidgetItem(str(encoding_count)))
        
        logger.info("Student database refreshed")
    
    #
    # RFID Management Methods
    #
    def refresh_person_combo(self):
        """Refresh person combo box with trained people."""
        current_text = self.person_combo.currentText() if self.person_combo.count() > 0 else ""
        
        self.person_combo.clear()
        self.person_combo.addItems(sorted(list(self.face_system.trained_people)))
        
        # Try to restore previous selection
        if current_text:
            index = self.person_combo.findText(current_text)
            if index >= 0:
                self.person_combo.setCurrentIndex(index)
    
    def on_mode_changed(self, checked):
        """
        Handle mode radio button change.
        
        Args:
            checked (bool): True if identify_radio is checked
        """
        if checked:
            mode = "identify"
        else:
            mode = "add_edit"
        
        self.mode_changed.emit(mode)
    
    def scan_rfid_card(self):
        """Scan new RFID card."""
        # This would normally wait for a card scan from the ESP32
        # For testing, we'll simulate it with a dialog
        card_id, ok = QInputDialog.getText(self, "Scan RFID Card", 
                                          "Please scan an RFID card or enter ID manually:")
        if ok and card_id:
            self.card_id_input.setText(card_id.upper())  # Ensure uppercase for consistency
    
    def add_rfid_card(self, card_id, person_name):
        """Add RFID card to database programmatically.
        
        Args:
            card_id (str): RFID card ID
            person_name (str): Person name
        """
        if not card_id or not person_name:
            return False
            
        # Check if card already exists
        if card_id in self.face_system.db_manager.rfid_database:
            return False
            
        # Add card to database
        success = self.face_system.db_manager.add_rfid_card(card_id, person_name)
        
        # Refresh table
        if success:
            self.refresh_rfid_table()
            logger.info(f"RFID card {card_id} assigned to {person_name}")
            
        return success
    
    def delete_rfid_card(self):
        """Delete selected RFID card."""
        selected_items = self.rfid_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select a card to delete.")
            return
        
        # Get card ID from first column of selected row
        row = selected_items[0].row()
        card_id = self.rfid_table.item(row, 0).text()
        
        reply = QMessageBox.question(
            self, "Confirmation", 
            f"Are you sure you want to delete card {card_id}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Remove card from database
            if self.face_system.db_manager.remove_rfid_card(card_id):
                # Refresh table
                self.refresh_rfid_table()
                
                QMessageBox.information(self, "Success", f"RFID card {card_id} deleted")
                logger.info(f"RFID card {card_id} deleted")
            else:
                QMessageBox.warning(self, "Error", "Failed to delete card")
    
    def refresh_rfid_table(self):
        """Refresh RFID card table."""
        # Clear table
        self.rfid_table.setRowCount(0)
        
        # Add rows for each card
        for i, (card_id, person_name) in enumerate(sorted(self.face_system.db_manager.rfid_database.items())):
            self.rfid_table.insertRow(i)
            
            # Set table items
            self.rfid_table.setItem(i, 0, QTableWidgetItem(card_id))
            self.rfid_table.setItem(i, 1, QTableWidgetItem(person_name))
        
        logger.info("RFID table refreshed")
    
    def start_rfid_server(self):
        """Start RFID server."""
        # Get port from settings tab (this would normally come from settings)
        port = self.face_system.config.get("rfid_port", 8080)
        self.main_window.rfid_server.port = port
        
        # Disable start button and enable stop button
        self.start_server_button.setEnabled(False)
        self.stop_server_button.setEnabled(True)
        
        # Start server thread
        self.main_window.rfid_server.start()
        
        # Update status with current mode
        mode_text = "Identify" if self.identify_radio.isChecked() else "Add/Edit"
        self.update_status(f"RFID Server: Running on port {port} (Mode: {mode_text})")
        
        logger.info(f"RFID server started on port {port}")
    
    def stop_rfid_server(self):
        """Stop RFID server."""
        if self.main_window.rfid_server.isRunning():
            self.main_window.rfid_server.stop()
            self.main_window.rfid_server.wait()
        
        # Enable start button and disable stop button
        self.start_server_button.setEnabled(True)
        self.stop_server_button.setEnabled(False)
        
        # Update status
        self.update_status("RFID Server: Stopped")
        
        logger.info("RFID server stopped")
    
    def update_status(self, status):
        """
        Update server status display.
        
        Args:
            status (str): Status message
        """
        self.server_status.setText(status)
    
    def handle_rfid_detection(self, identifier, is_new_card):
        """
        Handle RFID card detection based on current mode, but only if the current tab is Face Recognition or Student & RFID Management.
        Args:
            identifier (str): Card ID or person name
            is_new_card (bool): True if the card is new, False if existing
        """
        # Only allow detection if current tab is Face Recognition or Student & RFID Management
        current_tab = self.main_window.tabs.currentWidget()
        allowed_tabs = [self.main_window.recognition_tab, self.main_window.student_rfid_tab]
        if current_tab not in allowed_tabs:
            return  # Ignore detection if not in allowed tabs
        
        mode = 'add_edit' if self.main_window.rfid_mode == 'add_edit' or (hasattr(self, 'add_edit_radio') and self.add_edit_radio.isChecked()) else 'identify'
        if mode == "add_edit":
            # Add/Edit mode - show dialogs for new or existing cards
            if is_new_card:
                # This is a new card, show registration dialog
                card_id = identifier  # For new cards, identifier is the card ID
                self.handle_new_card(card_id)
            else:
                # This is an existing card, show management dialog
                person_name = identifier  # For existing cards, identifier is the person name
                card_id = self.find_card_id_by_person(person_name)
                self.handle_existing_card(card_id, person_name)
        else:
            # Identify mode - just use the card for authentication
            if not is_new_card:
                # This is an existing card, use it for authentication
                person_name = identifier  # For existing cards, identifier is the person name
                # Set RFID authentication in face system
                self.face_system.set_rfid_authentication(person_name)
                # Update RFID status in recognition tab
                self.main_window.update_rfid_status(f"RFID Card: {person_name} authenticated")
                # Show a small notification
                QMessageBox.information(self, "RFID Authentication", 
                                       f"Card authenticated for {person_name}")
            else:
                # This is a new card, show warning
                card_id = identifier
                QMessageBox.warning(self, "Unknown Card", 
                                   f"Card ID {card_id} is not registered in the system.\n\n"
                                   f"Switch to Add/Edit mode to register this card.")

    def find_card_id_by_person(self, person_name):
        """
        Find card ID by person name.
        Args:
            person_name (str): Person name
        Returns:
            str: Card ID or None if not found
        """
        for card_id, name in self.face_system.db_manager.rfid_database.items():
            if name == person_name:
                return card_id
        return None

    def handle_new_card(self, card_id):
        """
        Handle new RFID card detection.
        Args:
            card_id (str): RFID card ID
        """
        from gui.dialogs.card_dialogs import NewCardDialog
        dialog = NewCardDialog(self.face_system, card_id, self)
        if dialog.exec_():
            # Register the card
            person_name = dialog.person_name
            class_name = dialog.class_name
            # Add card to database automatically
            self.add_rfid_card(card_id, person_name)
            # Add class information to database
            if class_name:
                self.face_system.db_manager.update_student_info(person_name, {"class": class_name})
            # If user chose to capture dataset, start capture
            if dialog.should_capture:
                # Switch to capture tab
                self.main_window.tabs.setCurrentIndex(1)  # Index 1 is the capture tab
                # Set person name and class in capture form
                self.main_window.capture_tab.set_person_info(person_name, class_name)
                # Start capture
                self.main_window.capture_tab.start_capture()
            else:
                QMessageBox.information(self, "Success", f"RFID card {card_id} registered to {person_name}")

    def handle_existing_card(self, card_id, person_name):
        """
        Handle existing RFID card detection.
        Args:
            card_id (str): RFID card ID
            person_name (str): Person name
        """
        from gui.dialogs.card_dialogs import ExistingCardDialog
        dialog = ExistingCardDialog(self.face_system, card_id, person_name, self)
        if dialog.exec_():
            # Update class information
            new_class = dialog.class_name
            # Update database
            self.face_system.db_manager.update_student_info(person_name, {"class": new_class})
            # Refresh database table
            self.refresh_database()
            # If user chose to capture more dataset, start capture
            if dialog.should_capture:
                # Switch to capture tab
                self.main_window.tabs.setCurrentIndex(1)  # Index 1 is the capture tab
                # Set person name and class in capture form
                self.main_window.capture_tab.set_person_info(person_name, new_class)
                # Start capture
                self.main_window.capture_tab.start_capture()
            else:
                QMessageBox.information(self, "Success", f"Updated information for {person_name}")