import cv2
import numpy as np
import os
import pickle
from sklearn.neighbors import KNeighborsClassifier

class FaceRecognition:
    def __init__(self):
        self.face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.faces_data_file = 'data/faces_data.pkl'
        self.names_file = 'data/names.pkl'
        self.frames_total = 30  # Number of frames to capture
        self.capture_after_frame = 2  # Capture every nth frame
    
    def capture_face(self, callback=None):
        """Capture face images for registration"""
        video = cv2.VideoCapture(0)
        faces_data = []
        i = 0
        
        while True:
            ret, frame = video.read()
            if not ret:
                break
                
            # Create a copy for display
            display_frame = frame.copy()
            
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_detector.detectMultiScale(gray, 1.3, 5)
            
            for (x, y, w, h) in faces:
                # Crop and resize the face
                crop_img = frame[y:y+h, x:x+w]
                resized_img = cv2.resize(crop_img, (50, 50))
                
                # Save face data at intervals
                if len(faces_data) <= self.frames_total and i % self.capture_after_frame == 0:
                    faces_data.append(resized_img)
                
                i += 1
                
                # Draw rectangle around face
                cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                # Display progress
                progress = len(faces_data)
                cv2.putText(display_frame, f"Capturing: {progress}/{self.frames_total}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 120, 255), 2)
                
                # Progress bar
                progress_percent = min(progress / self.frames_total, 1.0)
                bar_width = 200
                bar_height = 20
                filled_width = int(bar_width * progress_percent)
                
                cv2.rectangle(display_frame, (10, 40), (10 + bar_width, 40 + bar_height), (200, 200, 200), -1)
                cv2.rectangle(display_frame, (10, 40), (10 + filled_width, 40 + bar_height), (0, 255, 0), -1)
            
            # Update callback with current frame if provided
            if callback and callable(callback):
                callback(display_frame)
            
            # Display the frame
            cv2.imshow('Face Capture', display_frame)
            
            # Check for exit conditions
            k = cv2.waitKey(1)
            if k == 27 or len(faces_data) >= self.frames_total:  # ESC key or enough frames
                break
        
        # Release resources
        video.release()
        cv2.destroyAllWindows()
        
        # Process and return the captured faces
        if len(faces_data) > 0:
            faces_data = np.asarray(faces_data)
            faces_data = faces_data.reshape((len(faces_data), -1))
            return faces_data
        else:
            return None
    
    def train_model(self):
        """Train the face recognition model with the saved data"""
        if not os.path.exists(self.faces_data_file) or not os.path.exists(self.names_file):
            return None
        
        # Load the data
        with open(self.faces_data_file, 'rb') as f:
            faces = pickle.load(f)
        
        with open(self.names_file, 'rb') as f:
            names = pickle.load(f)
        
        # Train the model
        model = KNeighborsClassifier(n_neighbors=5)
        model.fit(faces, names)
        
        return model
    
    def recognize_face(self, callback=None):
        """Recognize a face using the trained model"""
        # Train the model
        model = self.train_model()
        if model is None:
            return None
        
        video = cv2.VideoCapture(0)
        recognized_id = None
        confidence_threshold = 5  # Number of consistent recognitions needed
        recognition_count = {}
        
        while True:
            ret, frame = video.read()
            if not ret:
                break
            
            # Create a copy for display
            display_frame = frame.copy()
            
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_detector.detectMultiScale(gray, 1.3, 5)
            
            for (x, y, w, h) in faces:
                # Crop and resize the face
                crop_img = frame[y:y+h, x:x+w]
                resized_img = cv2.resize(crop_img, (50, 50)).flatten().reshape(1, -1)
                
                # Predict the face
                output = model.predict(resized_img)
                aadhar_id = output[0]
                
                # Count recognitions
                if aadhar_id in recognition_count:
                    recognition_count[aadhar_id] += 1
                else:
                    recognition_count[aadhar_id] = 1
                
                # Draw rectangle around face
                cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                # Display recognized ID
                cv2.putText(display_frame, f"ID: {aadhar_id}", 
                           (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Check if we have enough consistent recognitions
                if recognition_count[aadhar_id] >= confidence_threshold:
                    recognized_id = aadhar_id
            
            # Display status
            cv2.putText(display_frame, "Recognizing face...", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 120, 255), 2)
            
            # Update callback with current frame if provided
            if callback and callable(callback):
                callback(display_frame)
            
            # Display the frame
            cv2.imshow('Face Recognition', display_frame)
            
            # Check for exit conditions
            k = cv2.waitKey(1)
            if k == 27 or recognized_id is not None:  # ESC key or face recognized
                break
        
        # Release resources
        video.release()
        cv2.destroyAllWindows()
        
        return recognized_id
