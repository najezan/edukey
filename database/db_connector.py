"""
MySQL database connector for the face recognition system.
"""

import mysql.connector
from mysql.connector import Error
from typing import Dict, List, Any, Optional, Tuple
import json
import pickle
from utils.logger import logger

class DatabaseConnector:
    def __init__(self, host: str, user: str, password: str, database: str, port: int = 3306):
        self.connection_params = {
            'host': host,
            'user': user,
            'password': password,
            'database': database,
            'port': port
        }
        self.connection = None
        self._connect()
        self._create_tables()
    
    def _connect(self) -> None:
        try:
            self.connection = mysql.connector.connect(**self.connection_params)
            logger.info("Successfully connected to MySQL database")
        except Error as e:
            logger.error(f"Error connecting to MySQL database: {e}")
            raise

    def _ensure_connection(self) -> None:
        try:
            if self.connection is None or not self.connection.is_connected():
                self._connect()
        except Error as e:
            logger.error(f"Error reconnecting to database: {e}")
            raise

    def _create_tables(self) -> None:
        if not self.connection:
            raise Error("No database connection")
        
        cursor = None
        try:
            cursor = self.connection.cursor()
            
            # Students table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) UNIQUE,
                    data JSON
                )
            """)
            
            # RFID cards table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rfid_cards (
                    card_id VARCHAR(255) PRIMARY KEY,
                    student_name VARCHAR(255),
                    FOREIGN KEY (student_name) REFERENCES students(name)
                )
            """)
            
            # Face encodings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS face_encodings (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    student_name VARCHAR(255),
                    encoding BLOB,
                    FOREIGN KEY (student_name) REFERENCES students(name)
                )
            """)
            
            # Attendance table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    date DATE,
                    student_name VARCHAR(255),
                    record JSON,
                    FOREIGN KEY (student_name) REFERENCES students(name)
                )
            """)
            
            # Assets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS assets (
                    asset_name VARCHAR(255) PRIMARY KEY,
                    borrower VARCHAR(255),
                    class VARCHAR(255),
                    borrowed_at DATETIME,
                    returned_at DATETIME NULL,
                    FOREIGN KEY (borrower) REFERENCES students(name)
                )
            """)
            
            self.connection.commit()
            logger.info("Database tables created successfully")
        except Error as e:
            logger.error(f"Error creating database tables: {e}")
            raise
        finally:
            if cursor:
                cursor.close()

    def save_student(self, name: str, data: Dict[str, Any]) -> bool:
        if not self.connection:
            return False
        
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "INSERT INTO students (name, data) VALUES (%s, %s) "
                "ON DUPLICATE KEY UPDATE data = %s",
                (name, json.dumps(data), json.dumps(data))
            )
            self.connection.commit()
            return True
        except Error as e:
            logger.error(f"Error saving student {name}: {e}")
            return False
        finally:
            if cursor:
                cursor.close()

    def get_student(self, name: str) -> Optional[Dict[str, Any]]:
        if not self.connection:
            return None
        
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT data FROM students WHERE name = %s", (name,))
            result = cursor.fetchone()
            if result and isinstance(result, dict) and 'data' in result:
                return json.loads(str(result['data']))
            return None
        except Error as e:
            logger.error(f"Error getting student {name}: {e}")
            return None
        finally:
            if cursor:
                cursor.close()

    def save_rfid_card(self, card_id: str, student_name: str) -> bool:
        if not self.connection:
            return False
        
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "INSERT INTO rfid_cards (card_id, student_name) VALUES (%s, %s) "
                "ON DUPLICATE KEY UPDATE student_name = %s",
                (card_id, student_name, student_name)
            )
            self.connection.commit()
            return True
        except Error as e:
            logger.error(f"Error saving RFID card {card_id}: {e}")
            return False
        finally:
            if cursor:
                cursor.close()

    def get_rfid_card(self, card_id: str) -> Optional[str]:
        if not self.connection:
            return None
        
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT student_name FROM rfid_cards WHERE card_id = %s", (card_id,))
            result = cursor.fetchone()
            if result and isinstance(result, dict) and 'student_name' in result:
                return str(result['student_name'])
            return None
        except Error as e:
            logger.error(f"Error getting RFID card {card_id}: {e}")
            return None
        finally:
            if cursor:
                cursor.close()

    def save_face_encodings(self, encodings: List[Any], names: List[str]) -> bool:
        if not self.connection:
            return False
        
        cursor = None
        try:
            cursor = self.connection.cursor()
            for encoding, name in zip(encodings, names):
                cursor.execute(
                    "INSERT INTO face_encodings (student_name, encoding) VALUES (%s, %s)",
                    (name, pickle.dumps(encoding))
                )
            self.connection.commit()
            return True
        except Error as e:
            logger.error(f"Error saving face encodings: {e}")
            return False
        finally:
            if cursor:
                cursor.close()

    def get_face_encodings(self) -> Tuple[List[Any], List[str]]:
        if not self.connection:
            return [], []
        
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT student_name, encoding FROM face_encodings")
            results = cursor.fetchall()
            
            encodings = []
            names = []
            for result in results:
                if isinstance(result, dict) and 'encoding' in result and 'student_name' in result:
                    encodings.append(pickle.loads(result['encoding']))
                    names.append(str(result['student_name']))
            
            return encodings, names
        except Error as e:
            logger.error(f"Error getting face encodings: {e}")
            return [], []
        finally:
            if cursor:
                cursor.close()

    def save_attendance(self, date: str, student_name: str, record: Dict[str, Any]) -> bool:
        if not self.connection:
            return False
        
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "INSERT INTO attendance (date, student_name, record) VALUES (%s, %s, %s) "
                "ON DUPLICATE KEY UPDATE record = %s",
                (date, student_name, json.dumps(record), json.dumps(record))
            )
            self.connection.commit()
            return True
        except Error as e:
            logger.error(f"Error saving attendance for {student_name} on {date}: {e}")
            return False
        finally:
            if cursor:
                cursor.close()

    def get_attendance(self, date: str) -> Dict[str, Dict[str, Any]]:
        if not self.connection:
            return {}
        
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT student_name, record FROM attendance WHERE date = %s", (date,))
            results = cursor.fetchall()
            
            attendance = {}
            for result in results:
                if isinstance(result, dict) and 'record' in result and 'student_name' in result:
                    attendance[str(result['student_name'])] = json.loads(str(result['record']))
            
            return attendance
        except Error as e:
            logger.error(f"Error getting attendance for {date}: {e}")
            return {}
        finally:
            if cursor:
                cursor.close()

    def close(self) -> None:
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Database connection closed")
