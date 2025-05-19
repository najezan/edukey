"""
Updated tabs package initialization to include anti-spoofing tab.
"""

from gui.tabs.recognition_tab import RecognitionTab
from gui.tabs.capture_tab import CaptureTab
from gui.tabs.training_tab import TrainingTab
from gui.tabs.database_tab import DatabaseTab
from gui.tabs.rfid_tab import RFIDTab
from gui.tabs.settings_tab import SettingsTab
from gui.tabs.anti_spoofing_tab import AntiSpoofingTab

__all__ = [
    'RecognitionTab',
    'CaptureTab',
    'TrainingTab',
    'DatabaseTab',
    'RFIDTab',
    'SettingsTab',
    'AntiSpoofingTab'
]