"""
Domain models for the Face Recognition System.
"""

from .student import Student
from .attendance import AttendanceRecord
from .asset import Asset, AssetTransaction
from .rfid import RFIDCard
from .recognition import FaceEncoding, RecognitionEvent

__all__ = [
    'Student',
    'AttendanceRecord',
    'Asset',
    'AssetTransaction',
    'RFIDCard',
    'FaceEncoding',
    'RecognitionEvent'
]