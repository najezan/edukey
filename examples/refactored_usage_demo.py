"""
Demo script showing how to use the refactored Face Recognition System.

This demonstrates the new service-oriented architecture and how it provides
better separation of concerns, improved testability, and cleaner code.
"""

import sys
import os
import numpy as np

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.services.face_recognition_orchestrator import FaceRecognitionOrchestrator
from core.legacy_adapter import FaceRecognitionSystemAdapter
from core.anti_spoofing import AntiSpoofingSystem
from utils.logger import logger


def demo_new_architecture():
    """Demonstrate the new service-oriented architecture."""
    print("\n=== New Service-Oriented Architecture Demo ===")
    
    # Initialize anti-spoofing service
    anti_spoofing_service = AntiSpoofingSystem()
    
    # Initialize the new orchestrator
    orchestrator = FaceRecognitionOrchestrator(
        base_dir="data",
        anti_spoofing_service=anti_spoofing_service
    )
    
    # Get system statistics
    stats = orchestrator.get_system_stats()
    print(f"System initialized with {stats['recognition']['total_known_faces']} known faces")
    print(f"CUDA available: {stats['performance']['cuda_available']}")
    print(f"Detection method: {stats['performance']['detection_method']}")
    print(f"Anti-spoofing enabled: {stats['anti_spoofing_enabled']}")
    
    # Simulate frame processing
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    result = orchestrator.process_frame(dummy_frame)
    
    print(f"Processed frame in {result.processing_time:.3f}s")
    print(f"Found {len(result.face_locations)} faces")
    print(f"Recognitions: {len(result.recognitions)}")
    
    # Update settings example
    new_settings = {
        "face_recognition_tolerance": 0.5,
        "detection_method": "hog",
        "enable_anti_spoofing": True
    }
    orchestrator.update_settings(new_settings)
    print("Settings updated successfully")


def demo_backward_compatibility():
    """Demonstrate backward compatibility with legacy code."""
    print("\n=== Backward Compatibility Demo ===")
    
    # Use the adapter to maintain compatibility with existing code
    face_system = FaceRecognitionSystemAdapter(base_dir="data")
    
    # All legacy properties and methods should work
    print(f"Detection method: {face_system.detection_method}")
    print(f"Face recognition tolerance: {face_system.face_recognition_tolerance}")
    print(f"CUDA available: {face_system.is_cuda_available()}")
    print(f"Known faces: {len(face_system.known_face_encodings)}")
    print(f"Trained people: {len(face_system.trained_people)}")
    
    # Legacy method calls should work
    face_system.set_rfid_authentication("John Doe")
    print(f"RFID authentication set for: {face_system.last_rfid_person}")
    
    # Legacy batch processing
    dummy_batch = [(np.zeros((480, 640, 3), dtype=np.uint8), 
                   np.zeros((480, 640, 3), dtype=np.uint8), 
                   0.25)]
    
    results = face_system.process_face_recognition_batch(dummy_batch)
    print(f"Processed batch with {len(results)} frames")


def demo_individual_services():
    """Demonstrate using individual services directly."""
    print("\n=== Individual Services Demo ===")
    
    from core.services.face_detection_service import FaceDetectionService
    from core.services.face_recognition_service import FaceRecognitionService
    from core.services.performance_optimizer import PerformanceOptimizer
    from core.services.configuration_service import ConfigurationService
    
    # Use services individually for specific tasks
    config_service = ConfigurationService()
    performance_optimizer = PerformanceOptimizer()
    
    # Get optimal settings
    optimal_settings = performance_optimizer.optimize_for_hardware()
    print(f"Optimal settings: {optimal_settings}")
    
    # Initialize detection service with optimal method
    detection_service = FaceDetectionService(optimal_settings["detection_method"])
    
    # Initialize recognition service with configuration
    face_config = config_service.get_face_recognition_config()
    recognition_service = FaceRecognitionService(
        tolerance=face_config.tolerance,
        model=face_config.model
    )
    
    # Test face detection
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    face_locations = detection_service.detect_faces(dummy_frame)
    print(f"Detected {len(face_locations)} faces")
    
    # Get recognition statistics
    stats = recognition_service.get_recognition_stats()
    print(f"Recognition service stats: {stats}")


def demo_configuration_management():
    """Demonstrate centralized configuration management."""
    print("\n=== Configuration Management Demo ===")
    
    from core.services.configuration_service import (
        ConfigurationService, 
        FaceRecognitionConfig,
        AntiSpoofingConfig,
        PerformanceConfig
    )
    
    config_service = ConfigurationService()
    
    # Get current configurations
    face_config = config_service.get_face_recognition_config()
    anti_spoofing_config = config_service.get_anti_spoofing_config()
    performance_config = config_service.get_performance_config()
    
    print(f"Face recognition tolerance: {face_config.tolerance}")
    print(f"Detection method: {face_config.detection_method}")
    print(f"Anti-spoofing enabled: {anti_spoofing_config.enabled}")
    print(f"Performance frame skip: {performance_config.frame_skip}")
    
    # Update configuration with type-safe objects
    new_face_config = FaceRecognitionConfig(
        tolerance=0.4,
        detection_method="cnn",
        batch_size=32
    )
    
    config_service.update_face_recognition_config(new_face_config)
    print("Face recognition configuration updated")
    
    # Configuration observer pattern
    def on_config_change(changes):
        print(f"Configuration changed: {list(changes.keys())}")
    
    config_service.add_observer(on_config_change)
    
    # Test observer notification
    new_performance_config = PerformanceConfig(frame_skip=2, use_gpu=True)
    config_service.update_performance_config(new_performance_config)


def main():
    """Run all demos."""
    logger.info("Starting Face Recognition System Refactoring Demo")
    
    try:
        demo_new_architecture()
        demo_backward_compatibility()
        demo_individual_services()
        demo_configuration_management()
        
        print("\n=== Demo Complete ===")
        print("The refactored system provides:")
        print("✓ Better separation of concerns")
        print("✓ Improved testability")
        print("✓ Type safety")
        print("✓ Configuration management")
        print("✓ Performance optimization")
        print("✓ Backward compatibility")
        print("✓ Modular architecture")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"Error running demo: {e}")


if __name__ == "__main__":
    main()