#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entry point untuk aplikasi Face Recognition System.
"""

import sys
import os
from PyQt5.QtWidgets import QApplication

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.legacy_adapter import FaceRecognitionSystemAdapter
from gui.main_window import FaceRecognitionGUI
from utils.logger import logger

def main():
    """
    Main function to initialize and run the Face Recognition System.
    Uses the new refactored architecture with backward compatibility.
    """

    # Initialize logger
    logger.info("Starting Face Recognition System (Refactored Architecture)")
    
    # Create application instance
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Initialize face recognition system using the new refactored architecture
    # The adapter provides complete backward compatibility with existing GUI code
    face_system = FaceRecognitionSystemAdapter()
    
    # Log system information
    stats = face_system.orchestrator.get_system_stats()
    logger.info(f"System initialized with {stats['recognition']['total_known_faces']} known faces")
    logger.info(f"CUDA available: {stats['performance']['cuda_available']}")
    logger.info(f"Detection method: {stats['performance']['detection_method']}")
    
    # Initialize GUI (unchanged - uses adapter for compatibility)
    gui = FaceRecognitionGUI(face_system)
    gui.show()
    
    logger.info("GUI initialized and displayed")
    
    # Run application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
