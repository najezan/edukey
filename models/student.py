"""
Student domain model.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class StudentStatus(Enum):
    """Student status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    GRADUATED = "graduated"


@dataclass
class Student:
    """
    Student domain model with comprehensive information and business rules.
    """
    name: str
    class_name: str
    student_id: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: StudentStatus = StudentStatus.ACTIVE
    point: int = 100
    rfid_cards: List[str] = field(default_factory=list)
    face_encodings_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization validation and setup."""
        self.validate()
        
    def validate(self) -> None:
        """
        Validate student data according to business rules.
        
        Raises:
            ValueError: If validation fails
        """
        if not self.name or len(self.name.strip()) < 2:
            raise ValueError("Student name must be at least 2 characters long")
        
        if not self.class_name or len(self.class_name.strip()) < 1:
            raise ValueError("Class name is required")
        
        if self.point < 0 or self.point > 100:
            raise ValueError("Student points must be between 0 and 100")
        
        if self.email and not self._is_valid_email(self.email):
            raise ValueError("Invalid email format")
    
    def _is_valid_email(self, email: str) -> bool:
        """Simple email validation."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def add_rfid_card(self, card_id: str) -> None:
        """
        Add RFID card to student.
        
        Args:
            card_id: RFID card identifier
            
        Raises:
            ValueError: If card already exists
        """
        if card_id in self.rfid_cards:
            raise ValueError(f"RFID card {card_id} already associated with student")
        
        self.rfid_cards.append(card_id)
        self.updated_at = datetime.now()
    
    def remove_rfid_card(self, card_id: str) -> bool:
        """
        Remove RFID card from student.
        
        Args:
            card_id: RFID card identifier
            
        Returns:
            True if card was removed, False if not found
        """
        if card_id in self.rfid_cards:
            self.rfid_cards.remove(card_id)
            self.updated_at = datetime.now()
            return True
        return False
    
    def adjust_points(self, points: int, reason: str = "") -> None:
        """
        Adjust student points with validation.
        
        Args:
            points: Points to add (positive) or subtract (negative)
            reason: Reason for point adjustment
        """
        new_points = self.point + points
        if new_points < 0:
            new_points = 0
        elif new_points > 100:
            new_points = 100
        
        self.point = new_points
        self.updated_at = datetime.now()
        
        # Log the adjustment in metadata
        if 'point_history' not in self.metadata:
            self.metadata['point_history'] = []
        
        self.metadata['point_history'].append({
            'timestamp': datetime.now().isoformat(),
            'change': points,
            'new_total': new_points,
            'reason': reason
        })
    
    def set_status(self, status: StudentStatus, reason: str = "") -> None:
        """
        Change student status.
        
        Args:
            status: New status
            reason: Reason for status change
        """
        old_status = self.status
        self.status = status
        self.updated_at = datetime.now()
        
        # Log status change in metadata
        if 'status_history' not in self.metadata:
            self.metadata['status_history'] = []
        
        self.metadata['status_history'].append({
            'timestamp': datetime.now().isoformat(),
            'old_status': old_status.value,
            'new_status': status.value,
            'reason': reason
        })
    
    def is_active(self) -> bool:
        """Check if student is active."""
        return self.status == StudentStatus.ACTIVE
    
    def can_borrow_assets(self) -> bool:
        """Check if student can borrow assets (business rule)."""
        return self.is_active() and self.point >= 50
    
    def get_display_info(self) -> Dict[str, Any]:
        """Get student information for display purposes."""
        return {
            'name': self.name,
            'class': self.class_name,
            'student_id': self.student_id,
            'status': self.status.value,
            'point': self.point,
            'rfid_cards_count': len(self.rfid_cards),
            'face_encodings_count': self.face_encodings_count,
            'created_at': self.created_at.strftime('%Y-%m-%d'),
            'can_borrow': self.can_borrow_assets()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert student to dictionary for storage."""
        return {
            'name': self.name,
            'class': self.class_name,
            'student_id': self.student_id,
            'email': self.email,
            'phone': self.phone,
            'status': self.status.value,
            'point': self.point,
            'rfid_cards': self.rfid_cards.copy(),
            'face_encodings_count': self.face_encodings_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'metadata': self.metadata.copy()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Student':
        """Create student from dictionary."""
        # Convert datetime strings back to datetime objects
        created_at = datetime.fromisoformat(data.get('created_at', datetime.now().isoformat()))
        updated_at = datetime.fromisoformat(data.get('updated_at', datetime.now().isoformat()))
        
        # Convert status string to enum
        status_str = data.get('status', 'active')
        status = StudentStatus(status_str)
        
        return cls(
            name=data['name'],
            class_name=data['class'],
            student_id=data.get('student_id'),
            email=data.get('email'),
            phone=data.get('phone'),
            status=status,
            point=data.get('point', 100),
            rfid_cards=data.get('rfid_cards', []).copy(),
            face_encodings_count=data.get('face_encodings_count', 0),
            created_at=created_at,
            updated_at=updated_at,
            metadata=data.get('metadata', {}).copy()
        )
    
    def __str__(self) -> str:
        """String representation of student."""
        return f"Student(name='{self.name}', class='{self.class_name}', status='{self.status.value}')"
    
    def __repr__(self) -> str:
        """Detailed representation of student."""
        return (f"Student(name='{self.name}', class='{self.class_name}', "
                f"student_id='{self.student_id}', status='{self.status.value}', "
                f"point={self.point}, rfid_cards={len(self.rfid_cards)})")