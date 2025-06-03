"""
Performance optimization service implementation.
"""

import multiprocessing
from typing import Dict, Any
from core.interfaces.face_recognition_interface import IPerformanceOptimizer
from utils.logger import logger


class PerformanceOptimizer(IPerformanceOptimizer):
    """
    Service responsible for performance optimization and hardware detection.
    """
    
    def __init__(self):
        """Initialize performance optimizer."""
        self._cuda_available = None
        self._cpu_cores = multiprocessing.cpu_count()
        logger.info(f"PerformanceOptimizer initialized with {self._cpu_cores} CPU cores")
    
    def is_cuda_available(self) -> bool:
        """
        Check if CUDA is available for GPU acceleration.
        
        Returns:
            True if CUDA is available, False otherwise
        """
        if self._cuda_available is not None:
            return self._cuda_available
        
        try:
            import dlib
            # Check for CUDA availability with proper error handling
            if hasattr(dlib, 'DLIB_USE_CUDA'):
                self._cuda_available = getattr(dlib, 'DLIB_USE_CUDA', False)
            else:
                self._cuda_available = False
                
            if self._cuda_available:
                logger.info("CUDA is available! GPU acceleration enabled.")
                # Set dlib's CUDA device to 0 (first GPU) if available
                try:
                    cuda_module = getattr(dlib, 'cuda', None)
                    if cuda_module and hasattr(cuda_module, 'set_device'):
                        cuda_module.set_device(0)
                except AttributeError:
                    logger.debug("CUDA device setting not available")
            else:
                logger.info("CUDA is not available. Using CPU only.")
        except ImportError:
            logger.warning("dlib not available. Cannot check CUDA status.")
            self._cuda_available = False
        except Exception as e:
            logger.warning(f"Unable to check CUDA status: {e}. Assuming CPU only.")
            self._cuda_available = False
        
        return self._cuda_available
    
    def optimize_for_hardware(self) -> Dict[str, Any]:
        """
        Get optimized settings based on available hardware.
        
        Returns:
            Dictionary containing optimized settings
        """
        cuda_available = self.is_cuda_available()
        
        optimized_settings = {
            "detection_method": "cnn" if cuda_available else "hog",
            "batch_size": 16 if cuda_available else 4,
            "num_jitters": 20 if cuda_available else 1,
            "face_model": "large" if cuda_available else "small",
            "max_workers": max(1, self._cpu_cores - 1),
            "frame_skip": 1 if cuda_available else 2,
            "cuda_available": cuda_available,
            "cpu_cores": self._cpu_cores
        }
        
        logger.info(f"Optimized settings for hardware: {optimized_settings}")
        return optimized_settings
    
    def get_recommended_batch_size(self, operation_type: str = "recognition") -> int:
        """
        Get recommended batch size for different operations.
        
        Args:
            operation_type: Type of operation ('recognition', 'training', 'encoding')
            
        Returns:
            Recommended batch size
        """
        cuda_available = self.is_cuda_available()
        
        batch_sizes = {
            "recognition": 16 if cuda_available else 4,
            "training": 32 if cuda_available else 8,
            "encoding": 8 if cuda_available else 2
        }
        
        return batch_sizes.get(operation_type, 4)
    
    def get_optimal_thread_count(self, operation_type: str = "default") -> int:
        """
        Get optimal thread count for different operations.
        
        Args:
            operation_type: Type of operation
            
        Returns:
            Optimal thread count
        """
        if operation_type == "io_bound":
            # For I/O bound operations, we can use more threads
            return min(32, self._cpu_cores * 2)
        elif operation_type == "cpu_bound":
            # For CPU bound operations, use CPU cores minus 1
            return max(1, self._cpu_cores - 1)
        else:
            # Default conservative approach
            return max(1, self._cpu_cores // 2)
    
    def should_use_gpu_acceleration(self, operation: str) -> bool:
        """
        Determine if GPU acceleration should be used for a specific operation.
        
        Args:
            operation: Operation type
            
        Returns:
            True if GPU should be used, False otherwise
        """
        if not self.is_cuda_available():
            return False
        
        # GPU is beneficial for these operations
        gpu_beneficial_ops = [
            "face_detection_cnn",
            "face_encoding_large",
            "batch_processing"
        ]
        
        return operation in gpu_beneficial_ops
    
    def get_memory_optimization_settings(self) -> Dict[str, Any]:
        """
        Get memory optimization settings.
        
        Returns:
            Dictionary with memory optimization settings
        """
        return {
            "max_frame_buffer": 10,
            "cleanup_frequency": 100,  # frames
            "gc_threshold": 50,  # MB
            "preload_models": self.is_cuda_available()
        }