"""
Updated tabs package initialization to include student_rfid_tab.
"""

from gui.tabs.recognition_tab import RecognitionTab
from gui.tabs.capture_tab import CaptureTab
from gui.tabs.training_tab import TrainingTab
from gui.tabs.student_rfid_tab import StudentRFIDTab
from gui.tabs.anti_spoofing_tab import AntiSpoofingTab
from gui.tabs.settings_tab import SettingsTab

# Keep these imports for backward compatibility
from gui.tabs.database_tab import DatabaseTab
from gui.tabs.rfid_tab import RFIDTab

__all__ = [
    'RecognitionTab',
    'CaptureTab',
    'TrainingTab',
    'StudentRFIDTab',
    'AntiSpoofingTab',
    'SettingsTab',
    'DatabaseTab',
    'RFIDTab'
]