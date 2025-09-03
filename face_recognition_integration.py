import cv2
import face_recognition
import numpy as np
import os
import time
from datetime import datetime
from database_module import DatabaseManager
from config import DATABASE_PATH

# Initialize the DatabaseManager
db_manager = DatabaseManager(db_path=DATABASE_PATH)

def load_known_faces():
    """
    Loads all known face encodings and names from the database.
    
    Returns:
        list, list, list: A tuple containing lists of known face encodings,
                         names, and user IDs.
    """
    print("Loading known faces from the database...")
    users = db_manager.get_all_users()
    
    known_face_encodings = [user['encoding'] for user in users]
    known_face_names = [user['name'] for user in users]
    known_face_user_ids = [user['id'] for user in users]
    
    print(f"Loaded {len(known_face_encodings)} known faces.")
    return known_face_encodings, known_face_names, known_face_user_ids

def mark_attendance(user_id):
    """
    Marks the attendance for a given user ID.
    
    Args:
        user_id (str): The ID of the user to mark attendance for.
    """
    # Check if a record exists for today
    today = datetime.now().strftime("%Y-%m-%d")
    record = db_manager.get_attendance_record(user_id, today)
    
    if record:
        print(f"Attendance already marked for user {user_id} today.")
        return True # Return True to indicate attendance was handled
    else:
        # Mark attendance for the user
        db_manager.add_attendance_record(user_id, today)
        print(f"Attendance marked for user {user_id}.")
        return True # Return True to indicate attendance was handled

def run_face_recognition():
    """
    Main function to run the face recognition attendance system.
    """
    # Load known faces and their IDs
    known_face_encodings, known_face_names, known_face_user_ids = load_known_faces()
    
    if not known_face_encodings:
        print("No registered faces found. Please register a user first using user_registration.py")
        return

    # Initialize video capture
    video_capture = cv2.VideoCapture(0)
    try:
        if not video_capture.isOpened():
            print("Error: Could not open video stream. Make sure a webcam is connected.")
            return

        print("\n--- Face Recognition Attendance System ---")
        print("Press 'q' to quit.")
        print("Press 'm' for manual attendance entry.")

        # Variables for tracking attendance status and timeout
        last_detected_time = {} # Stores the last time a face was detected for each user
        detection_threshold = 5 # seconds
        
        start_time = time.time()
        face_detected_after_start = False

        while True:
            ret, frame = video_capture.read()
            if not ret or frame is None:
                print("Error: Failed to read from video stream.")
                break

            # Ensure frame is in the correct format
            if frame.dtype != np.uint8:
                frame = frame.astype(np.uint8)
            if len(frame.shape) == 2:  # grayscale, convert to BGR
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            
            # Check for 120-second timeout if no face has been detected yet
            if not face_detected_after_start and (time.time() - start_time) > 120:
                print("\nTimeout: No face detected for 120 seconds. Terminating.")
                break

            # Convert the image from BGR color to RGB color
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Find all the faces and face encodings in the current frame
            face_locations = face_recognition.face_locations(rgb_frame)
            
            if face_locations:
                face_detected_after_start = True
            
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                # See if the face is a match for the known face(s)
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.5)

                name = "Unknown"
                user_id = None

                # Find the best match
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                
                if matches[best_match_index] and face_distances[best_match_index] < 0.5:
                    user_id = known_face_user_ids[best_match_index]
                    name = known_face_names[best_match_index]
                    
                    current_time = datetime.now()
                    
                    # Check if enough time has passed since the last detection for this user
                    if (user_id not in last_detected_time or 
                        (current_time - last_detected_time[user_id]).total_seconds() > detection_threshold):
                        
                        if mark_attendance(user_id):
                            print("Attendance marked. Exiting application...")
                            video_capture.release()
                            cv2.destroyAllWindows()
                            return

                # Draw a box around the face
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

                # Draw a label with a name below the face
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

            # Display the resulting image
            cv2.imshow('Face Recognition', frame)

            # Check for key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('m'):
                print("\n--- Manual Attendance ---")
                user_id = input("Enter User ID for manual attendance: ")
                if user_id:
                    user = db_manager.get_user_by_id(user_id)
                    if user:
                        if mark_attendance(user_id):
                            print("Attendance marked. Exiting application...")
                            video_capture.release()
                            cv2.destroyAllWindows()
                            return
                    else:
                        print(f"Error: User with ID '{user_id}' not found.")
                else:
                    print("Invalid User ID.")
                print("\nReturning to face recognition system...")
    finally:
    # Release handle to the webcam and close all windows
        video_capture.release()
        cv2.destroyAllWindows()
        
if __name__ == "__main__":
    run_face_recognition()
