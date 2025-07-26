import os

# Define the base directory for the project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define the path for the SQLite database file
# It will be created in the same directory as this script
DATABASE_PATH = os.path.join(BASE_DIR, 'attendance_records.db')

# Define the directory to store captured images for known faces (optional, primarily for visual reference)
# Facial encodings are stored in the database
KNOWN_FACES_DIR = os.path.join(BASE_DIR, 'known_faces')

# Ensure the known_faces directory exists
os.makedirs(KNOWN_FACES_DIR, exist_ok=True)


