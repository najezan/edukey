#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entry point untuk aplikasi Face Recognition System.
"""

import sys
import os
from PyQt5.QtWidgets import QApplication

# Memastikan direktori saat ini ada di PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.face_recognition import FaceRecognitionSystem
from gui.main_window import FaceRecognitionGUI
from utils.logger import setup_logger

def main():
    """
    Fungsi utama untuk menjalankan aplikasi.
    """
    # Setup logger
    logger = setup_logger()
    logger.info("Starting Face Recognition System")
    
    # Create application
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Use Fusion style for a modern look
    
    # Create face recognition system
    face_system = FaceRecognitionSystem()
    
    # Create and show GUI
    gui = FaceRecognitionGUI(face_system)
    gui.show()
    
    # Run application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
