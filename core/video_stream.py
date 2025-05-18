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
        """
        self.stream = cv2.VideoCapture(src)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        # Set higher FPS if supported by the camera
        self.stream.set(cv2.CAP_PROP_FPS, 60)
        
        # Try to use the best backend based on the platform
        if hasattr(cv2, 'CAP_DSHOW'):
            self.stream = cv2.VideoCapture(src, cv2.CAP_DSHOW)  # DirectShow (Windows)
        elif hasattr(cv2, 'CAP_V4L2'):
            self.stream = cv2.VideoCapture(src, cv2.CAP_V4L2)  # V4L2 (Linux)
        
        # Enable OpenCL acceleration for OpenCV if available
        if cv2.ocl.haveOpenCL():
            cv2.ocl.setUseOpenCL(True)
            logger.info("OpenCL acceleration enabled for OpenCV")
        
        self.grabbed, self.frame = self.stream.read()
        self.stopped = False
        
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
        while not self.stopped:
            if not self.grabbed:
                self.stop()
            else:
                self.grabbed, self.frame = self.stream.read()
                
    def read(self):
        """
        Read the current frame.
        
        Returns:
            numpy.ndarray: The current frame
        """
        return self.frame
        
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
