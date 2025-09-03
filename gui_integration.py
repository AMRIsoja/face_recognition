import tkinter as tk
from tkinter import messagebox, simpledialog, Toplevel, Label, CENTER
import threading
import cv2
from PIL import Image, ImageTk
from user_registration import register_new_user
from face_recognition_integration import run_face_recognition, load_known_faces

def show_status_popup(root, success, message, user_name=None, user_id=None):
    popup = Toplevel(root)
    popup.geometry("400x200")
    popup.resizable(False, False)
    popup.title("Status")
    popup.grab_set()
    popup.configure(bg="#e0e0e0")

    # Mark or Cancel symbol
    if success:
        symbol = "✔"
        color = "#2ecc40"  # Green
        msg = f"User: {user_name} with ID: {user_id}\nwas successfully marked."
    else:
        symbol = "✖"
        color = "#e74c3c"  # Red
        msg = message

    Label(popup, text=symbol, font=("Arial", 64), fg=color, bg="#e0e0e0").pack(pady=(20, 10))
    Label(popup, text=msg, font=("Arial", 14), bg="#e0e0e0", wraplength=350, justify=CENTER).pack(pady=(0, 20))

    tk.Button(popup, text="OK", font=("Arial", 12), width=10, command=popup.destroy).pack()

class FaceRecognitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Attendance System")
        self.root.geometry("400x300")
        self.root.resizable(False, False)

        # Title
        tk.Label(root, text="Smart Attendance System", font=("Arial", 16, "bold")).pack(pady=20)

        # Register Button
        tk.Button(root, text="Register New User", font=("Arial", 12), width=20, command=self.register_user).pack(pady=10)

        # Attendance Button
        tk.Button(root, text="Mark Attendance", font=("Arial", 12), width=20, command=self.mark_attendance).pack(pady=10)

        # Exit Button
        tk.Button(root, text="Exit", font=("Arial", 12), width=20, command=root.quit).pack(pady=10)

    def register_user(self):
        user_id = simpledialog.askstring("User Registration", "Enter a unique User ID (e.g., S001):", parent=self.root)
        if not user_id:
            return
        name = simpledialog.askstring("User Registration", "Enter the user's full name:", parent=self.root)
        if not name:
            return

        def run_registration():
            success = register_new_user(user_id.strip(), name.strip())
            if success:
                self.root.after(0, show_status_popup, self.root, True, "", name.strip(), user_id.strip())
            else:
                self.root.after(0, show_status_popup, self.root, False, "Registration failed or user already exists.")

        threading.Thread(target=run_registration, daemon=True).start()

    def mark_attendance(self):
        self.root.nametowidget(".!button2").config(state=tk.DISABLED)  # Disable button (adjust index if needed)
        def run_attendance():
            # Load known faces to get names and ids
            known_face_encodings, known_face_names, known_face_user_ids = load_known_faces()
            # Wrap run_face_recognition to get user info
            from face_recognition_integration import db_manager
            import face_recognition
            import numpy as np
            import time

            video_capture = cv2.VideoCapture(0)
            if not video_capture.isOpened():
                self.root.after(0, show_status_popup, self.root, False, "Error: Could not open video stream.")
                return

            last_detected_time = {}
            detection_threshold = 5
            start_time = time.time()
            face_detected_after_start = False
            marked = False

            try:
                while True:
                    ret, frame = video_capture.read()
                    if not ret or frame is None:
                        self.root.after(0, show_status_popup, self.root, False, "Error: Failed to read from video stream.")
                        break

                    if frame.dtype != np.uint8:
                        frame = frame.astype(np.uint8)
                    if len(frame.shape) == 2:
                        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

                    if not face_detected_after_start and (time.time() - start_time) > 120:
                        self.root.after(0, show_status_popup, self.root, False, "Timeout: No face detected for 120 seconds.")
                        break

                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    face_locations = face_recognition.face_locations(rgb_frame)

                    if face_locations:
                        face_detected_after_start = True

                    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

                    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                        matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.5)
                        name = "Unknown"
                        user_id = None
                        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                        best_match_index = np.argmin(face_distances)
                        if matches and matches[best_match_index] and face_distances[best_match_index] < 0.5:
                            user_id = known_face_user_ids[best_match_index]
                            name = known_face_names[best_match_index]
                            current_time = time.time()
                            if (user_id not in last_detected_time or 
                                (current_time - last_detected_time[user_id]) > detection_threshold):
                                from face_recognition_integration import mark_attendance
                                mark_attendance(user_id)
                                marked = True
                                self.root.after(0, show_status_popup, self.root, True, "", name, user_id)
                                video_capture.release()
                                cv2.destroyAllWindows()
                                return
                    cv2.imshow('Face Recognition', frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        break
            finally:
                video_capture.release()
                cv2.destroyAllWindows()
                self.root.after(0, lambda: self.root.nametowidget(".!button2").config(state=tk.NORMAL))  # Re-enable button
                if not marked:
                    self.root.after(0, show_status_popup, self.root, False, "Attendance not marked.")

        threading.Thread(target=run_attendance, daemon=True).start()

def main():
    root = tk.Tk()
    app = FaceRecognitionApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()