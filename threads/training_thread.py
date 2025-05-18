"""
Thread for training face recognition model.
"""

import os
import time
from typing import List, Tuple, Any
from PyQt5.QtCore import QThread, pyqtSignal
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

from utils.logger import logger

class TrainingThread(QThread):
    """
    Thread for handling model training with PyQt signals.
    
    This class handles training of the face recognition model in a separate thread,
    emitting signals to update the UI with progress and status.
    """
    
    # Define PyQt signals
    update_status = pyqtSignal(str)
    update_progress = pyqtSignal(int)
    training_complete = pyqtSignal(bool)
    
    def __init__(self, face_system):
        """
        Initialize the training thread.
        
        Args:
            face_system: Face recognition system
        """
        super().__init__()
        self.face_system = face_system
    
    def run(self):
        """Train the face recognition model in a separate thread."""
        self.update_status.emit("Analyzing dataset for training...")
        
        # Get list of people in dataset directory
        dataset_people = self.face_system.db_manager.get_dataset_persons()
        
        # Filter people already trained
        new_people = dataset_people - self.face_system.trained_people
        
        if not new_people:
            self.update_status.emit("No new people to train. All people in the dataset are already trained.")
            self.training_complete.emit(False)
            return
        
        self.update_status.emit(f"Found {len(new_people)} new people to train: {', '.join(sorted(list(new_people)))}")
        self.update_status.emit("Training face recognition model using parallel processing and GPU acceleration...")
        
        if self.face_system.is_cuda_available():
            self.update_status.emit(f"Using GPU acceleration for training with {self.face_system.batch_size} parallel batches...")
        else:
            self.update_status.emit(f"Using CPU parallel processing with {self.face_system.n_cpu_cores} cores...")
        
        # Lists to store face encodings and their corresponding names for new people
        new_face_encodings = []
        new_face_names = []
        
        # Use parallel processing for faster training
        if self.face_system.is_cuda_available():
            executor_class = ThreadPoolExecutor  # Use threads for GPU to avoid device conflicts
            max_workers = self.face_system.batch_size  # Higher for GPU
        else:
            executor_class = ProcessPoolExecutor  # Use processes for CPU
            max_workers = self.face_system.n_cpu_cores
        
        # Calculate total work for progress tracking
        total_people = len(new_people)
        people_processed = 0
        
        # Process each new person
        for person_name in new_people:
            # Get image files for this person
            image_files = self.face_system.db_manager.get_person_images(person_name)
            
            self.update_status.emit(f"Processing {len(image_files)} images for {person_name}...")
            
            if not image_files:
                self.update_status.emit(f"No images found for {person_name}, skipping...")
                people_processed += 1
                self.update_progress.emit(int((people_processed / total_people) * 100))
                continue
            
            # Start time for this person
            person_start_time = time.time()
            
            # Split images into batches for parallel processing
            batch_size = max(1, len(image_files) // max_workers)
            batches = [image_files[i:i + batch_size] for i in range(0, len(image_files), batch_size)]
            
            self.update_status.emit(f"Processing {len(image_files)} images in {len(batches)} batches...")
            
            # Process batches in parallel
            encodings_list = []
            names_list = []
            
            with executor_class(max_workers=max_workers) as executor:
                # Submit all batches for processing
                futures = [executor.submit(self.face_system.process_image_batch, batch, person_name) for batch in batches]
                
                # Process results as they complete
                for i, future in enumerate(futures):
                    batch_encodings, batch_names = future.result()
                    encodings_list.extend(batch_encodings)
                    names_list.extend(batch_names)
                    
                    # Update progress
                    batch_progress = ((i + 1) / len(batches))
                    person_progress = (people_processed + batch_progress) / total_people
                    self.update_progress.emit(int(person_progress * 100))
                    
                    # Print progress
                    self.update_status.emit(f"Progress: {i+1}/{len(batches)} batches ({batch_progress*100:.1f}%)")
            
            # Add encodings and names from this person to the new lists
            new_face_encodings.extend(encodings_list)
            new_face_names.extend(names_list)
            
            person_time = time.time() - person_start_time
            self.update_status.emit(f"Added {len(encodings_list)} encodings for {person_name} in {person_time:.2f} seconds")
            
            # Update progress
            people_processed += 1
            self.update_progress.emit(int((people_processed / total_people) * 100))
        
        if not new_face_encodings:
            self.update_status.emit("No faces found in the dataset for new people.")
            self.training_complete.emit(False)
            return
        
        # Add new encodings to database
        success = self.face_system.db_manager.add_face_encodings(new_face_encodings, new_face_names)
        
        if success:
            # Update face system variables
            self.face_system.known_face_encodings = self.face_system.db_manager.face_encodings
            self.face_system.known_face_names = self.face_system.db_manager.face_names
            self.face_system.trained_people = self.face_system.db_manager.trained_people
            
            self.update_status.emit(f"Training complete! Saved {len(self.face_system.known_face_encodings)} face encodings")
            self.update_status.emit(f"Added {len(new_face_encodings)} new face encodings.")
            self.training_complete.emit(True)
        else:
            self.update_status.emit("Error saving face encodings.")
            self.training_complete.emit(False)
