"""
MySQL database manager for face recognition system (backward compatible with DatabaseManager).
"""

import mysql.connector
from typing import Dict, List, Set, Any, Optional, Tuple
from utils.logger import logger

class MySQLDatabaseManager:
    def __init__(self, host: str, user: str, password: str, database: str):
        self.conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        self.cursor = self.conn.cursor(dictionary=True)
        self._ensure_tables()

    def _ensure_tables(self):
        # Create tables if they do not exist (students, rfid, attendance, assets, encodings)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                name VARCHAR(255) PRIMARY KEY,
                data JSON
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS rfid (
                card_id VARCHAR(255) PRIMARY KEY,
                person_name VARCHAR(255)
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                date DATE,
                student_name VARCHAR(255),
                record JSON,
                PRIMARY KEY (date, student_name)
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS assets (
                asset_name VARCHAR(255) PRIMARY KEY,
                record JSON
            )
        ''')
        self.conn.commit()

    # Student database methods
    def update_student_info(self, name: str, data: Dict[str, Any]) -> bool:
        import json
        try:
            self.cursor.execute(
                "REPLACE INTO students (name, data) VALUES (%s, %s)",
                (name, json.dumps(data))
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"MySQL error updating student info: {e}")
            return False

    def get_student_info(self, name: str) -> Optional[Dict[str, Any]]:
        import json
        self.cursor.execute("SELECT data FROM students WHERE name=%s", (name,))
        row = self.cursor.fetchone()
        if row:
            return json.loads(row['data'])
        return None

    # RFID methods
    def add_rfid_card(self, card_id: str, person_name: str) -> bool:
        try:
            self.cursor.execute(
                "REPLACE INTO rfid (card_id, person_name) VALUES (%s, %s)",
                (card_id, person_name)
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"MySQL error adding RFID card: {e}")
            return False

    def remove_rfid_card(self, card_id: str) -> bool:
        try:
            self.cursor.execute("DELETE FROM rfid WHERE card_id=%s", (card_id,))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except Exception as e:
            logger.error(f"MySQL error removing RFID card: {e}")
            return False

    def get_person_by_card(self, card_id: str) -> Optional[str]:
        self.cursor.execute("SELECT person_name FROM rfid WHERE card_id=%s", (card_id,))
        row = self.cursor.fetchone()
        return row['person_name'] if row else None

    # Attendance methods
    def record_attendance(self, date: str, student_name: str, record: Dict[str, Any]) -> bool:
        import json
        try:
            self.cursor.execute(
                "REPLACE INTO attendance (date, student_name, record) VALUES (%s, %s, %s)",
                (date, student_name, json.dumps(record))
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"MySQL error recording attendance: {e}")
            return False

    def get_attendance(self, date: str) -> Dict[str, Dict[str, Any]]:
        import json
        self.cursor.execute("SELECT student_name, record FROM attendance WHERE date=%s", (date,))
        rows = self.cursor.fetchall()
        return {row['student_name']: json.loads(row['record']) for row in rows}

    def get_student_attendance_history(self, student_name: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        import json
        query = "SELECT date, record FROM attendance WHERE student_name=%s"
        params = [student_name]
        if start_date:
            query += " AND date >= %s"
            params.append(start_date)
        if end_date:
            query += " AND date <= %s"
            params.append(end_date)
        self.cursor.execute(query, tuple(params))
        rows = self.cursor.fetchall()
        return {str(row['date']): json.loads(row['record']) for row in rows}

    # Asset management methods
    def get_assets(self):
        import json
        self.cursor.execute("SELECT asset_name, record FROM assets")
        rows = self.cursor.fetchall()
        return {row['asset_name']: json.loads(row['record']) for row in rows}

    def borrow_asset(self, asset_name, borrower, classes, borrowed_at):
        import json
        record = {
            'borrower': borrower,
            'class': classes,
            'borrowed_at': borrowed_at,
            'returned_at': ''
        }
        try:
            self.cursor.execute(
                "REPLACE INTO assets (asset_name, record) VALUES (%s, %s)",
                (asset_name, json.dumps(record))
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"MySQL error borrowing asset: {e}")
            return False

    def return_asset(self, asset_name, returned_at):
        import json
        self.cursor.execute("SELECT record FROM assets WHERE asset_name=%s", (asset_name,))
        row = self.cursor.fetchone()
        if not row:
            return False
        record = json.loads(row['record'])
        if record.get('returned_at'):
            return False
        record['returned_at'] = returned_at
        try:
            self.cursor.execute(
                "UPDATE assets SET record=%s WHERE asset_name=%s",
                (json.dumps(record), asset_name)
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"MySQL error returning asset: {e}")
            return False

    def delete_asset(self, asset_name):
        try:
            self.cursor.execute("DELETE FROM assets WHERE asset_name=%s", (asset_name,))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except Exception as e:
            logger.error(f"MySQL error deleting asset: {e}")
            return False
