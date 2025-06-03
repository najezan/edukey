"""
Test script to validate the refactoring implementation.
This ensures all new services work correctly and maintain backward compatibility.
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch
import numpy as np

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.services.face_detection_service import FaceDetectionService
from core.services.face_recognition_service import FaceRecognitionService
from core.services.performance_optimizer import PerformanceOptimizer
from core.services.configuration_service import ConfigurationService, FaceRecognitionConfig
from core.services.batch_processor import BatchProcessor
from core.services.face_recognition_orchestrator import FaceRecognitionOrchestrator
from core.legacy_adapter import FaceRecognitionSystemAdapter


class TestFaceDetectionService(unittest.TestCase):
    """Test the face detection service."""
    
    def setUp(self):
        self.service = FaceDetectionService("hog")
    
    def test_initialization(self):
        """Test service initialization."""
        self.assertEqual(self.service.detection_method, "hog")
    
    def test_set_detection_method(self):
        """Test setting detection method."""
        self.service.set_detection_method("cnn")
        self.assertEqual(self.service.detection_method, "cnn")
        
        # Test invalid method (should not change)
        self.service.set_detection_method("invalid")
        self.assertEqual(self.service.detection_method, "cnn")
    
    @patch('face_recognition.face_locations')
    def test_detect_faces(self, mock_face_locations):
        """Test face detection."""
        mock_face_locations.return_value = [(10, 20, 30, 40)]
        
        dummy_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        locations = self.service.detect_faces(dummy_frame)
        
        self.assertEqual(len(locations), 1)
        self.assertEqual(locations[0], (10, 20, 30, 40))
        mock_face_locations.assert_called_once()


class TestFaceRecognitionService(unittest.TestCase):
    """Test the face recognition service."""
    
    def setUp(self):
        self.service = FaceRecognitionService(tolerance=0.5)
    
    def test_initialization(self):
        """Test service initialization."""
        self.assertEqual(self.service.tolerance, 0.5)
        self.assertEqual(len(self.service.known_face_encodings), 0)
    
    def test_load_known_faces(self):
        """Test loading known faces."""
        encodings = [np.array([1, 2, 3]), np.array([4, 5, 6])]
        names = ["Person1", "Person2"]
        
        self.service.load_known_faces(encodings, names)
        
        self.assertEqual(len(self.service.known_face_encodings), 2)
        self.assertEqual(len(self.service.known_face_names), 2)
        self.assertEqual(self.service.known_face_names, names)
    
    def test_set_tolerance(self):
        """Test setting tolerance."""
        self.service.set_tolerance(0.3)
        self.assertEqual(self.service.tolerance, 0.3)
        
        # Test invalid tolerance (should not change)
        self.service.set_tolerance(1.5)
        self.assertEqual(self.service.tolerance, 0.3)
    
    def test_get_recognition_stats(self):
        """Test getting recognition statistics."""
        encodings = [np.array([1, 2, 3])]
        names = ["TestPerson"]
        self.service.load_known_faces(encodings, names)
        
        stats = self.service.get_recognition_stats()
        
        self.assertEqual(stats["total_known_faces"], 1)
        self.assertEqual(stats["tolerance"], 0.5)
        self.assertIn("TestPerson", stats["known_names"])


class TestPerformanceOptimizer(unittest.TestCase):
    """Test the performance optimizer."""
    
    def setUp(self):
        self.optimizer = PerformanceOptimizer()
    
    def test_initialization(self):
        """Test optimizer initialization."""
        self.assertIsNotNone(self.optimizer._cpu_cores)
        self.assertGreater(self.optimizer._cpu_cores, 0)
    
    def test_optimize_for_hardware(self):
        """Test hardware optimization."""
        settings = self.optimizer.optimize_for_hardware()
        
        required_keys = ["detection_method", "batch_size", "cuda_available", "cpu_cores"]
        for key in required_keys:
            self.assertIn(key, settings)
        
        self.assertIn(settings["detection_method"], ["hog", "cnn"])
        self.assertIsInstance(settings["batch_size"], int)
        self.assertIsInstance(settings["cuda_available"], bool)
    
    def test_get_recommended_batch_size(self):
        """Test batch size recommendations."""
        recognition_batch = self.optimizer.get_recommended_batch_size("recognition")
        training_batch = self.optimizer.get_recommended_batch_size("training")
        
        self.assertIsInstance(recognition_batch, int)
        self.assertIsInstance(training_batch, int)
        self.assertGreater(recognition_batch, 0)
        self.assertGreater(training_batch, 0)


class TestConfigurationService(unittest.TestCase):
    """Test the configuration service."""
    
    def setUp(self):
        self.config_service = ConfigurationService()
    
    def test_get_face_recognition_config(self):
        """Test getting face recognition configuration."""
        config = self.config_service.get_face_recognition_config()
        
        self.assertIsInstance(config, FaceRecognitionConfig)
        self.assertIsInstance(config.tolerance, float)
        self.assertIn(config.detection_method, ["hog", "cnn"])
    
    def test_update_face_recognition_config(self):
        """Test updating face recognition configuration."""
        new_config = FaceRecognitionConfig(
            tolerance=0.3,
            detection_method="cnn",
            batch_size=32
        )
        
        self.config_service.update_face_recognition_config(new_config)
        
        # Verify the update
        updated_config = self.config_service.get_face_recognition_config()
        self.assertEqual(updated_config.tolerance, 0.3)
        self.assertEqual(updated_config.detection_method, "cnn")
        self.assertEqual(updated_config.batch_size, 32)
    
    def test_observer_pattern(self):
        """Test configuration observer pattern."""
        changes_received = []
        
        def observer(changes):
            changes_received.append(changes)
        
        self.config_service.add_observer(observer)
        
        # Trigger a configuration change
        new_config = FaceRecognitionConfig(tolerance=0.4)
        self.config_service.update_face_recognition_config(new_config)
        
        # Verify observer was notified
        self.assertGreater(len(changes_received), 0)


class TestBatchProcessor(unittest.TestCase):
    """Test the batch processor."""
    
    def setUp(self):
        self.detection_service = FaceDetectionService()
        self.recognition_service = FaceRecognitionService()
        self.performance_optimizer = PerformanceOptimizer()
        
        self.batch_processor = BatchProcessor(
            self.detection_service,
            self.recognition_service, 
            self.performance_optimizer
        )
    
    def test_initialization(self):
        """Test batch processor initialization."""
        self.assertIsNotNone(self.batch_processor.detection_service)
        self.assertIsNotNone(self.batch_processor.recognition_service)
        self.assertIsNotNone(self.batch_processor.performance_optimizer)
    
    @patch('face_recognition.load_image_file')
    @patch('face_recognition.face_locations')
    @patch('face_recognition.face_encodings')
    def test_process_image_batch(self, mock_encodings, mock_locations, mock_load):
        """Test batch image processing."""
        # Mock the face_recognition functions
        mock_load.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_locations.return_value = [(10, 20, 30, 40)]
        mock_encodings.return_value = [np.array([1, 2, 3])]
        
        image_paths = ["test1.jpg", "test2.jpg"]
        encodings, names = self.batch_processor.process_image_batch(image_paths, "TestPerson")
        
        # Should process successfully
        self.assertEqual(len(names), 2)
        self.assertEqual(names[0], "TestPerson")
        self.assertEqual(names[1], "TestPerson")


class TestFaceRecognitionOrchestrator(unittest.TestCase):
    """Test the face recognition orchestrator."""
    
    def setUp(self):
        # Mock the anti-spoofing service
        self.mock_anti_spoofing = Mock()
        self.mock_anti_spoofing.is_real_face.return_value = (True, 0.9, {})
        self.mock_anti_spoofing.analyze_face_liveness.return_value = (True, 0.8, {})
        
        self.orchestrator = FaceRecognitionOrchestrator(
            base_dir="data",
            anti_spoofing_service=self.mock_anti_spoofing
        )
    
    def test_initialization(self):
        """Test orchestrator initialization."""
        self.assertIsNotNone(self.orchestrator.detection_service)
        self.assertIsNotNone(self.orchestrator.recognition_service)
        self.assertIsNotNone(self.orchestrator.batch_processor)
        self.assertIsNotNone(self.orchestrator.config_service)
    
    @patch('face_recognition.face_locations')
    @patch('face_recognition.face_encodings')
    def test_process_frame(self, mock_encodings, mock_locations):
        """Test frame processing."""
        # Mock face detection and recognition
        mock_locations.return_value = [(10, 20, 30, 40)]
        mock_encodings.return_value = [np.array([1, 2, 3])]
        
        dummy_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        result = self.orchestrator.process_frame(dummy_frame)
        
        self.assertIsNotNone(result.frame)
        self.assertIsInstance(result.processing_time, float)
        self.assertIsInstance(result.fps, float)
    
    def test_set_rfid_authentication(self):
        """Test RFID authentication setting."""
        self.orchestrator.set_rfid_authentication("TestPerson")
        
        self.assertEqual(self.orchestrator.last_rfid_person, "TestPerson")
        self.assertGreater(self.orchestrator.last_rfid_time, 0)
    
    def test_get_system_stats(self):
        """Test getting system statistics."""
        stats = self.orchestrator.get_system_stats()
        
        required_keys = ["recognition", "performance", "anti_spoofing_enabled", "current_fps"]
        for key in required_keys:
            self.assertIn(key, stats)


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with legacy adapter."""
    
    def setUp(self):
        self.adapter = FaceRecognitionSystemAdapter()
    
    def test_legacy_properties(self):
        """Test that legacy properties are available."""
        # Test properties that should exist for backward compatibility
        self.assertHasAttr(self.adapter, 'db_manager')
        self.assertHasAttr(self.adapter, 'attendance_manager')
        self.assertHasAttr(self.adapter, 'config')
        self.assertHasAttr(self.adapter, 'detection_method')
        self.assertHasAttr(self.adapter, 'face_recognition_tolerance')
        self.assertHasAttr(self.adapter, 'known_face_encodings')
        self.assertHasAttr(self.adapter, 'known_face_names')
    
    def test_legacy_methods(self):
        """Test that legacy methods are available."""
        # Test methods that should exist for backward compatibility
        self.assertTrue(hasattr(self.adapter, 'is_cuda_available'))
        self.assertTrue(hasattr(self.adapter, 'process_image_batch'))
        self.assertTrue(hasattr(self.adapter, 'process_face_recognition_batch'))
        self.assertTrue(hasattr(self.adapter, 'set_rfid_authentication'))
        self.assertTrue(hasattr(self.adapter, 'verify_two_factor_auth'))
        self.assertTrue(hasattr(self.adapter, 'update_settings'))
    
    def test_legacy_method_calls(self):
        """Test that legacy methods can be called."""
        # Test CUDA availability check
        cuda_available = self.adapter.is_cuda_available()
        self.assertIsInstance(cuda_available, bool)
        
        # Test RFID authentication
        self.adapter.set_rfid_authentication("TestPerson")
        self.assertEqual(self.adapter.last_rfid_person, "TestPerson")
        
        # Test two-factor authentication
        result, message = self.adapter.verify_two_factor_auth("TestPerson", "TestPerson")
        self.assertIsInstance(result, bool)
        self.assertIsInstance(message, str)


def run_tests():
    """Run all tests and return results."""
    # Create test suite
    test_classes = [
        TestFaceDetectionService,
        TestFaceRecognitionService,
        TestPerformanceOptimizer,
        TestConfigurationService,
        TestBatchProcessor,
        TestFaceRecognitionOrchestrator,
        TestBackwardCompatibility
    ]
    
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    print("="*50)
    print("Face Recognition System Refactoring Tests")
    print("="*50)
    
    result = run_tests()
    
    print("\n" + "="*50)
    if result.wasSuccessful():
        print("✅ All tests passed! Refactoring is successful.")
    else:
        print("❌ Some tests failed. Please check the implementation.")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
    print("="*50)