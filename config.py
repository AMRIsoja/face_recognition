import os

# Get the directory of the current script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define the path to the SQLite database
# The database file will be saved in the same directory as this script.
DATABASE_PATH = os.path.join(BASE_DIR, "smart_attendance.db")

# Path for the directory to store user images for face registration
# This directory will be created if it doesn't exist
IMAGES_PATH = os.path.join(BASE_DIR, "images")

# The minimum confidence level for a face match (e.g., 0.6 means 60% confidence)
# This can be adjusted based on your needs. A lower value is more permissive,
# a higher value is more strict.
FACE_MATCH_THRESHOLD = 0.6

# The time in seconds to wait before logging attendance for the same user again.
# This prevents logging a single person multiple times in a short window.
ATTENDANCE_LOGGING_INTERVAL = 300 # 5 minutes (5 * 60 seconds)

# Ensure the images directory exists
if not os.path.exists(IMAGES_PATH):
    os.makedirs(IMAGES_PATH)