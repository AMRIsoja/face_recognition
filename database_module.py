import sqlite3
import numpy as np

class DatabaseManager:
    """
    Manages the SQLite database for user and attendance data.
    """
    def __init__(self, db_path="database.db"):
        self.db_path = db_path
        self._ensure_tables_exist()

    def _get_connection(self):
        """Returns a connection to the database."""
        return sqlite3.connect(self.db_path)

    def _ensure_tables_exist(self):
        """Creates the necessary tables if they don't exist."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Create the users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                encoding BLOB NOT NULL
            )
        """)
        
        # Create the attendance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY,
                user_id TEXT NOT NULL,
                date TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        conn.commit()
        conn.close()
        print("Database tables 'users' and 'attendance' ensured to exist.")

    def add_user(self, user_id, name, encoding):
        """Adds a new user to the database."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # Convert numpy array to a BLOB (binary format)
            encoding_blob = encoding.tobytes()
            cursor.execute("INSERT INTO users (id, name, encoding) VALUES (?, ?, ?)",
                           (user_id, name, encoding_blob))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
        finally:
            conn.close()

    def get_all_users(self):
        """Retrieves all users and their face encodings from the database."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, encoding FROM users")
        rows = cursor.fetchall()
        
        users = []
        for row in rows:
            user_id, name, encoding_blob = row
            # Convert BLOB back to a numpy array
            encoding = np.frombuffer(encoding_blob, dtype=np.float64)
            users.append({'id': user_id, 'name': name, 'encoding': encoding})
            
        conn.close()
        return users

    def get_user_by_id(self, user_id):
        """Retrieves a single user by their ID."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, encoding FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            user_id, name, encoding_blob = row
            encoding = np.frombuffer(encoding_blob, dtype=np.float64)
            return {'id': user_id, 'name': name, 'encoding': encoding}
        return None

    def get_attendance_record(self, user_id, date):
        """Checks for an existing attendance record for a user on a given date."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM attendance WHERE user_id = ? AND date = ?", 
                       (user_id, date))
        record = cursor.fetchone()
        conn.close()
        return record

    def add_attendance_record(self, user_id, date):
        """Adds a new attendance record for a user."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO attendance (user_id, date) VALUES (?, ?)", 
                           (user_id, date))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
        finally:
            conn.close()
