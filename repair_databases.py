"""
Script to repair corrupted database files
"""

from database.db_manager import DatabaseManager
from utils.logger import logger

def repair_databases():
    """Repair and reinitialize database files"""
    logger.info("Starting database repair...")
    
    # Initialize database manager which will trigger repair functionality
    db = DatabaseManager()
    
    # Save empty databases to ensure they're properly initialized
    db.save_student_database()
    db.save_rfid_database()
    db.save_face_encodings()
    db.save_attendance_database()
    
    logger.info("Database repair complete")

if __name__ == "__main__":
    repair_databases()
