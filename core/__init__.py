"""
Core package initialization.
"""

from core.face_recognition import FaceRecognitionSystem
from core.video_stream import VideoStream
from core.rfid_server import RFIDServer

__all__ = ['FaceRecognitionSystem', 'VideoStream', 'RFIDServer']
