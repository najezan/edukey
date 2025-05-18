"""
RFID server for handling card authentication.
"""

import socket
import json
from typing import Dict, Optional
from utils.logger import logger

class RFIDServer:
    """
    RFID server for handling card authentication.
    
    This class provides methods for starting a socket server to receive
    RFID card information from ESP32 or other clients.
    """
    
    def __init__(self, rfid_database: Dict[str, str], port: int = 8080):
        """
        Initialize the RFID server.
        
        Args:
            rfid_database (Dict[str, str]): RFID database (card_id -> person_name)
            port (int): Port to listen on
        """
        self.rfid_database = rfid_database
        self.port = port
        self.running = False
        self.server_socket = None
    
    def start(self) -> bool:
        """
        Start the RFID server.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        if self.running:
            logger.warning("RFID server already running")
            return False
        
        try:
            # Create socket server
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(5)
            self.server_socket.settimeout(1)  # 1 second timeout for non-blocking
            
            self.running = True
            logger.info(f"RFID server started on port {self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to start RFID server: {e}")
            return False
    
    def process_client(self, client_socket: socket.socket, addr: tuple) -> Optional[tuple]:
        """
        Process a client connection.
        
        Args:
            client_socket (socket.socket): Client socket
            addr (tuple): Client address
            
        Returns:
            Optional[tuple]: (card_id, is_new) or None if error
        """
        client_socket.settimeout(5)  # 5 second timeout for client operations
        
        # Read all data from client
        data_chunks = []
        while True:
            try:
                chunk = client_socket.recv(1024)
                if not chunk:
                    break
                data_chunks.append(chunk)
            except socket.timeout:
                break
        
        # Combine all chunks
        if not data_chunks:
            return None
            
        request_data = b''.join(data_chunks).decode('utf-8', errors='ignore')
        logger.debug(f"Received data from {addr}: {request_data}")
        
        # Try to parse as JSON directly first
        json_data = None
        try:
            json_data = json.loads(request_data)
            logger.debug(f"Successfully parsed as direct JSON: {json_data}")
        except json.JSONDecodeError:
            # If direct JSON parsing fails, try to extract JSON from HTTP request
            logger.debug(f"Failed to parse as direct JSON, trying to extract from HTTP")
            
            # Look for JSON in HTTP body
            try:
                # Find the start of JSON data (after headers)
                json_start = request_data.find('{')
                json_end = request_data.rfind('}')
                if json_start >= 0 and json_end >= 0:
                    json_str = request_data[json_start:json_end+1]
                    logger.debug(f"Extracted JSON string: {json_str}")
                    json_data = json.loads(json_str)
                    logger.debug(f"Successfully parsed extracted JSON: {json_data}")
            except json.JSONDecodeError as e:
                logger.error(f"JSON extraction failed: {e}")
        
        if json_data and 'card_id' in json_data:
            card_id = json_data['card_id'].upper()  # Ensure uppercase for consistency
            logger.info(f"RFID card detected: {card_id} from {addr}")
            
            # Check if card is in database
            is_new_card = card_id not in self.rfid_database
            
            if not is_new_card:
                person_name = self.rfid_database[card_id]
                response = {"status": "success", "person": person_name, "is_new": False}
                
                # Emit result
                logger.info(f"Card authenticated for: {person_name}")
                result = (card_id, False, person_name)
            else:
                response = {"status": "new_card", "message": "New card detected", "is_new": True}
                logger.info(f"New card detected: {card_id}")
                result = (card_id, True, None)
            
            # Prepare response
            response_json = json.dumps(response)
            logger.debug(f"Sending response: {response_json}")
            
            # Check if the request was HTTP
            if "HTTP" in request_data:
                # Send HTTP response
                http_response = "HTTP/1.1 200 OK\r\n"
                http_response += "Content-Type: application/json\r\n"
                http_response += "Connection: close\r\n"
                http_response += f"Content-Length: {len(response_json)}\r\n\r\n"
                http_response += response_json
                client_socket.send(http_response.encode())
            else:
                # Send simple JSON response
                client_socket.send(response_json.encode())
                
            return result
        else:
            # Send error response
            error_msg = "Invalid data format"
            error_response = {"status": "error", "message": error_msg}
            error_json = json.dumps(error_response)
            logger.error(f"Invalid data format. Sending error: {error_json}")
            
            # Check if the request was HTTP
            if "HTTP" in request_data:
                # Send HTTP error response
                http_response = "HTTP/1.1 400 Bad Request\r\n"
                http_response += "Content-Type: application/json\r\n"
                http_response += "Connection: close\r\n"
                http_response += f"Content-Length: {len(error_json)}\r\n\r\n"
                http_response += error_json
                client_socket.send(http_response.encode())
            else:
                # Send simple JSON error response
                client_socket.send(error_json.encode())
                
            return None
    
    def handle_connection(self) -> Optional[tuple]:
        """
        Handle a single connection.
        
        Returns:
            Optional[tuple]: (card_id, is_new, person_name) or None if no connection
        """
        if not self.running or not self.server_socket:
            return None
            
        try:
            client, addr = self.server_socket.accept()
            result = self.process_client(client, addr)
            client.close()
            return result
        except socket.timeout:
            # This is normal, just continue
            return None
        except Exception as e:
            logger.error(f"RFID server error: {e}")
            return None
    
    def stop(self) -> None:
        """Stop the RFID server."""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception as e:
                logger.error(f"Error closing RFID server socket: {e}")
            self.server_socket = None
        logger.info("RFID server stopped")
