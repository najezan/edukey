"""
RFID tab for managing RFID cards.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
                           QPushButton, QLabel, QTableWidget, QTableWidgetItem, 
                           QLineEdit, QComboBox, QRadioButton, QMessageBox,
                           QInputDialog)
from PyQt5.QtCore import Qt, pyqtSignal

from utils.logger import logger

class RFIDTab(QWidget):
    """
    Tab for managing RFID cards and server.
    
    This tab contains controls for managing RFID cards, server settings,
    and server control.
    """
    
    # Define signals
    mode_changed = pyqtSignal(str)  # Mode ('identify' or 'add_edit')
    
    def __init__(self, face_system, main_window):
        """
        Initialize the RFID tab.
        
        Args:
            face_system: Face recognition system
            main_window: Main window for RFID server access
        """
        super().__init__()
        self.face_system = face_system
        self.main_window = main_window
        
        # Initialize UI components
        self._init_ui()
        
        # Initialize table
        self.refresh_rfid_table()
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()
        
        # Create RFID card table
        self.rfid_table = QTableWidget()
        self.rfid_table.setColumnCount(2)
        self.rfid_table.setHorizontalHeaderLabels(["Card ID", "Person"])
        self.rfid_table.horizontalHeader().setStretchLastSection(True)
        
        # Create form for adding new cards
        form_layout = QFormLayout()
        self.card_id_input = QLineEdit()
        self.card_id_input.setPlaceholderText("Scan card or enter ID manually")
        
        self.person_combo = QComboBox()
        self.refresh_person_combo()
        
        form_layout.addRow("Card ID:", self.card_id_input)
        form_layout.addRow("Person:", self.person_combo)
        
        # Create control buttons
        button_layout = QHBoxLayout()
        self.scan_button = QPushButton("Scan New Card")
        self.add_button = QPushButton("Add Card")
        self.delete_button = QPushButton("Delete Selected")
        self.refresh_button = QPushButton("Refresh")
        
        button_layout.addWidget(self.scan_button)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.refresh_button)
        
        # Connect buttons
        self.scan_button.clicked.connect(self.scan_rfid_card)
        self.add_button.clicked.connect(self.add_rfid_card)
        self.delete_button.clicked.connect(self.delete_rfid_card)
        self.refresh_button.clicked.connect(self.refresh_rfid_table)
        
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
        
        # Add widgets to layout
        layout.addWidget(self.rfid_table)
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)
        layout.addWidget(mode_group)
        layout.addWidget(self.server_status)
        layout.addLayout(server_button_layout)
        
        # Set layout for tab
        self.setLayout(layout)
    
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
    
    def add_rfid_card(self):
        """Add RFID card to database."""
        card_id = self.card_id_input.text().strip().upper()
        person_name = self.person_combo.currentText()
        
        if not card_id:
            QMessageBox.warning(self, "Warning", "Please scan an RFID card first.")
            return
        
        if not person_name:
            QMessageBox.warning(self, "Warning", "Please select a person.")
            return
        
        # Check if card already exists
        if card_id in self.face_system.db_manager.rfid_database:
            reply = QMessageBox.question(
                self, "Confirmation", 
                f"This card is already registered to {self.face_system.db_manager.rfid_database[card_id]}. Do you want to reassign it?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        # Add card to database
        self.face_system.db_manager.add_rfid_card(card_id, person_name)
        
        # Refresh table
        self.refresh_rfid_table()
        
        # Clear card ID field
        self.card_id_input.clear()
        
        QMessageBox.information(self, "Success", f"RFID card {card_id} assigned to {person_name}")
        logger.info(f"RFID card {card_id} assigned to {person_name}")
    
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
