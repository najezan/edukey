"""
Thread for handling RFID server operations.
"""

import time
from typing import Dict, Optional, Tuple
from PyQt5.QtCore import QThread, pyqtSignal

from core.rfid_server import RFIDServer
from utils.logger import logger

class RFIDServerThread(QThread):
    """
    Thread for handling RFID card authentication from ESP32.
    
    This class runs the RFID server in a separate thread and emits signals
    when RFID cards are detected.
    """
    
    # Define PyQt signals
    rfid_detected = pyqtSignal(str, bool)  # (identifier, is_new_card)
    update_status = pyqtSignal(str)
    
    def __init__(self, face_system, port: int = 8080):
        """
        Initialize the RFID server thread.
        
        Args:
            face_system: Face recognition system
            port (int): Port to listen on
        """
        super().__init__()
        self.face_system = face_system
        self.port = port
        self.running = False
        self.rfid_database = self.face_system.db_manager.rfid_database
    
    def run(self):
        """Run RFID server."""
        self.running = True
        
        # Create RFID server
        rfid_server = RFIDServer(self.rfid_database, self.port)
        if not rfid_server.start():
            self.update_status.emit(f"Failed to start RFID server on port {self.port}")
            return
            
        self.update_status.emit(f"RFID server started on port {self.port}")
        
        # Main server loop
        while self.running:
            result = rfid_server.handle_connection()
            if result:
                card_id, is_new_card, person_name = result
                
                if not is_new_card:
                    # Existing card
                    self.rfid_detected.emit(person_name, False)
                    self.update_status.emit(f"Card authenticated for: {person_name}")
                else:
                    # New card
                    self.rfid_detected.emit(card_id, True)
                    self.update_status.emit(f"New card detected: {card_id}")
            
            # Sleep to reduce CPU usage
            time.sleep(0.01)
        
        # Stop server
        rfid_server.stop()
        self.update_status.emit("RFID server stopped")
    
    def stop(self):
        """Stop RFID server."""
        self.running = False
        logger.info("Stopping RFID server...")
