import cv2
import face_recognition
import numpy as np
import time
import os
from database_module import DatabaseManager
from config import DATABASE_PATH, IMAGES_PATH, FACE_MATCH_THRESHOLD

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
    # 1. User ID validation: Check if user already exists
    if not user_id or not name:
        print("User ID and Name cannot be empty.")
        return False
    
    user_check = db_manager.get_user_by_id(user_id)
    if user_check:
        print(f"Error: User with ID '{user_id}' already exists. Please use a different ID.")
        return False
        
    video_capture = cv2.VideoCapture(0)
    try:
        if not video_capture.isOpened():
            print("Error: Could not open video stream. Make sure a webcam is connected.")
            return False

        print("\n--- User Registration ---")
        print("Please look directly at the camera. We will validate and register your face.")
        print(f"The video will terminate in 120 seconds if a face is not detected.")
        
        # Load all known face encodings and names from the database for validation
        known_users = db_manager.get_all_users()
        
        known_encodings = [user['encoding'] for user in known_users]
        known_names = [user['name'] for user in known_users]
        known_ids = [user['id'] for user in known_users]

        face_encodings_list = []
        captured_frames = []
        images_captured = 0
        start_time = time.time()
        
        # Debugging to understand the known encordings
        print("Known encodings loaded from DB:", known_encodings)
        print("Number of known encodings:", len(known_encodings))

        while True:
            ret, frame = video_capture.read()
            if not ret:
                print("Error: Failed to read from video stream.")
                break
            
            # Check for 120-second timeout
            if (time.time() - start_time) > 120:
                print("\nTimeout: The registration process has been terminated due to inactivity or no face detected.")
                break
            
            # Convert the image from BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Find all faces in the frame
            face_locations = face_recognition.face_locations(rgb_frame)
            
            if face_locations:
                face_encoding = face_recognition.face_encodings(rgb_frame, face_locations)[0]
                
                # 2. Face uniqueness validation: Check if the face is already registered
                matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=FACE_MATCH_THRESHOLD)
                if True in matches:
                    # Only then treat as already registered
                    first_match_index = matches.index(True)
                    matched_id = known_ids[first_match_index]
                    matched_name = known_names[first_match_index]
                    
                    print(f"\nValidation Error: This face is already registered.")
                    print(f"Details: Name: {matched_name}, ID: {matched_id}")
                    cv2.putText(frame, f"Already Registered as: {matched_name} ({matched_id})", 
                                (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    cv2.putText(frame, "Terminating...", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    
                    # Keep the window open for a few seconds to show the message
                    cv2.imshow('User Registration', frame)
                    cv2.waitKey(4000) # Wait for 4 seconds
                    # Deburging Face distance
                    face_distances = face_recognition.face_distance(known_encodings, face_encoding)
                    print("Face distances:", face_distances)
                    print("Matches:", matches)
                    print("Encoding dtype:", [enc.dtype for enc in known_encodings])
                    break
                
                # Draw a box around the face and display instructions
                top, right, bottom, left = face_locations[0]
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                
                # Display instructions
                cv2.putText(frame, "Capturing...", (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Capture an image every 2 seconds
                if images_captured < num_images and (time.time() - start_time) > (2 * images_captured):
                    face_encodings_list.append(face_encoding)
                    captured_frames.append(frame.copy())
                    
                    print(f"Image {images_captured + 1}/{num_images} captured.")
                    images_captured += 1
                    
                    # Exit the loop once all images are captured
                    if images_captured == num_images:
                        break
                    
            else:
                # If no face is found, display a message
                cv2.putText(frame, "No face detected. Please face the camera.", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            # Display the video feed
            cv2.imshow('User Registration', frame)
            
            # Break the loop on 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        # Release the webcam and close windows
    finally:
        video_capture.release()
        cv2.destroyAllWindows()
        
    if len(face_encodings_list) == num_images:
        # Compute the average of all captured face encodings
        avg_face_encoding = np.mean(face_encodings_list, axis=0)
        
        # Store the user in the database
        if db_manager.add_user(user_id, name, avg_face_encoding):
            # Save the captured images only on successful registration
            for i, img_frame in enumerate(captured_frames):
                image_filename = f"{user_id}_{name.replace(' ', '_')}_{i + 1}.jpg"
                image_path = os.path.join(IMAGES_PATH, image_filename)
                cv2.imwrite(image_path, img_frame)

            print(f"\nUser '{name}' with ID '{user_id}' has been successfully registered.")
            return True
        else:
            print("\nError: Failed to add user to the database.")
            return False
    else:
        print("\nRegistration incomplete. Please try again.")
        return False

if __name__ == "__main__":
    print("Welcome to the User Registration portal.")
    user_id = input("Enter a unique User ID (e.g., S001): ").strip()
    name = input("Enter the user's full name: ").strip()

    if user_id and name:
        register_new_user(user_id, name)
    else:
        print("Invalid input. Please provide a User ID and Name.")
