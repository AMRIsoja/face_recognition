import cv2
import face_recognition
import numpy as np
import time
import os
from database_module import DatabaseManager
from config import DATABASE_PATH, FACE_MATCH_THRESHOLD, ATTENDANCE_LOGGING_INTERVAL

# Initialize the DatabaseManager with the path from the config file
db_manager = DatabaseManager(db_path=DATABASE_PATH)

# --- 1. Load Known Face Encodings from the Database ---
def load_known_faces():
    """
    Loads all user data (including names and face encodings) from the database.
    This function should be called once at the start of the program.
    """
    print("Loading known faces from the database...")
    users = db_manager.get_all_users()
    known_face_encodings = [user['face_encoding'] for user in users]
    known_face_names = [user['name'] for user in users]
    known_face_user_ids = [user['user_id'] for user in users]
    
    print(f"Loaded {len(known_face_encodings)} known faces.")
    return known_face_encodings, known_face_names, known_face_user_ids

# --- 2. Main Face Recognition Loop ---
def run_face_recognition():
    """
    Main function to run the video stream and perform face recognition.
    It captures video, finds faces, compares them to known faces, and logs attendance.
    """
    # Load known faces from the database
    known_face_encodings, known_face_names, known_face_user_ids = load_known_faces()
    
    # Initialize a dictionary to store the last time attendance was logged for each user
    last_attendance_log = {}

    # Open a connection to the webcam (0 is usually the default webcam)
    video_capture = cv2.VideoCapture(0)

    if not video_capture.isOpened():
        print("Error: Could not open video stream. Make sure a webcam is connected and not in use by another application.")
        return

    print("\nStarting video stream for face recognition. Press 'q' to quit.")

    while True:
        # Capture a single frame of video
        ret, frame = video_capture.read()
        if not ret:
            print("Error: Failed to read from video stream.")
            break

        # Convert the image from BGR color (OpenCV) to RGB color (face_recognition)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Find all the faces and face encodings in the current frame
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        # Loop through each face found in the frame
        for face_encoding, face_location in zip(face_encodings, face_locations):
            # Compare the found face with the known faces
            # The 'face_recognition.compare_faces' function returns a list of True/False values
            # indicating a match for each known face.
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=FACE_MATCH_THRESHOLD)
            name = "Unknown"
            user_id = "N/A"

            # Use the known face with the smallest distance to the new face
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            
            # Find the index of the best match
            best_match_index = np.argmin(face_distances)
            
            # If a match is found and the distance is within the tolerance
            if matches[best_match_index] and face_distances[best_match_index] <= FACE_MATCH_THRESHOLD:
                name = known_face_names[best_match_index]
                user_id = known_face_user_ids[best_match_index]
                
                # Check if enough time has passed since the last log for this user
                current_time = time.time()
                if (user_id not in last_attendance_log or 
                    (current_time - last_attendance_log[user_id]) > ATTENDANCE_LOGGING_INTERVAL):
                    
                    # Log attendance in the database
                    if db_manager.log_attendance(user_id):
                        last_attendance_log[user_id] = current_time # Update the last log time
                    
            # Draw a box around the face
            top, right, bottom, left = face_location
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

            # Draw a label with a name below the face
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (0, 0, 0), 1)

        # Display the resulting image
        cv2.imshow('Smart Attendance System', frame)

        # Break the loop on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the webcam and close all windows
    video_capture.release()
    cv2.destroyAllWindows()
    print("\nVideo stream stopped.")

# This block ensures the face recognition loop runs when the script is executed
if __name__ == "__main__":
    run_face_recognition()

