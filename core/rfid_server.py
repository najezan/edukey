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
    
    def __init__(self, rfid_database: Dict[str, str], port: int = 8080, gui_tab=None):
        """
        Initialize the RFID server.
        
        Args:
            rfid_database (Dict[str, str]): RFID database (card_id -> person_name)
            port (int): Port to listen on
            gui_tab: Reference to the StudentRFIDTab for getting mode
        """
        self.rfid_database = rfid_database
        self.port = port
        self.running = False
        self.server_socket = None
        self.gui_tab = gui_tab
    
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
        try:
            client_socket.settimeout(10)  # Increased timeout for client operations
            
            # Read all data from client
            data_chunks = []
            total_received = 0
            max_size = 4096  # Limit maximum request size
            
            while total_received < max_size:
                try:
                    chunk = client_socket.recv(1024)
                    if not chunk:
                        break
                    data_chunks.append(chunk)
                    total_received += len(chunk)
                    
                    # Check if we have a complete HTTP request
                    combined_data = b''.join(data_chunks)
                    if b'\r\n\r\n' in combined_data:
                        # We have headers, check if we have the complete body
                        headers_end = combined_data.find(b'\r\n\r\n')
                        headers = combined_data[:headers_end].decode('utf-8', errors='ignore')
                        
                        # Look for Content-Length
                        content_length = 0
                        for line in headers.split('\r\n'):
                            if line.lower().startswith('content-length:'):
                                try:
                                    content_length = int(line.split(':')[1].strip())
                                except:
                                    pass
                        
                        # Check if we have the complete body
                        body_start = headers_end + 4
                        body_received = len(combined_data) - body_start
                        if body_received >= content_length:
                            break
                            
                except socket.timeout:
                    break
                except Exception as e:
                    logger.error(f"Error reading from client: {e}")
                    break
            
            # Combine all chunks
            if not data_chunks:
                logger.warning(f"No data received from {addr}")
                self._send_error_response(client_socket, "No data received", is_http=True)
                return None
                
            request_data = b''.join(data_chunks).decode('utf-8', errors='ignore')
            logger.debug(f"Received data from {addr}: {request_data}")
            
            # Check if this is an HTTP request
            is_http_request = request_data.startswith('POST') or request_data.startswith('GET')
            
            json_data = None
            
            if is_http_request:
                # Parse HTTP request
                try:
                    # Split headers and body
                    if '\r\n\r\n' in request_data:
                        headers, body = request_data.split('\r\n\r\n', 1)
                        logger.debug(f"HTTP headers: {headers}")
                        logger.debug(f"HTTP body: {body}")
                        
                        # Check if this is a POST request to /rfid
                        if 'POST /rfid' in headers or 'POST /' in headers:
                            # Try to parse the body as JSON
                            if body.strip():
                                json_data = json.loads(body.strip())
                                logger.debug(f"Successfully parsed JSON from HTTP body: {json_data}")
                            else:
                                raise json.JSONDecodeError("Empty body", "", 0)
                        else:
                            # Not a supported endpoint
                            error_msg = "Endpoint not supported. Use POST /rfid"
                            self._send_http_error(client_socket, 404, error_msg)
                            return None
                    else:
                        raise ValueError("Invalid HTTP request format")
                        
                except (json.JSONDecodeError, ValueError) as e:
                    logger.error(f"HTTP request parsing failed: {e}")
                    error_msg = "Invalid HTTP request or JSON format"
                    self._send_http_error(client_socket, 400, error_msg)
                    return None
            else:
                # Try to parse as JSON directly (backward compatibility)
                try:
                    json_data = json.loads(request_data.strip())
                    logger.debug(f"Successfully parsed JSON: {json_data}")
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parsing failed: {e}")
                    error_msg = "Invalid JSON format"
                    self._send_error_response(client_socket, error_msg, is_http=False)
                    return None
            
            # Process the JSON data
            if json_data and 'card_id' in json_data:
                card_id = json_data['card_id'].upper()  # Ensure uppercase for consistency
                
                # Get mode from GUI instead of ESP32
                if self.gui_tab and hasattr(self.gui_tab, 'identify_radio'):
                    mode = 'identify' if self.gui_tab.identify_radio.isChecked() else 'add_edit'
                elif self.gui_tab and hasattr(self.gui_tab, 'main_window') and hasattr(self.gui_tab.main_window, 'rfid_mode'):
                    mode = self.gui_tab.main_window.rfid_mode
                else:
                    mode = json_data.get('mode', 'identify')  # Fallback to ESP32 mode if no GUI
                
                logger.info(f"RFID card detected: {card_id} from {addr}, mode: {mode} (from GUI)")
                
                # Check if card is in database
                is_new_card = card_id not in self.rfid_database
                
                if not is_new_card:
                    person_name = self.rfid_database[card_id]
                    if mode == 'identify':
                        response = {"status": "success", "message": f"Welcome {person_name}", "person": person_name, "is_new": False, "mode": mode}
                    else:  # add_edit mode
                        response = {"status": "success", "message": f"Card registered to {person_name}", "person": person_name, "is_new": False, "mode": mode}
                    logger.info(f"Card authenticated for: {person_name}")
                    result = (card_id, False, person_name)
                else:
                    if mode == 'identify':
                        response = {"status": "error", "message": "Unknown card, register first.", "is_new": True, "mode": mode}
                    else:  # add_edit mode
                        response = {"status": "success", "message": "Ready to register new card", "is_new": True, "mode": mode}
                    logger.info(f"New card detected: {card_id}")
                    result = (card_id, True, None)
                
                # Send response
                response_json = json.dumps(response)
                logger.debug(f"Sending response: {response_json}")
                
                if is_http_request:
                    self._send_http_response(client_socket, 200, response_json)
                else:
                    client_socket.send(response_json.encode())
                
                return result
            else:
                error_msg = "Missing 'card_id' in JSON"
                if is_http_request:
                    self._send_http_error(client_socket, 400, error_msg)
                else:
                    self._send_error_response(client_socket, error_msg, is_http=False)
                
                return None
                
        except Exception as e:
            logger.error(f"Unexpected error processing client {addr}: {e}")
            try:
                self._send_error_response(client_socket, "Internal server error", is_http=True)
            except:
                pass
            return None
    
    def _send_http_response(self, client_socket: socket.socket, status_code: int, json_body: str) -> None:
        """Send an HTTP response with JSON body."""
        try:
            status_text = "OK" if status_code == 200 else "Bad Request" if status_code == 400 else "Not Found"
            http_response = f"HTTP/1.1 {status_code} {status_text}\r\n"
            http_response += "Content-Type: application/json\r\n"
            http_response += "Connection: close\r\n"
            http_response += f"Content-Length: {len(json_body)}\r\n\r\n"
            http_response += json_body
            
            client_socket.send(http_response.encode())
            logger.debug(f"Sent HTTP response: {status_code} {status_text}")
        except Exception as e:
            logger.error(f"Error sending HTTP response: {e}")
    
    def _send_http_error(self, client_socket: socket.socket, status_code: int, error_message: str) -> None:
        """Send an HTTP error response."""
        error_response = {"status": "error", "message": error_message}
        error_json = json.dumps(error_response)
        self._send_http_response(client_socket, status_code, error_json)
    
    def _send_error_response(self, client_socket: socket.socket, error_message: str, is_http: bool = True) -> None:
        """Send an error response (HTTP or raw JSON)."""
        try:
            error_response = {"status": "error", "message": error_message}
            error_json = json.dumps(error_response)
            
            if is_http:
                self._send_http_response(client_socket, 400, error_json)
            else:
                client_socket.send(error_json.encode())
            
            logger.debug(f"Sent error response: {error_message}")
        except Exception as e:
            logger.error(f"Error sending error response: {e}")

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
