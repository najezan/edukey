"""
Database management for the face recognition system.
"""

import os
import pickle
from typing import Dict, List, Set, Any, Optional, Tuple
from utils.logger import logger

import shutil

class DatabaseManager:
    """
    Manages saving and loading of student, face encodings and RFID data.
    
    This class provides a unified interface for all database operations.
    """
    
    def __init__(self, base_dir: str = "data"):
        """
        Initialize the database manager.
        
        Args:
            base_dir (str): Base directory for all data storage
        """
        self.base_dir = base_dir
        self.trained_model_dir = os.path.join(base_dir, "trained_model")
        self.dataset_dir = os.path.join(base_dir, "dataset")
        
        # File paths
        self.encodings_file = os.path.join(self.trained_model_dir, "encodings.pickle")
        self.student_db_file = os.path.join(self.trained_model_dir, "student_database.pickle")
        self.rfid_db_file = os.path.join(self.trained_model_dir, "rfid_database.pickle")
        self.attendance_db_file = os.path.join(self.trained_model_dir, "attendance_database.pickle")
        
        # Create directories if they don't exist
        self._create_dirs()
        
        # Initialize databases
        self.student_database: Dict[str, Dict[str, Any]] = {}
        self.rfid_database: Dict[str, str] = {}  # card_id -> person_name
        self.face_encodings: List[Any] = []
        self.face_names: List[str] = []
        self.trained_people: Set[str] = set()
        self.attendance_database: Dict[str, Dict[str, Dict[str, Any]]] = {}  # date -> {student -> record}
        
        # Repair corrupted pickle files if any
        self._repair_corrupted_files()
        
        # Load data
        self._load_all_data()
        
        # Create attendance directory if it doesn't exist
        self.attendance_dir = os.path.join(base_dir, "attendance")
        if not os.path.exists(self.attendance_dir):
            os.makedirs(self.attendance_dir)
    
    def _repair_corrupted_files(self) -> None:
        """
        Check and repair corrupted pickle files by backing up and recreating empty defaults.
        """
        files_to_check = [
            (self.encodings_file, "face_encodings"),
            (self.student_db_file, "student_database"),
            (self.rfid_db_file, "rfid_database"),
            (self.attendance_db_file, "attendance_database")
        ]
        
        for file_path, attr_name in files_to_check:
            if os.path.exists(file_path):
                try:
                    with open(file_path, "rb") as f:
                        import pickle
                        pickle.load(f)
                except Exception as e:
                    logger.error(f"Corrupted pickle file detected: {file_path}. Error: {e}")
                    # Backup corrupted file
                    backup_path = file_path + ".bak"
                    try:
                        os.rename(file_path, backup_path)
                        logger.info(f"Backed up corrupted file to {backup_path}")
                    except Exception as backup_error:
                        logger.error(f"Failed to backup corrupted file {file_path}: {backup_error}")
                    
                    # Recreate empty default for the attribute
                    if attr_name == "face_encodings":
                        self.face_encodings = []
                        self.face_names = []
                        self.trained_people = set()
                    elif attr_name == "student_database":
                        self.student_database = {}
                    elif attr_name == "rfid_database":
                        self.rfid_database = {}
                    elif attr_name == "attendance_database":
                        self.attendance_database = {}
                    
                    # Save empty data to new file
                    save_method = getattr(self, f"save_{attr_name}", None)
                    if save_method:
                        save_method()
    
    def _create_dirs(self) -> None:
        """Create necessary directories if they don't exist."""
        for directory in [self.base_dir, self.trained_model_dir, self.dataset_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
                logger.info(f"Created directory: {directory}")
    
    def _load_all_data(self) -> None:
        """Load all data from disk."""
        self._load_student_database()
        self._load_rfid_database()
        self._load_face_encodings()
        self._load_attendance_database()
        self.load_asset_database()
    
    def _load_student_database(self) -> None:
        """Load student database from disk."""
        if os.path.exists(self.student_db_file):
            try:
                with open(self.student_db_file, "rb") as f:
                    self.student_database = pickle.loads(f.read())
                logger.info(f"Loaded information for {len(self.student_database)} students")
            except Exception as e:
                logger.error(f"Error loading student database: {e}")
                self.student_database = {}
    
    def _load_rfid_database(self) -> None:
        """Load RFID database from disk."""
        if os.path.exists(self.rfid_db_file):
            try:
                with open(self.rfid_db_file, "rb") as f:
                    self.rfid_database = pickle.loads(f.read())
                logger.info(f"Loaded {len(self.rfid_database)} RFID cards from database")
            except Exception as e:
                logger.error(f"Error loading RFID database: {e}")
                self.rfid_database = {}
    
    def _load_face_encodings(self) -> None:
        """Load face encodings from disk."""
        if os.path.exists(self.encodings_file):
            try:
                with open(self.encodings_file, "rb") as f:
                    data = pickle.loads(f.read())
                    self.face_encodings = data["encodings"]
                    self.face_names = data["names"]
                    # Add all trained names to the set
                    for name in self.face_names:
                        self.trained_people.add(name)
                logger.info(f"Loaded {len(self.face_encodings)} face encodings")
                logger.info(f"People already in the model: {', '.join(sorted(list(self.trained_people)))}")
            except Exception as e:
                logger.error(f"Error loading face encodings: {e}")
                self.face_encodings = []
                self.face_names = []
                self.trained_people = set()
    
    # Asset Management
    def get_assets(self):
        if not hasattr(self, 'asset_database'):
            self.asset_database = {}
        return self.asset_database

    def borrow_asset(self, asset_name, borrower, classes, borrowed_at):
        if not hasattr(self, 'asset_database'):
            self.asset_database = {}
        record = self.asset_database.get(asset_name, {})
        if record.get('borrowed_at') and not record.get('returned_at'):
            return False  # Already borrowed and not returned
        self.asset_database[asset_name] = {
            'borrower': borrower,
            'class': classes,
            'borrowed_at': borrowed_at,
            'returned_at': ''
        }
        self.save_asset_database()
        return True

    def return_asset(self, asset_name, returned_at):
        if not hasattr(self, 'asset_database'):
            self.asset_database = {}
        record = self.asset_database.get(asset_name)
        if not record or record.get('returned_at'):
            return False  # Not borrowed or already returned
        self.asset_database[asset_name]['returned_at'] = returned_at
        self.save_asset_database()
        return True

    def delete_asset(self, asset_name):
        """Delete an asset record from the database."""
        if not hasattr(self, 'asset_database'):
            self.asset_database = {}
        if asset_name in self.asset_database:
            del self.asset_database[asset_name]
            self.save_asset_database()
            return True
        return False

    def save_asset_database(self):
        import os, pickle
        asset_db_file = os.path.join(self.base_dir, 'trained_model', 'asset_database.pickle')
        os.makedirs(os.path.dirname(asset_db_file), exist_ok=True)
        with open(asset_db_file, 'wb') as f:
            pickle.dump(self.asset_database, f)

    def load_asset_database(self):
        import os, pickle
        asset_db_file = os.path.join(self.base_dir, 'trained_model', 'asset_database.pickle')
        if os.path.exists(asset_db_file):
            with open(asset_db_file, 'rb') as f:
                self.asset_database = pickle.load(f)
        else:
            self.asset_database = {}
    
    def save_student_database(self) -> bool:
        """
        Save student database to disk.
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.student_db_file), exist_ok=True)
            
            with open(self.student_db_file, "wb") as f:
                f.write(pickle.dumps(self.student_database))
            logger.info(f"Saved {len(self.student_database)} student records to database")
            return True
        except Exception as e:
            logger.error(f"Error saving student database: {e}")
            return False
    
    def save_rfid_database(self) -> bool:
        """
        Save RFID database to disk.
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.rfid_db_file), exist_ok=True)
            
            with open(self.rfid_db_file, "wb") as f:
                f.write(pickle.dumps(self.rfid_database))
            logger.info(f"Saved {len(self.rfid_database)} RFID cards to database")
            return True
        except Exception as e:
            logger.error(f"Error saving RFID database: {e}")
            return False
    
    def save_face_encodings(self) -> bool:
        """
        Save face encodings to disk.
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.encodings_file), exist_ok=True)
            
            data = {"encodings": self.face_encodings, "names": self.face_names}
            with open(self.encodings_file, "wb") as f:
                f.write(pickle.dumps(data))
            logger.info(f"Saved {len(self.face_encodings)} face encodings to {self.encodings_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving face encodings: {e}")
            return False
    
    def update_student_info(self, name: str, data: Dict[str, Any]) -> bool:
        """
        Update or add student information.
        
        Args:
            name (str): Student name
            data (Dict[str, Any]): Student data
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        self.student_database[name] = data
        return self.save_student_database()
    
    def get_student_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get student information.
        
        Args:
            name (str): Student name
            
        Returns:
            Optional[Dict[str, Any]]: Student data or None if not found
        """
        return self.student_database.get(name)
    
    def add_rfid_card(self, card_id: str, person_name: str) -> bool:
        """
        Add or update RFID card.
        
        Args:
            card_id (str): RFID card ID
            person_name (str): Person name
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        self.rfid_database[card_id] = person_name
        return self.save_rfid_database()
    
    def remove_rfid_card(self, card_id: str) -> bool:
        """
        Remove RFID card.
        
        Args:
            card_id (str): RFID card ID
            
        Returns:
            bool: True if removed and saved successfully, False otherwise
        """
        if card_id in self.rfid_database:
            del self.rfid_database[card_id]
            return self.save_rfid_database()
        return False
    
    def get_person_by_card(self, card_id: str) -> Optional[str]:
        """
        Get person name by RFID card ID.
        
        Args:
            card_id (str): RFID card ID
            
        Returns:
            Optional[str]: Person name or None if not found
        """
        return self.rfid_database.get(card_id)
    
    def add_face_encodings(self, new_encodings: List[Any], new_names: List[str]) -> bool:
        """
        Add new face encodings.
        
        Args:
            new_encodings (List[Any]): List of face encodings
            new_names (List[str]): List of person names
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        self.face_encodings.extend(new_encodings)
        self.face_names.extend(new_names)
        
        # Update trained people set
        for name in new_names:
            self.trained_people.add(name)
            
        return self.save_face_encodings()
    
    def get_dataset_persons(self) -> Set[str]:
        """
        Get set of persons in the dataset directory.
        
        Returns:
            Set[str]: Set of person names
        """
        dataset_people = set()
        if os.path.exists(self.dataset_dir):
            for item in os.listdir(self.dataset_dir):
                person_dir = os.path.join(self.dataset_dir, item)
                if os.path.isdir(person_dir):
                    dataset_people.add(item)
        return dataset_people
    
    def get_new_persons_to_train(self) -> Set[str]:
        """
        Get set of persons that need to be trained.
        
        Returns:
            Set[str]: Set of person names
        """
        return self.get_dataset_persons() - self.trained_people
    
    def get_person_images(self, person_name: str) -> List[str]:
        """
        Get list of image paths for a person.
        
        Args:
            person_name (str): Person name
            
        Returns:
            List[str]: List of image file paths
        """
        person_dir = os.path.join(self.dataset_dir, person_name)
        image_files = []
        
        if os.path.exists(person_dir) and os.path.isdir(person_dir):
            image_files = [
                os.path.join(person_dir, f) for f in os.listdir(person_dir)
                if f.lower().endswith(('.jpg', '.jpeg', '.png'))
            ]
        
        return image_files

    def _load_attendance_database(self) -> None:
        """Load attendance database from disk."""
        if os.path.exists(self.attendance_db_file):
            try:
                with open(self.attendance_db_file, "rb") as f:
                    self.attendance_database = pickle.loads(f.read())
                logger.info(f"Loaded attendance records for {len(self.attendance_database)} dates")
            except Exception as e:
                logger.error(f"Error loading attendance database: {e}")
                self.attendance_database = {}
    
    def _attendance_file_for_date(self, date: str) -> str:
        """Get the file path for a specific date's attendance."""
        return os.path.join(self.base_dir, "attendance", f"attendance_{date}.pickle")

    def get_attendance(self, date: str) -> Dict[str, Dict[str, Any]]:
        """
        Lazily load attendance records for a specific date from disk.
        
        Args:
            date (str): Date in ISO format (YYYY-MM-DD)
            
        Returns:
            Dict[str, Dict[str, Any]]: Attendance records for the date
        """
        file_path = self._attendance_file_for_date(date)
        if os.path.exists(file_path):
            try:
                with open(file_path, "rb") as f:
                    return pickle.load(f)
            except Exception as e:
                logger.error(f"Error loading attendance for {date}: {e}")
                return {}
        return {}

    def record_attendance(self, date: str, student_name: str, record: Dict[str, Any]) -> bool:
        """
        Record attendance for a student for a specific date (lazy save).
        
        Args:
            date (str): Date in ISO format (YYYY-MM-DD)
            student_name (str): Student name
            record (Dict[str, Any]): Attendance record
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        file_path = self._attendance_file_for_date(date)
        # Load existing records for the date
        attendance = self.get_attendance(date)
        attendance[student_name] = record
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "wb") as f:
                pickle.dump(attendance, f)
            logger.info(f"Saved attendance for {date}, {len(attendance)} records")
            return True
        except Exception as e:
            logger.error(f"Error saving attendance for {date}: {e}")
            return False
    
    def save_attendance_database(self) -> bool:
        """
        Save attendance database to disk.
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.attendance_db_file), exist_ok=True)
            
            with open(self.attendance_db_file, "wb") as f:
                f.write(pickle.dumps(self.attendance_database))
            logger.info(f"Saved attendance records for {len(self.attendance_database)} dates")
            return True
        except Exception as e:
            logger.error(f"Error saving attendance database: {e}")
            return False
    
    def delete_student(self, student_name: str) -> bool:
        """
        Delete a student and all associated data.
        
        This method:
        1. Removes the student from face encodings
        2. Removes the student from the student database
        3. Removes any RFID cards associated with the student
        4. Deletes the student's dataset folder
        5. Removes attendance records
        6. Saves all changes to disk
        
        Args:
            student_name (str): Name of the student to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            # Step 1: Remove from face encodings
            if student_name in self.trained_people:
                # Create lists for indices to keep
                new_encodings = []
                new_names = []
                
                # Filter out the student's encodings
                for i, name in enumerate(self.face_names):
                    if name != student_name:
                        new_encodings.append(self.face_encodings[i])
                        new_names.append(name)
                
                # Update the lists
                self.face_encodings = new_encodings
                self.face_names = new_names
                self.trained_people.remove(student_name)
                
                # Save the updated face encodings
                if not self.save_face_encodings():
                    logger.error(f"Failed to save face encodings after deleting {student_name}")
                    return False
            
            # Step 2: Remove from student database
            if student_name in self.student_database:
                del self.student_database[student_name]
                if not self.save_student_database():
                    logger.error(f"Failed to save student database after deleting {student_name}")
                    return False
            
            # Step 3: Remove any RFID cards associated with the student
            cards_to_remove = []
            for card_id, name in self.rfid_database.items():
                if name == student_name:
                    cards_to_remove.append(card_id)
            
            for card_id in cards_to_remove:
                del self.rfid_database[card_id]
            
            if cards_to_remove and not self.save_rfid_database():
                logger.error(f"Failed to save RFID database after deleting {student_name}")
                return False
            
            # Step 4: Delete the student's dataset folder
            student_dir = os.path.join(self.dataset_dir, student_name)
            if os.path.exists(student_dir):
                shutil.rmtree(student_dir)
            
            # Step 5: Remove attendance records
            for date in self.attendance_database:
                if student_name in self.attendance_database[date]:
                    del self.attendance_database[date][student_name]
            self.save_attendance_database()
            
            logger.info(f"Successfully deleted student {student_name} and all associated data")
            return True
        
        except Exception as e:
            logger.error(f"Error deleting student {student_name}: {e}")
            return False
    
    def delete_attendance_record(self, date: str, student_name: str) -> bool:
        """
        Delete a student's attendance record for a specific date.
        
        Args:
            date (str): Date in ISO format (YYYY-MM-DD)
            student_name (str): Name of the student
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        file_path = self._attendance_file_for_date(date)
        if not os.path.exists(file_path):
            return False
        try:
            with open(file_path, "rb") as f:
                attendance = pickle.load(f)
            if student_name in attendance:
                del attendance[student_name]
                with open(file_path, "wb") as f:
                    pickle.dump(attendance, f)
                logger.info(f"Deleted attendance for {student_name} on {date}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting attendance for {student_name} on {date}: {e}")
            return False
    
    def add_student(self, name: str, data: Dict[str, Any]) -> bool:
        """
        Add a new student with default point=100 if not specified.
        
        Args:
            name (str): Student name
            data (Dict[str, Any]): Student data (e.g., class, etc.)
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        if "point" not in data:
            data["point"] = 100
        self.student_database[name] = data
        return self.save_student_database()