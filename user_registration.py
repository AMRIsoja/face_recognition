# user_registration.py

import cv2
import face_recognition
import numpy as np
import time
import os
from database_module import DatabaseManager
from config import DATABASE_PATH, IMAGES_PATH

# Initialize the DatabaseManager
db_manager = DatabaseManager(db_path=DATABASE_PATH)

def register_new_user(user_id, name, num_images=5):
    """
    Captures a new user's face, computes its encoding, and saves it to the database.

    Args:
        user_id (str): A unique ID for the user (e.g., student ID).
        name (str): The full name of the user.
        num_images (int): The number of images to capture for a more robust encoding.
    
    Returns:
        bool: True if the user was registered successfully, False otherwise.
    """
    if not user_id or not name:
        print("User ID and Name cannot be empty.")
        return False
    
    # Check if user already exists
    if db_manager.get_user_by_id(user_id):
        print(f"Error: User with ID '{user_id}' already exists.")
        return False

    video_capture = cv2.VideoCapture(0)
    if not video_capture.isOpened():
        print("Error: Could not open video stream. Make sure a webcam is connected.")
        return False

    print("\n--- User Registration ---")
    print("Please look directly at the camera. We will capture your face in a moment.")
    print(f"Capturing {num_images} images to create a stable face encoding.")
    
    face_encodings_list = []
    images_captured = 0
    start_time = time.time()
    
    while images_captured < num_images:
        ret, frame = video_capture.read()
        if not ret:
            print("Error: Failed to read from video stream.")
            break
        
        # Convert the image from BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Find all faces in the frame
        face_locations = face_recognition.face_locations(rgb_frame)
        
        # Draw a box around the face and display instructions
        if face_locations:
            face_location = face_locations[0] # Assume the largest face is the target
            top, right, bottom, left = face_location
            
            # Draw rectangle around the face
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            
            # Display instructions
            cv2.putText(frame, "Capturing...", (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Capture an image every 2 seconds
            if time.time() - start_time > 2:
                # Get the face encoding for the detected face
                face_encoding = face_recognition.face_encodings(rgb_frame, [face_location])[0]
                face_encodings_list.append(face_encoding)
                
                print(f"Image {images_captured + 1}/{num_images} captured.")
                images_captured += 1
                start_time = time.time() # Reset the timer
                
                # Save the captured image to the known_faces directory for reference
                image_filename = f"{user_id}_{name.replace(' ', '_')}_{images_captured}.jpg"
                image_path = os.path.join(IMAGES_PATH, image_filename)
                cv2.imwrite(image_path, frame)
        else:
            # If no face is found, display a message
            cv2.putText(frame, "No face detected. Please face the camera.", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Display the video feed
        cv2.imshow('User Registration', frame)
        
        # Break the loop on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the webcam
    video_capture.release()
    cv2.destroyAllWindows()
    
    if len(face_encodings_list) > 0:
        # Compute the average of all captured face encodings
        avg_face_encoding = np.mean(face_encodings_list, axis=0)
        
        # Store the user in the database
        if db_manager.add_user(user_id, name, avg_face_encoding):
            print(f"\nUser '{name}' with ID '{user_id}' has been successfully registered.")
            return True
        else:
            print("\nError: Failed to add user to the database.")
            return False
    else:
        print("\nError: No face was successfully captured. Please try again.")
        return False

# Example usage of the registration function
if __name__ == "__main__":
    print("Welcome to the User Registration portal.")
    user_id = input("Enter a unique User ID (e.g., S001): ").strip()
    name = input("Enter the user's full name: ").strip()

    if user_id and name:
        register_new_user(user_id, name)
    else:
        print("Invalid input. Please provide a User ID and Name.")
