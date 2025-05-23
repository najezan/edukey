"""
Attendance management system for face recognition-based attendance tracking.
"""

import os
import json
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Tuple
from utils.logger import logger
from utils.config import Config
import cv2 # Import OpenCV
import face_recognition
import numpy as np

class AttendanceManager:
    """
    Manages attendance tracking and reporting.
    """
    
    def __init__(self, db_manager, config=None):
        """
        Initialize the attendance manager.
        
        Args:
            db_manager: DatabaseManager instance for data storage
            config: Config instance (optional)
        """
        self.db_manager = db_manager
        self.config = config or Config()
        
        # Load attendance rules from config
        cutoff_time = self.config.get("attendance_late_cutoff", "09:00")
        hours, minutes = map(int, cutoff_time.split(":"))
        
        self.attendance_rules = {
            "min_confidence": int(self.config.get("attendance_min_confidence", 85)),
            "late_cutoff": time(hours, minutes),
            "cooldown": self.config.get("attendance_cooldown", 5)  # minutes
        }
        
        # Cache for last attendance time per person
        self.last_attendance = {}
        self.attendance_image_dir = os.path.join("data", "attendance", "images")
        os.makedirs(self.attendance_image_dir, exist_ok=True)

    def mark_attendance(self, 
                       student_name: str, 
                       confidence: float, 
                       frame, # Add frame parameter
                       verification_method: str = "face",
                       class_info: Optional[str] = None) -> Tuple[bool, str]:
        """
        Mark attendance for a student.
        
        Args:
            student_name (str): Name of the student
            confidence (float): Face recognition confidence score
            frame: The image frame captured when attendance is marked
            verification_method (str): Method of verification (face/face+rfid)
            class_info (Optional[str]): Student's class information
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Check confidence threshold
            if confidence < self.attendance_rules["min_confidence"]:
                return False, f"Confidence too low: {confidence}%"
            
            # Check cooldown period
            current_time = datetime.now()
            if student_name in self.last_attendance:
                time_since_last = current_time - self.last_attendance[student_name]
                if time_since_last < timedelta(minutes=self.attendance_rules["cooldown"]):
                    # Get previous attendance status
                    current_date = current_time.date().isoformat()
                    attendance_records = self.db_manager.get_attendance(current_date)
                    if student_name in attendance_records:
                        prev_status = attendance_records[student_name].get('status', 'unknown')
                        # Map status to 'hadir' or 'late'
                        if prev_status == 'present':
                            prev_status_display = 'hadir'
                        elif prev_status == 'late':
                            prev_status_display = 'telat'
                        else:
                            prev_status_display = prev_status
                        return False, f"{prev_status_display}"
                    return False, "Already marked attendance"
            
            current_date = current_time.date().isoformat()
            
            # Get student info
            student_info = self.db_manager.get_student_info(student_name)
            if not student_info:
                return False, "Student not found in database"
            
            # Determine attendance status
            current_time_obj = current_time.time()
            if current_time_obj <= self.attendance_rules["late_cutoff"]:
                status = "present"
            else:
                status = "late"
                # Subtract 5 points if student is late
                if hasattr(self.db_manager, 'student_database') and student_name in self.db_manager.student_database:
                    current_point = self.db_manager.student_database[student_name].get("point", 100)
                    new_point = max(0, current_point - 5)
                    self.db_manager.student_database[student_name]["point"] = new_point
                    self.db_manager.save_student_database()

            # Update last attendance time
            self.last_attendance[student_name] = current_time

            # Save the captured frame
            image_path = ""
            if frame is not None:
                try:
                    rgb_frame = frame.copy()
                    if len(rgb_frame.shape) == 3 and rgb_frame.shape[2] == 3:
                        face_locations = face_recognition.face_locations(rgb_frame)
                        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                        known_encodings = getattr(self.db_manager, 'face_encodings', None)
                        known_names = getattr(self.db_manager, 'face_names', None)
                        if known_encodings is None or known_names is None:
                            try:
                                from core.face_recognition import FaceRecognitionSystem
                                face_system = FaceRecognitionSystem()
                                known_encodings = face_system.known_face_encodings
                                known_names = face_system.known_face_names
                            except Exception:
                                known_encodings = []
                                known_names = []
                        # Only label the face of the attended student
                        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                            name = "Unknown"
                            if known_encodings and known_names:
                                matches = face_recognition.compare_faces(known_encodings, face_encoding)
                                face_distances = face_recognition.face_distance(known_encodings, face_encoding)
                                if len(face_distances) > 0:
                                    import numpy as np
                                    best_match_index = np.argmin(face_distances)
                                    if matches[best_match_index]:
                                        name = known_names[best_match_index]
                            if name == student_name:
                                label = name
                                label_class = ""
                                if hasattr(self.db_manager, 'student_database') and name in self.db_manager.student_database:
                                    label_class = self.db_manager.student_database[name].get("class", "")
                                cv2.rectangle(rgb_frame, (left, top), (right, bottom), (0, 255, 0), 2)
                                if class_info or label_class:
                                    label += f" ({class_info or label_class})"
                                cv2.putText(rgb_frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    timestamp_str = current_time.strftime("%Y%m%d_%H%M%S_%f")
                    image_filename = f"{student_name}_{timestamp_str}.jpg"
                    image_path = os.path.join(self.attendance_image_dir, image_filename)
                    os.makedirs(os.path.dirname(image_path), exist_ok=True)
                    cv2.imwrite(image_path, rgb_frame)
                    logger.info(f"Saved attendance image to {image_path}")
                except Exception as e:
                    logger.error(f"Failed to save attendance image: {e}")
                    image_path = "" # Reset path if saving failed

            # Create attendance record
            attendance_record = {
                "time_in": current_time.strftime("%H:%M:%S"),
                "confidence": confidence,
                "verification_method": verification_method,
                "class": class_info or student_info.get("class", ""),
                "status": status,
                "image_path": image_path  # Add image path to record
            }
            
            # Save attendance
            success = self.db_manager.record_attendance(
                current_date, student_name, attendance_record)
            
            if success:
                return True, f"Attendance marked: {status}"
            else:
                return False, "Failed to save attendance"
                
        except Exception as e:
            logger.error(f"Error marking attendance: {e}")
            return False, f"Error marking attendance: {str(e)}"
    
    def get_daily_attendance(self, date: Optional[str] = None) -> Dict:
        """
        Get attendance records for a specific date.
        
        Args:
            date (Optional[str]): Date in ISO format (YYYY-MM-DD). 
                                If None, returns today's attendance.
            
        Returns:
            Dict: Attendance records for the date
        """
        if date is None:
            date = datetime.now().date().isoformat()
        
        return self.db_manager.get_attendance(date)
    
    def get_class_attendance(self, class_name: str, date: Optional[str] = None) -> Dict:
        """
        Get attendance records for a specific class.
        
        Args:
            class_name (str): Name of the class
            date (Optional[str]): Date in ISO format (YYYY-MM-DD)
            
        Returns:
            Dict: Attendance records for the class
        """
        daily_attendance = self.get_daily_attendance(date)
        class_attendance = {}
        
        for student_name, record in daily_attendance.items():
            if record.get("class") == class_name:
                class_attendance[student_name] = record
        
        return class_attendance
    
    def get_student_attendance_history(self, student_name: str, 
                                     start_date: Optional[str] = None, 
                                     end_date: Optional[str] = None) -> Dict:
        """
        Get attendance history for a specific student.
        
        Args:
            student_name (str): Name of the student
            start_date (Optional[str]): Start date in ISO format
            end_date (Optional[str]): End date in ISO format
            
        Returns:
            Dict: Student's attendance history
        """
        return self.db_manager.get_student_attendance_history(
            student_name, start_date, end_date)
    
    def update_attendance_rules(self, rules: Dict) -> None:
        """
        Update attendance rules.
        
        Args:
            rules (Dict): New rules to apply
        """
        if "attendance_late_cutoff" in rules:
            hours, minutes = map(int, rules["attendance_late_cutoff"].split(":"))
            self.attendance_rules["late_cutoff"] = time(hours, minutes)
        
        if "attendance_min_confidence" in rules:
            self.attendance_rules["min_confidence"] = int(rules["attendance_min_confidence"])
            
        if "attendance_cooldown" in rules:
            self.attendance_rules["cooldown"] = int(rules["attendance_cooldown"])
        
        # Save to config
        self.config.update({
            "attendance_min_confidence": self.attendance_rules["min_confidence"],
            "attendance_late_cutoff": f"{self.attendance_rules['late_cutoff'].strftime('%H:%M')}",
            "attendance_cooldown": self.attendance_rules["cooldown"]
        })
        self.config.save_config()
