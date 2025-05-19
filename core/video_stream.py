"""
Module for video stream processing.
"""

import cv2
from threading import Thread
from utils.logger import logger

class VideoStream:
    """
    Class to handle video capture in a separate thread for improved performance.
    
    This class implements the video streaming functionality with threading to improve
    performance and avoid blocking the main application thread.
    """
    
    def __init__(self, src: int = 0, width: int = 640, height: int = 480):
        """
        Initialize the video stream.
        
        Args:
            src (int): Camera source index
            width (int): Desired frame width
            height (int): Desired frame height
            
        Raises:
            RuntimeError: If camera cannot be opened or initialized
        """
        # Try to use the best backend based on the platform
        if hasattr(cv2, 'CAP_DSHOW'):
            self.stream = cv2.VideoCapture(src, cv2.CAP_DSHOW)  # DirectShow (Windows)
        elif hasattr(cv2, 'CAP_V4L2'):
            self.stream = cv2.VideoCapture(src, cv2.CAP_V4L2)  # V4L2 (Linux)
        else:
            self.stream = cv2.VideoCapture(src)  # Default backend
            
        # Verify camera opened successfully
        if not self.stream.isOpened():
            # Try fallback to default backend if platform-specific backend failed
            self.stream = cv2.VideoCapture(src)
            if not self.stream.isOpened():
                error_msg = f"Failed to open camera (index: {src})"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
        
        # Set camera properties
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.stream.set(cv2.CAP_PROP_FPS, 60)  # Set higher FPS if supported
        
        # Enable OpenCL acceleration for OpenCV if available
        if cv2.ocl.haveOpenCL():
            cv2.ocl.setUseOpenCL(True)
            logger.info("OpenCL acceleration enabled for OpenCV")
        
        # Verify we can actually read from the camera
        self.grabbed, self.frame = self.stream.read()
        if not self.grabbed or self.frame is None:
            error_msg = f"Failed to read from camera (index: {src})"
            logger.error(error_msg)
            self.stream.release()
            raise RuntimeError(error_msg)
            
        self.stopped = False
        logger.info(f"Successfully initialized camera (index: {src})")
        
    def start(self):
        """
        Start the video stream thread.
        
        Returns:
            VideoStream: self for method chaining
        """
        Thread(target=self.update, args=()).start()
        return self
        
    def update(self):
        """
        Update the frame continuously in a background thread.
        """
        consecutive_failures = 0
        max_failures = 5  # Maximum number of consecutive read failures before stopping
        
        while not self.stopped:
            self.grabbed, frame = self.stream.read()
            
            if not self.grabbed or frame is None:
                consecutive_failures += 1
                logger.warning(f"Failed to read frame (attempt {consecutive_failures}/{max_failures})")
                if consecutive_failures >= max_failures:
                    logger.error("Too many consecutive frame read failures, stopping stream")
                    self.stop()
                    break
            else:
                consecutive_failures = 0  # Reset counter on successful read
                self.frame = frame
                
    def read(self):
        """
        Read the current frame.
        
        Returns:
            numpy.ndarray: The current frame, or None if no frame is available
        """
        return self.frame if hasattr(self, 'frame') else None
        
    def stop(self):
        """
        Stop the video stream thread.
        """
        self.stopped = True
        
    def __del__(self):
        """
        Release resources when the object is deleted.
        """
        self.stop()
        if hasattr(self, 'stream') and self.stream.isOpened():
            self.stream.release()
